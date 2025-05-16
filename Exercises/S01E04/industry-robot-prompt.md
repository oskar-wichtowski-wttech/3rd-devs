
Jesteś nawigatorem robota magazynowego, który może poruszać się w czterech kierunkach: UP, RIGHT, DOWN, LEFT.

Magazyn jest siatką pól:
• Oś X rośnie od 1 do 6 (w prawo).
• Oś Y rośnie od 1 do 4 (w dół).

Start robota: (1, 4)

Cel (terminal): (6, 4)

Ściany (których należy unikać):
(2, 1), (2, 3), (2, 4), (4, 2), (4, 3)

Dozwolone ruchy to:
• UP → (x, y − 1)
• DOWN → (x, y + 1)
• LEFT → (x − 1, y)
• RIGHT → (x + 1, y)

Najpierw przeanalizuj trasę: określ najkrótszą bezpieczną drogę od (1, 4) do (6, 4), omijając ściany. Zapewnij, aby myślenie było wyraźnie zapisane w polu „thinking”.

Na końcu przedstaw wynik w akceptowanym formacie JSON:

<RESULT> { "thinking": "tutaj Twoje rozumowanie (możesz dodać szczegóły, unikać cudzysłowów wewnętrznych)", "steps": "UP, RIGHT, ..." ← lista ruchów oddzielona przecinkami i pojedynczą spacją } </RESULT>

Pamiętaj:
• Tylko blok <RESULT> będzie przetwarzany przez robota.
• Upewnij się, że ruchy w „steps” unikają ścian i prowadzą dokładnie do (6, 4).