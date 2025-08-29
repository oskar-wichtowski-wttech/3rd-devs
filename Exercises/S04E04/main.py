from __future__ import annotations

import re
from typing import Dict, List, Tuple

import logging
from flask import Flask, jsonify, request


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# 4x4 siatka: współrzędne (wiersz, kolumna), 0-index, (0,0) lewy górny róg
# UZUPEŁNIJ OPISY NA PODSTAWIE pliku `mapa_s04e04.png`.
# Maksymalnie dwa słowa na opis pola – to wartości zwracane w `description`.
GRID_CONTENT: List[List[str]] = [
    [
        "start",  # (0,0)
        "trawa",  # (0,1)
        "pojedyncze drzewo",  # (0,2)
        "dom",  # (0,3)
    ],
    [
        "trawa",  # (1,0)
        "wiatrak",  # (1,1)
        "trawa",  # (1,2)
        "trawa",  # (1,3)
    ],
    [
        "trawa",  # (2,0)
        "trawa",  # (2,1)
        "skały",  # (2,2)
        "dwa drzewa",  # (2,3)
    ],
    [
        "góry",  # (3,0)
        "góry",  # (3,1)
        "samochód",  # (3,2)
        "jaskinia",  # (3,3)
    ],
]


def grid_size() -> Tuple[int, int]:
    return len(GRID_CONTENT), len(GRID_CONTENT[0]) if GRID_CONTENT else 0


NUMBER_WORDS: Dict[str, int] = {
    # podstawowe liczebniki PL
    "zero": 0,
    "jeden": 1,
    "jedno": 1,
    "pierwszy": 1,
    "dwa": 2,
    "drugi": 2,
    "trzy": 3,
    "cztery": 4,
    "pięć": 5,
    # cyfry arabskie w tekście
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def parse_instruction_to_delta_sequence(instruction: str) -> List[Tuple[int, int]]:
    instruction_norm = normalize(instruction)

    # Rozbijanie na frazy po łącznikach czasowych
    parts = re.split(r"\b(potem|później|następnie|a potem|a później|,|\.|i|oraz|ale|lecz)\b", instruction_norm)
    # Zachowaj tylko segmenty nie-będące spójnikami
    phrases = [p.strip() for p in parts if p and not re.fullmatch(r"(potem|później|następnie|a potem|a później|,|\.|i|oraz|ale|lecz)", p)]

    deltas: List[Tuple[int, int]] = []

    # Kierunki i ich wektory (wiersz, kolumna)
    direction_vectors: Dict[str, Tuple[int, int]] = {
        # prawo/lewo
        "prawo": (0, 1),
        "w prawo": (0, 1),
        "na prawo": (0, 1),
        "prawa": (0, 1),
        # zachód
        "zachód": (0, -1),
        "lewo": (0, -1),
        "w lewo": (0, -1),
        "na lewo": (0, -1),
        "lewa": (0, -1),
        # góra/dół
        "góra": (-1, 0),
        "w górę": (-1, 0),
        "do góry": (-1, 0),
        "na górę": (-1, 0),
        "północ": (-1, 0),
        "dół": (1, 0),
        "w dół": (1, 0),
        "na dół": (1, 0),
        "południe": (1, 0),
        # alternatywne nazwy kierunków geograficznych
        "wschód": (0, 1),
    }

    # Wyrażenia typu "na sam dół", "na maksa w prawo" → do granicy
    edge_patterns: List[Tuple[re.Pattern, Tuple[int, int]]] = [
        (re.compile(r"na sama? dół|na sam dół"), (1, 0)),
        (re.compile(r"na sama? górę|na samą górę|na samą góre|na samą gore|na samą góre"), (-1, 0)),
        (re.compile(r"na samo? prawo|na samą? prawo"), (0, 1)),
        (re.compile(r"na samo? lewo|na samą? lewo"), (0, -1)),
    ]

    edge_intent_pattern = re.compile(
        r"(na maksa|maxymalnie|do oporu|do końca|jak najdalej|ile wlezie|ile sie da|ile się da)"
    )

    # Frazy ilościowe: "o X pól", "X krok(i)/pole/pola/pól"
    qty_pattern = re.compile(
        r"(?:(?:o|na|jeszcze)\s+)?((?:\d+|zero|jeden|jedno|pierwszy|dwa|drugi|trzy|cztery|pięć))\s+(?:krok|kroki|kroków|pole|pola|pól)?"
    )

    for phrase in phrases:
        logging.info("processing phrase: '%s'", phrase)
        # krawędzie do końca planszy
        matched_edge = False
        for patt, vec in edge_patterns:
            if patt.search(phrase):
                deltas.append((9999 * vec[0], 9999 * vec[1]))
                matched_edge = True
                break
        if matched_edge:
            continue

        # określ kierunek w frazie
        dir_vec: Tuple[int, int] | None = None
        for key, vec in direction_vectors.items():
            if re.search(rf"\b{re.escape(key)}\b", phrase):
                dir_vec = vec
                break
        if dir_vec is None:
            # Sprobuj z konstrukcjami typu "w prawo", "w lewo", "w dół", "w górę"
            if "prawo" in phrase:
                dir_vec = (0, 1)
            elif "lewo" in phrase:
                dir_vec = (0, -1)
            elif "gór" in phrase:
                dir_vec = (-1, 0)
            elif "dół" in phrase or "dol" in phrase:
                dir_vec = (1, 0)

        if dir_vec is None:
            # brak rozpoznanego kierunku – pomiń frazę
            continue

        # jeśli jest intencja krawędzi + wykryty kierunek → ruch do krawędzi
        if edge_intent_pattern.search(phrase):
            deltas.append((9999 * dir_vec[0], 9999 * dir_vec[1]))
            continue

        qty = 1
        qty_match = qty_pattern.search(phrase)
        if qty_match:
            raw = qty_match.group(1)
            qty = NUMBER_WORDS.get(raw, None) or (int(raw) if raw.isdigit() else 1)
        deltas.append((dir_vec[0] * qty, dir_vec[1] * qty))
        logging.info("added delta: (%d, %d) for phrase '%s'", dir_vec[0] * qty, dir_vec[1] * qty, phrase)

    logging.info("final deltas: %s", deltas)
    return deltas


def apply_deltas_from_start(deltas: List[Tuple[int, int]]) -> Tuple[int, int]:
    rows, cols = grid_size()
    r, c = 0, 0
    for dr, dc in deltas:
        # ruchy do krawędzi
        if abs(dr) > rows or abs(dc) > cols:
            if dr > 0:
                r = rows - 1
            elif dr < 0:
                r = 0
            if dc > 0:
                c = cols - 1
            elif dc < 0:
                c = 0
            continue

        # ruch krokowy z ograniczeniem do granic
        r = max(0, min(rows - 1, r + dr))
        c = max(0, min(cols - 1, c + dc))
    return r, c


def describe_cell(position: Tuple[int, int]) -> str:
    r, c = position
    try:
        value = GRID_CONTENT[r][c]
    except Exception:
        value = ""
    return value or "nieznane"


@app.post("/webhook")
def webhook() -> tuple:
    try:
        payload = request.get_json(silent=True) or {}
        logging.info("headers=%s", dict(request.headers))
        logging.info("payload=%s", payload)
        instruction = str(payload.get("instruction", ""))
        deltas = parse_instruction_to_delta_sequence(instruction)
        final_pos = apply_deltas_from_start(deltas)
        description = describe_cell(final_pos)
        logging.info("response={description='%s', row=%d, col=%d}", description, final_pos[0], final_pos[1])
        return (jsonify({"description": description}), 200)
    except Exception:  # noqa: BLE001
        logging.exception("error")
        return (jsonify({"description": "nieznane"}), 200)


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    # Uruchom lokalnie (HTTP). Wystaw HTTPS przez ngrok lub reverse proxy.
    app.run(host="0.0.0.0", port=5000)


