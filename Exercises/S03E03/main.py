import os
import requests
from typing import List, Dict, Any
from openai import OpenAI
import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
API_KEY = os.getenv("DV_API_KEY")
DATABASE_API_URL = "https://c3ntrala.ag3nts.org/apidb"
CENTRAL_API_URL = "https://c3ntrala.ag3nts.org/report"

def query_database(sql_query: str) -> Dict[str, Any]:
    """Wykonuje zapytanie SQL do bazy danych przez API"""
    payload = {
        "task": "database",
        "apikey": API_KEY,
        "query": sql_query
    }
    
    response = requests.post(DATABASE_API_URL, json=payload)
    print(f"Database API Response: {response.status_code}")
    print(f"Response content: {response.text}")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Database API error: {response.status_code} - {response.text}")

def discover_database_structure() -> Dict[str, Any]:
    """Odkrywa strukturę bazy danych"""
    print("Odkrywanie struktury bazy danych...")
    
    # Pobierz listę tabel
    tables_result = query_database("SHOW TABLES;")
    print(f"Tablice: {tables_result}")
    
    # Pobierz strukturę tabel users i datacenters
    users_structure = query_database("SHOW CREATE TABLE users;")
    print(f"Struktura tabeli users: {users_structure}")
    
    datacenters_structure = query_database("SHOW CREATE TABLE datacenters;")
    print(f"Struktura tabeli datacenters: {datacenters_structure}")
    
    return {
        "tables": tables_result,
        "users_structure": users_structure,
        "datacenters_structure": datacenters_structure
    }

def generate_sql_query(database_structure: Dict[str, Any]) -> str:
    """Generuje zapytanie SQL za pomocą LLM"""
    prompt = f"""
Na podstawie poniższych schematów tabel, napisz zapytanie SQL, które zwróci DC_ID aktywnych datacenter, których menadżerowie (z tabeli users) są nieaktywni.

Schemat tabeli users:
{database_structure['users_structure']}

Schemat tabeli datacenters:
{database_structure['datacenters_structure']}

Ważne: Zwróć tylko i wyłącznie surowy tekst zapytania SQL, bez żadnych dodatkowych opisów, wyjaśnień czy formatowania typu Markdown.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jesteś ekspertem SQL. Odpowiadaj tylko surowym kodem SQL bez żadnych dodatkowych komentarzy."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    sql_query = response.choices[0].message.content.strip()
    print(f"Wygenerowane zapytanie SQL: {sql_query}")
    
    return sql_query

def process_results(query_result: Dict[str, Any]) -> List[int]:
    """Przetwarza wyniki zapytania i wyodrębnia listę ID"""
    print(f"Wyniki zapytania: {query_result}")
    
    # Wyodrębnij dane z odpowiedzi API - sprawdź różne możliwe formaty
    if 'reply' in query_result:
        data = query_result['reply']
    elif 'data' in query_result:
        data = query_result['data']
    elif 'result' in query_result:
        data = query_result['result']
    else:
        data = query_result
    
    # Jeśli dane są w formacie listy obiektów, wyodrębnij DC_ID
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict):
            # Zakładamy, że kolumna nazywa się DC_ID lub dc_id
            dc_ids = []
            for row in data:
                if 'dc_id' in row:
                    dc_ids.append(int(row['dc_id']))
                elif 'DC_ID' in row:
                    dc_ids.append(int(row['DC_ID']))
                elif 'id' in row:
                    dc_ids.append(int(row['id']))
            return dc_ids
        else:
            # Jeśli dane są już listą liczb
            return [int(x) for x in data if str(x).isdigit()]
    
    return []

def submit_answer(dc_ids: List[int]) -> None:
    """Przesyła ostateczną odpowiedź do centrali"""
    payload = {
        "task": "database",
        "apikey": API_KEY,
        "answer": dc_ids
    }
    
    print(f"dc_ids: {dc_ids}")
    response = requests.post(CENTRAL_API_URL, json=payload)
    print(f"Central API Response: {response.status_code}")
    print(f"Response content: {response.text}")
    
    if response.status_code == 200:
        print("Odpowiedź została pomyślnie przesłana!")
    else:
        print(f"Błąd podczas przesyłania odpowiedzi: {response.status_code}")

def main() -> None:
    """Główna funkcja wykonująca zadanie"""
    try:
        # Krok 1: Odkryj strukturę bazy danych
        database_structure = discover_database_structure()
        
        # Krok 2: Wygeneruj zapytanie SQL za pomocą LLM
        sql_query = generate_sql_query(database_structure)
        
        # Krok 3: Wykonaj wygenerowane zapytanie SQL
        query_result = query_database(sql_query)
        
        # Krok 4: Przetwórz wynik
        dc_ids = process_results(query_result)
        print(f"Znalezione DC_ID: {dc_ids}")
        
        # Krok 5: Prześlij ostateczną odpowiedź do centrali
        submit_answer(dc_ids)
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    main() 