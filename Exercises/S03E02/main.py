import os
import glob
from datetime import datetime
from typing import List, Dict, Any
import openai
from openai import OpenAI
import chromadb
import dotenv
import requests

dotenv.load_dotenv(dotenv_path="../../.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Nowa konfiguracja ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")

def get_embedding(text: str) -> List[float]:
    """Generuje embedding dla podanego tekstu"""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

def parse_date_from_filename(filename: str) -> str:
    """Wyciąga datę z nazwy pliku w formacie YYYY-MM-DD"""
    basename = os.path.basename(filename)
    date_str = basename.replace('.txt', '')
    date_obj = datetime.strptime(date_str, '%Y_%m_%d')
    return date_obj.strftime('%Y-%m-%d')

def load_reports() -> List[Dict[str, Any]]:
    """Ładuje wszystkie raporty z plików"""
    reports = []
    pattern = "weapons_tests/do-not-share/*.txt"
    
    for filepath in glob.glob(pattern):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        date = parse_date_from_filename(filepath)
        
        reports.append({
            'content': content,
            'date': date,
            'filename': os.path.basename(filepath)
        })
    
    return reports

def create_vector_database(reports: List[Dict[str, Any]]) -> None:
    """Tworzy bazę wektorową z raportami"""
    try:
        chroma_client.delete_collection("weapons_reports")
        print("Usunięto istniejącą kolekcję...")
    except:
        pass

    collection = chroma_client.create_collection(
        name="weapons_reports",
        embedding_function=None,
        metadata={"dim": 1536}
    )

    documents = []
    metadatas = []
    ids = []
    embeddings = []

    for i, report in enumerate(reports):
        documents.append(report['content'])
        metadatas.append({
            'date': report['date'],
            'filename': report['filename']
        })
        ids.append(f"report_{i}")
        embeddings.append(get_embedding(report['content']))

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    print(f"Zaindeksowano {len(reports)} raportów w bazie wektorowej")

def search_kradziez() -> str:
    """Wyszukuje datę kradzieży prototypu broni"""
    collection = chroma_client.get_collection("weapons_reports")
    
    query = "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
    query_embedding = get_embedding(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=1
    )
    
    if results['metadatas'] and results['metadatas'][0]:
        return results['metadatas'][0][0]['date']
    
    return "Nie znaleziono odpowiedzi"

def main() -> None:
    """Główna funkcja aplikacji"""
    print("Ładowanie raportów...")
    reports = load_reports()
    
    print("Tworzenie bazy wektorowej...")
    create_vector_database(reports)
    
    print("Wyszukiwanie daty kradzieży...")
    kradziez_date = search_kradziez()
    
    print(f"Data kradzieży prototypu broni: {kradziez_date}")
    
    # Prepare payload for central API
    dv_key = os.getenv("DV_API_KEY")
    payload = {
        "task": "wektory",
        "apikey": dv_key,
        "answer": kradziez_date
    }
    
    # Send to central API
    response = requests.post(
        'https://c3ntrala.ag3nts.org/report',
        json=payload
    )
    
    if response.status_code == 200:
        print("Successfully sent results to central API")
        print(response.text)
    else:
        print(f"Error sending results: {response.status_code}")

if __name__ == "__main__":
    main()
