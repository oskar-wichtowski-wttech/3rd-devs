import os
import json
from pathlib import Path
import requests
from openai import OpenAI
import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def get_all_facts(facts_dir):
    facts = {}
    print(f"Looking for facts in: {facts_dir}")
    if not os.path.exists(facts_dir):
        print(f"Facts directory does not exist: {facts_dir}")
        return facts
        
    for fact_file in Path(facts_dir).glob('*.txt'):
        print(f"Found fact file: {fact_file}")
        content = read_file_content(fact_file)
        if content:
            facts[fact_file.name] = content
    return facts

def prepare_llm_prompt(report_content, report_filename, facts):
    prompt = f"""Przeanalizuj poniższy raport i wygeneruj precyzyjną listę słów kluczowych w języku polskim.

WAŻNE WSKAZÓWKI:
1. Słowa kluczowe muszą być:
   - W języku polskim
   - W mianowniku
   - Oddzielone przecinkami
   - Jak najbardziej konkretne i specyficzne dla tego raportu

2. Analiza faktów:
   - Jeśli w raporcie pojawia się osoba, a w faktach są o niej informacje, MUSZĄ one trafić do słów kluczowych
   - Zwróć uwagę na możliwe literówki w nazwiskach (np. "Kowaski" i "Kowalki" mogą być tą samą osobą)
   - Wykorzystaj WSZYSTKIE istotne informacje z faktów powiązanych z raportem

3. Nazwa pliku:
   - Wykorzystaj informacje zawarte w nazwie pliku (np. sektor, data, numer)
   - Informacje z nazwy pliku są tak samo ważne jak treść raportu

4. Specyficzne wskazówki:
   - Jeśli raport wspomina o "dzikiej faunie", "zwierzynie leśnej" lub "wildlife", użyj ogólniejszego słowa "zwierzęta"
   - Uwzględnij nazwiska i imiona, jeśli są istotne dla raportu
   - Bądź precyzyjny - każde słowo kluczowe powinno mieć konkretne uzasadnienie w raporcie lub faktach

Nazwa pliku raportu: {report_filename}
Treść raportu:
{report_content}

Dodatkowe fakty do analizy:
{json.dumps(facts, indent=2, ensure_ascii=False)}

Format odpowiedzi: lista,słów,kluczowych,oddzielonych,przecinkami"""
    return prompt

def process_reports(reports_dir, facts_dir, openai_api_key):
    client = OpenAI(api_key=openai_api_key)
    facts = get_all_facts(facts_dir)
    results = {}
    
    print(f"Looking for reports in: {reports_dir}")
    if not os.path.exists(reports_dir):
        print(f"Reports directory does not exist: {reports_dir}")
        return results
    
    report_files = list(Path(reports_dir).glob('*sektor_*.txt'))
    print(f"Found {len(report_files)} report files")
    
    for report_file in report_files:
        print(f"Processing report: {report_file}")
        report_content = read_file_content(report_file)
        if not report_content:
            print(f"Skipping {report_file} due to read error")
            continue
            
        prompt = prepare_llm_prompt(report_content, report_file.name, facts)
        
        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Jesteś precyzyjnym asystentem analizującym raporty i generującym słowa kluczowe w języku polskim. Twoje słowa kluczowe muszą być dokładne, konkretne i uwzględniać wszystkie istotne informacje z raportu, faktów oraz nazwy pliku."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            keywords = response.choices[0].message.content.strip()
            results[report_file.name] = keywords
            print(f"Successfully processed {report_file.name}")
            print(f"Generated keywords: {keywords}")
            
        except Exception as e:
            print(f"Error processing {report_file.name}: {str(e)}")
    
    return results

def main():
    # Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    DV_API_KEY = os.getenv('DV_API_KEY')
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    if not DV_API_KEY:
        raise ValueError("DV_API_KEY environment variable is required")
    
    # Get the absolute path to the reports directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    REPORTS_DIR = os.path.join(current_dir, "..", "S01E04", "pliki_z_fabryki")
    FACTS_DIR = os.path.join(REPORTS_DIR, "facts")
    
    print(f"Current directory: {current_dir}")
    print(f"Reports directory: {REPORTS_DIR}")
    print(f"Facts directory: {FACTS_DIR}")
    
    # Process reports
    results = process_reports(REPORTS_DIR, FACTS_DIR, OPENAI_API_KEY)
    
    print("\nFinal results:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # Save results
    with open('keywords.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Prepare payload for central API
    
    # Send to central API
    response = requests.post(
        'https://c3ntrala.ag3nts.org/report',
        json={
            "task": "dokumenty",
            "apikey": DV_API_KEY,
            "answer": results
        }
    )
    
    if response.status_code == 200:
        print("Successfully sent results to central API")
        print(response.text)
    else:
        print(f"Error sending results: {response.status_code}")

if __name__ == "__main__":
    main()
