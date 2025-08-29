import os
from typing import List, Set
import requests
import dotenv


def load_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def build_set(path: str) -> Set[str]:
    return set(load_lines(path))


def compute_correct_ids() -> List[str]:
    correct = build_set("lab_data/correct.txt")
    incorrect = build_set("lab_data/incorect.txt")
    result: List[str] = []
    for row in load_lines("lab_data/verify.txt"):
        if "=" not in row:
            continue
        idx, data = row.split("=", 1)
        if data in correct and data not in incorrect:
            result.append(idx)
    return result


def submit(ids: List[str]) -> dict:
    dotenv.load_dotenv(dotenv_path="../../.env")
    api_key = os.getenv("DV_API_KEY")
    payload = {
        "task": "research",
        "apikey": api_key,
        "answer": ids,
    }
    r = requests.post("https://c3ntrala.ag3nts.org/report", json=payload)
    return r.json()


def main() -> None:
    ids = compute_correct_ids()
    resp = submit(ids)
    print(resp)


if __name__ == "__main__":
    main()
