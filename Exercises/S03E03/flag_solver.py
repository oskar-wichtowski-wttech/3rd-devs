import json
from typing import List, Dict, Any

def solve_flag_from_data() -> None:
    """Rozwiązuje flagę z danych correct_order"""
    
    # Dane z correct_order table
    data = [
        {"base_id": "7742", "letter": "D", "weight": "16"},
        {"base_id": "8823", "letter": "N", "weight": "6"},
        {"base_id": "1892", "letter": "E", "weight": "17"},
        {"base_id": "8993", "letter": "{", "weight": "1"},
        {"base_id": "2288", "letter": "}", "weight": "20"},
        {"base_id": "1463", "letter": ":", "weight": "5"},
        {"base_id": "8449", "letter": "W", "weight": "8"},
        {"base_id": "9858", "letter": "R", "weight": "18"},
        {"base_id": "4942", "letter": "F", "weight": "2"},
        {"base_id": "3137", "letter": "D", "weight": "13"},
        {"base_id": "8859", "letter": "{", "weight": "0"},
        {"base_id": "6885", "letter": "G", "weight": "4"},
        {"base_id": "6847", "letter": "}", "weight": "19"},
        {"base_id": "3581", "letter": "R", "weight": "15"},
        {"base_id": "5366", "letter": "O", "weight": "10"},
        {"base_id": "6087", "letter": "R", "weight": "11"},
        {"base_id": "4338", "letter": "W", "weight": "9"},
        {"base_id": "2428", "letter": "L", "weight": "3"},
        {"base_id": "7129", "letter": "O", "weight": "14"},
        {"base_id": "9359", "letter": "L", "weight": "12"},
        {"base_id": "6409", "letter": "E", "weight": "7"}
    ]
    
    print("🔍 ROZWIĄZYWANIE FLAGI Z DANYCH CORRECT_ORDER")
    print("=" * 60)
    
    # Sortuj według weight (od najmniejszego do największego)
    sorted_data = sorted(data, key=lambda x: int(x['weight']))
    
    print("📋 DANE POSORTOWANE WG WEIGHT:")
    print("-" * 40)
    for record in sorted_data:
        print(f"Weight {record['weight']:2s}: '{record['letter']}' (base_id: {record['base_id']})")
    
    # Zbuduj flagę z liter posortowanych według weight
    flag_chars = [record['letter'] for record in sorted_data]
    flag = ''.join(flag_chars)
    
    print(f"\n🚩 POTENCJALNA FLAGA: {flag}")
    
    # Sprawdź czy to wygląda na flagę
    if flag.startswith('FLAG{') and flag.endswith('}'):
        print("🎉 TO WYGLĄDA NA PRAWDZIWĄ FLAGĘ!")
        print(f"🎯 FLAGA: {flag}")
    else:
        print("❓ To nie wygląda na standardową flagę, ale może być ukryta wiadomość")
    
    # Zapisz wyniki do pliku
    result = {
        'original_data': data,
        'sorted_by_weight': sorted_data,
        'flag': flag,
        'characters': flag_chars,
        'weight_order': [int(record['weight']) for record in sorted_data]
    }
    
    with open('flag_solution.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Zapisano rozwiązanie do: flag_solution.json")
    
    # Dodatkowa analiza
    print(f"\n📊 ANALIZA:")
    print(f"  - Liczba znaków: {len(flag_chars)}")
    print(f"  - Zakres weight: {min(int(r['weight']) for r in data)} - {max(int(r['weight']) for r in data)}")
    print(f"  - Unikalne litery: {len(set(flag_chars))}")
    print(f"  - Litery: {sorted(set(flag_chars))}")

def analyze_alternative_sortings() -> None:
    """Analizuje alternatywne sposoby sortowania"""
    print("\n🔄 ALTERNATYWNE SORTOWANIA")
    print("=" * 60)
    
    data = [
        {"base_id": "7742", "letter": "D", "weight": "16"},
        {"base_id": "8823", "letter": "N", "weight": "6"},
        {"base_id": "1892", "letter": "E", "weight": "17"},
        {"base_id": "8993", "letter": "{", "weight": "1"},
        {"base_id": "2288", "letter": "}", "weight": "20"},
        {"base_id": "1463", "letter": ":", "weight": "5"},
        {"base_id": "8449", "letter": "W", "weight": "8"},
        {"base_id": "9858", "letter": "R", "weight": "18"},
        {"base_id": "4942", "letter": "F", "weight": "2"},
        {"base_id": "3137", "letter": "D", "weight": "13"},
        {"base_id": "8859", "letter": "{", "weight": "0"},
        {"base_id": "6885", "letter": "G", "weight": "4"},
        {"base_id": "6847", "letter": "}", "weight": "19"},
        {"base_id": "3581", "letter": "R", "weight": "15"},
        {"base_id": "5366", "letter": "O", "weight": "10"},
        {"base_id": "6087", "letter": "R", "weight": "11"},
        {"base_id": "4338", "letter": "W", "weight": "9"},
        {"base_id": "2428", "letter": "L", "weight": "3"},
        {"base_id": "7129", "letter": "O", "weight": "14"},
        {"base_id": "9359", "letter": "L", "weight": "12"},
        {"base_id": "6409", "letter": "E", "weight": "7"}
    ]
    
    # Sortowanie według base_id
    sorted_by_base_id = sorted(data, key=lambda x: int(x['base_id']))
    flag_by_base_id = ''.join([record['letter'] for record in sorted_by_base_id])
    print(f"Sortowanie według base_id: {flag_by_base_id}")
    
    # Sortowanie według base_id (malejąco)
    sorted_by_base_id_desc = sorted(data, key=lambda x: int(x['base_id']), reverse=True)
    flag_by_base_id_desc = ''.join([record['letter'] for record in sorted_by_base_id_desc])
    print(f"Sortowanie według base_id (malejąco): {flag_by_base_id_desc}")
    
    # Sortowanie według weight (malejąco)
    sorted_by_weight_desc = sorted(data, key=lambda x: int(x['weight']), reverse=True)
    flag_by_weight_desc = ''.join([record['letter'] for record in sorted_by_weight_desc])
    print(f"Sortowanie według weight (malejąco): {flag_by_weight_desc}")
    
    # Sortowanie alfabetyczne według litery
    sorted_by_letter = sorted(data, key=lambda x: x['letter'])
    flag_by_letter = ''.join([record['letter'] for record in sorted_by_letter])
    print(f"Sortowanie alfabetyczne: {flag_by_letter}")
    
    sorted_by_weight_reverse = sorted(data, key=lambda x: int(x['weight']), reverse=False)
    flag_by_weight_reverse = ''.join([record['letter'] for record in sorted_by_weight_reverse])
    print(f"Sortowanie według weight (rosnąco): {flag_by_weight_reverse}")

def main() -> None:
    """Główna funkcja"""
    solve_flag_from_data()
    analyze_alternative_sortings()
    
    print("\n" + "=" * 60)
    print("✨ Analiza zakończona! Sprawdź wyniki powyżej.")

if __name__ == "__main__":
    main() 