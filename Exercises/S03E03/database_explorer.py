import os
import requests
from typing import List, Dict, Any
import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")

API_KEY = os.getenv("DV_API_KEY")
DATABASE_API_URL = "https://c3ntrala.ag3nts.org/apidb"

def query_database(sql_query: str) -> Dict[str, Any]:
    """Wykonuje zapytanie SQL do bazy danych przez API"""
    payload = {
        "task": "database",
        "apikey": API_KEY,
        "query": sql_query
    }
    
    response = requests.post(DATABASE_API_URL, json=payload)
    print(f"Query: {sql_query}")
    print(f"Response: {response.status_code}")
    print(f"Content: {response.text}")
    print("-" * 50)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Database API error: {response.status_code} - {response.text}")

def explore_all_tables() -> None:
    """Eksploruje wszystkie tabele w bazie danych"""
    print("🔍 EKSPLORACJA WSZYSTKICH TABEL")
    print("=" * 60)
    
    # Pobierz listę wszystkich tabel
    tables_result = query_database("SHOW TABLES;")
    
    if 'reply' in tables_result:
        tables = [table['Tables_in_banan'] for table in tables_result['reply']]
        print(f"Znalezione tabele: {tables}")
        
        for table in tables:
            print(f"\n📋 TABELA: {table}")
            print("-" * 30)
            
            # Pobierz strukturę tabeli
            structure = query_database(f"SHOW CREATE TABLE {table};")
            
            # Pobierz wszystkie dane z tabeli
            try:
                all_data = query_database(f"SELECT * FROM {table};")
                if 'reply' in all_data:
                    print(f"Liczba rekordów: {len(all_data['reply'])}")
                    if all_data['reply']:
                        print("Przykładowe dane:")
                        for i, row in enumerate(all_data['reply'][:5]):  # Pokaż pierwsze 5 rekordów
                            print(f"  {i+1}: {row}")
                        if len(all_data['reply']) > 5:
                            print(f"  ... i {len(all_data['reply']) - 5} więcej")
            except Exception as e:
                print(f"Błąd podczas pobierania danych: {e}")

def explore_table_details() -> None:
    """Szczegółowa eksploracja każdej tabeli"""
    print("\n🔬 SZCZEGÓŁOWA EKSPLORACJA TABEL")
    print("=" * 60)
    
    tables = ['users', 'datacenters', 'connections', 'correct_order']
    
    for table in tables:
        print(f"\n📊 TABELA: {table}")
        print("-" * 40)
        
        # Struktura tabeli
        structure = query_database(f"DESCRIBE {table};")
        
        # Liczba rekordów
        count = query_database(f"SELECT COUNT(*) as count FROM {table};")
        
        # Unikalne wartości w każdej kolumnie
        if 'reply' in structure:
            columns = [col['Field'] for col in structure['reply']]
            print(f"Kolumny: {columns}")
            
            for column in columns:
                try:
                    unique_values = query_database(f"SELECT DISTINCT {column} FROM {table} LIMIT 10;")
                    if 'reply' in unique_values and unique_values['reply']:
                        values = [str(row[column]) for row in unique_values['reply']]
                        print(f"  {column}: {values}")
                except Exception as e:
                    print(f"  {column}: błąd - {e}")

def search_for_flags() -> None:
    """Szuka flag w danych"""
    print("\n🚩 SZUKANIE FLAG")
    print("=" * 60)
    
    # Szukaj w różnych tabelach
    tables = ['users', 'datacenters', 'connections', 'correct_order']
    
    for table in tables:
        print(f"\n🔍 Szukanie w tabeli: {table}")
        
        # Pobierz wszystkie dane
        try:
            all_data = query_database(f"SELECT * FROM {table};")
            if 'reply' in all_data:
                for row in all_data['reply']:
                    for key, value in row.items():
                        if isinstance(value, str):
                            # Szukaj wzorców flag
                            if 'flag' in value.lower() or 'ctf' in value.lower():
                                print(f"  FLAG PATTERN: {key} = {value}")
                            # Szukaj base64
                            if len(value) > 10 and value.isalnum():
                                print(f"  POTENTIAL BASE64: {key} = {value}")
                            # Szukaj hex
                            if value.startswith('0x') or (len(value) % 2 == 0 and all(c in '0123456789abcdefABCDEF' for c in value)):
                                print(f"  POTENTIAL HEX: {key} = {value}")
        except Exception as e:
            print(f"  Błąd: {e}")

def explore_connections_table() -> None:
    """Szczegółowa eksploracja tabeli connections"""
    print("\n🔗 EKSPLORACJA TABELI CONNECTIONS")
    print("=" * 60)
    
    try:
        # Pobierz strukturę
        structure = query_database("DESCRIBE connections;")
        
        # Pobierz wszystkie dane
        all_data = query_database("SELECT * FROM connections;")
        
        if 'reply' in all_data:
            print(f"Liczba połączeń: {len(all_data['reply'])}")
            
            # Analizuj każde połączenie
            for i, connection in enumerate(all_data['reply']):
                print(f"\nPołączenie {i+1}:")
                for key, value in connection.items():
                    print(f"  {key}: {value}")
                    
                    # Sprawdź czy wartość może być flagą
                    if isinstance(value, str):
                        if len(value) > 20 and value.isalnum():
                            print(f"    ⚠️  POTENTIAL FLAG: {value}")
                        if 'flag' in value.lower():
                            print(f"    🚩 FLAG FOUND: {value}")
                            
    except Exception as e:
        print(f"Błąd: {e}")

def explore_correct_order_table() -> None:
    """Szczegółowa eksploracja tabeli correct_order"""
    print("\n📋 EKSPLORACJA TABELI CORRECT_ORDER")
    print("=" * 60)
    
    try:
        # Pobierz strukturę
        structure = query_database("DESCRIBE correct_order;")
        
        # Pobierz wszystkie dane
        all_data = query_database("SELECT * FROM correct_order;")
        
        if 'reply' in all_data:
            print(f"Liczba rekordów: {len(all_data['reply'])}")
            
            # Analizuj każdy rekord
            for i, record in enumerate(all_data['reply']):
                print(f"\nRekord {i+1}:")
                for key, value in record.items():
                    print(f"  {key}: {value}")
                    
                    # Sprawdź czy wartość może być flagą
                    if isinstance(value, str):
                        if len(value) > 20 and value.isalnum():
                            print(f"    ⚠️  POTENTIAL FLAG: {value}")
                        if 'flag' in value.lower():
                            print(f"    🚩 FLAG FOUND: {value}")
                            
    except Exception as e:
        print(f"Błąd: {e}")

def try_special_queries() -> None:
    """Próbuje specjalne zapytania"""
    print("\n🎯 SPECJALNE ZAPYTANIA")
    print("=" * 60)
    
    special_queries = [
        "SELECT * FROM connections WHERE 1=1;",
        "SELECT * FROM correct_order WHERE 1=1;",
        "SELECT * FROM users WHERE username LIKE '%flag%';",
        "SELECT * FROM datacenters WHERE location LIKE '%flag%';",
        "SELECT * FROM connections WHERE id LIKE '%flag%';",
        "SELECT * FROM correct_order WHERE id LIKE '%flag%';",
        "SELECT * FROM users WHERE access_level = 'admin';",
        "SELECT * FROM users WHERE is_active = 0;",
        "SELECT * FROM datacenters WHERE is_active = 1;",
        "SELECT * FROM connections ORDER BY id;",
        "SELECT * FROM correct_order ORDER BY id;"
    ]
    
    for query in special_queries:
        try:
            result = query_database(query)
            if 'reply' in result and result['reply']:
                print(f"✅ {query}")
                for row in result['reply']:
                    print(f"  {row}")
            else:
                print(f"❌ {query} - brak wyników")
        except Exception as e:
            print(f"❌ {query} - błąd: {e}")

def main() -> None:
    """Główna funkcja eksplorująca bazę danych"""
    print("🔍 EKSPLORACJA BAZY DANYCH - SZUKANIE FLAG")
    print("=" * 60)
    
    try:
        # Eksploruj wszystkie tabele
        explore_all_tables()
        
        # Szczegółowa eksploracja
        explore_table_details()
        
        # Szukaj flag
        search_for_flags()
        
        # Szczegółowa eksploracja tabeli connections
        explore_connections_table()
        
        # Szczegółowa eksploracja tabeli correct_order
        explore_correct_order_table()
        
        # Specjalne zapytania
        try_special_queries()
        
        print("\n" + "=" * 60)
        print("✨ Eksploracja zakończona! Sprawdź powyższe wyniki pod kątem ukrytych flag.")
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    main() 