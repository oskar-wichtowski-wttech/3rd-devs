import os
import json
from pathlib import Path
from typing import List, Dict
import requests
from PIL import Image
import base64
from io import BytesIO
from openai import OpenAI
import dotenv

dotenv.load_dotenv(dotenv_path="../.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a helpful assistant that categorizes content into people or hardware. 
You must respond with a valid JSON object in this exact format:
{
    "category": "people" or "hardware",
    "confidence": number between 0.00000 and 1.00000
}

For confidence scores, use this scale:
- 0.95000-1.00000: Clear, unambiguous evidence
- 0.80000-0.94999: Strong evidence with minor uncertainty
- 0.60000-0.79999: Good evidence but with some ambiguity
- 0.40000-0.59999: Moderate evidence with significant uncertainty
- 0.20000-0.39999: Weak evidence, mostly circumstantial
- 0.00000-0.19999: Very weak evidence or unclear

For 'people' category, look for:
- Human presence or traces (footprints, fingerprints, DNA)
- Captured or detained individuals
- Human activity or movement
- Biometric data or identification
- Reports of human sightings
- Evidence of human habitation
- Personal belongings or items left behind

For 'hardware' category, look for:
- Equipment repairs or maintenance
- Hardware malfunctions or issues
- Physical component replacements
- Mechanical system problems
- Technical specifications
- System diagnostics
- Physical damage to equipment

Do not categorize:
- Software-related issues as hardware
- General surveillance reports without human presence as 'people'
- Routine system checks without issues as 'hardware'

Remember: Your response must be a valid JSON object with exactly these two fields: category and confidence. Use the confidence scale above to differentiate between strong and weak evidence."""

def process_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    return categorize_content(content, file_path.name)

def process_png_file(file_path):
    try:
        with Image.open(file_path) as img:
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this image and return a JSON object with category and confidence score."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )
        return parse_categorization_response(response.choices[0].message.content, file_path.name)
    except Exception as e:
        print(f"Error processing PNG {file_path.name}: {e}")
        return []

def process_mp3_file(file_path):
    try:
        with open(file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pl"
            )
        return categorize_content(transcript.text.lower(), file_path.name)
    except Exception as e:
        print(f"Error processing MP3 {file_path.name}: {e}")
        return []

def parse_categorization_response(response: str, filename: str) -> List[Dict]:
    try:
        # Clean the response to ensure it's valid JSON
        response = response.strip()
        if not response.startswith('{'):
            response = response[response.find('{'):]
        if not response.endswith('}'):
            response = response[:response.rfind('}')+1]
            
        data = json.loads(response)
        if data.get('category') in ['people', 'hardware']:
            confidence = float(data.get('confidence', 0))
            if 0 <= confidence <= 100:
                return [{
                    'category': data['category'],
                    'confidence': round(confidence, 5),
                    'filename': filename
                }]
    except Exception as e:
        print(f"Error parsing response for {filename}: {e}")
        print(f"Raw response: {response}")
    return []

def categorize_content(content: str, filename: str) -> List[Dict]:
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": SYSTEM_PROMPT
                },
                {"role": "user", "content": content}
            ]
        )
        return parse_categorization_response(response.choices[0].message.content, filename)
    except Exception as e:
        print(f"Error categorizing content from {filename}: {e}")
        return []

def main():
    base_path = Path('/home/oskar/3rd-devs/Exercises/S01E04/pliki_z_fabryki')
    categorized_files = []
    
    for file_path in base_path.glob('*'):
        if (file_path.is_file() 
            and file_path.name != 'weapons_tests.zip' 
            and file_path.name != '2024-11-12_report-99.zip'
            and file_path.name != '2024-11-12_report-99.jpeg'
            and 'facts' not in str(file_path)
            and not file_path.suffix == '.zip'):
            print(f"Processing {file_path.name}...")
            
            if file_path.suffix == '.txt':
                results = process_text_file(file_path)
            elif file_path.suffix in ['.png', '.jpeg']:
                results = process_png_file(file_path)
            elif file_path.suffix == '.mp3':
                results = process_mp3_file(file_path)
            else:
                continue
                
            if results:
                categorized_files.extend(results)
                print(f"Processed {file_path.name} with results: {results}")
    
    # Sort by confidence and take top 3 for each category
    result = {
        "people": [],
        "hardware": []
    }
    
    # Sort files by confidence
    categorized_files.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    # Take top 3 for each category
    for item in categorized_files:
        category = item['category']
        if len(result[category]) < 3:
            result[category].append(item['filename'])
    
    # Sort filenames alphabetically within each category
    result["people"].sort()
    result["hardware"].sort()
    
    print("\nFinal categorization:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    report_payload = {
        "task": "kategorie",
        "apikey": os.getenv("DV_API_KEY"),
        "answer": result
    }
    
    try:
        report_response = requests.post(
            "https://c3ntrala.ag3nts.org/report",
            json=report_payload
        )
        print(f"\nReport response: {report_response.json()}")
    except Exception as e:
        print(f"Error sending report: {e}")

if __name__ == "__main__":
    main()
