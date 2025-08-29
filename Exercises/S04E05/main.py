import os
import requests
import json
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import openai
from typing import Dict, List, Any, Optional
import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")

# API keys
DV_API_KEY = os.getenv("DV_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# URLs
CENTRAL_API_URL = "https://c3ntrala.ag3nts.org/report"
QUESTIONS_URL = f"https://c3ntrala.ag3nts.org/data/{DV_API_KEY}/notes.json"

# PDF path
PDF_PATH = "notatnik-rafala.pdf"

def extract_text_from_pdf_pages(pdf_path: str, start_page: int = 0, end_page: int = 17) -> str:
    """Extract text from PDF pages 1-18 (0-17 in 0-based indexing)"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(start_page, end_page + 1):
            page = doc.load_page(page_num)
            text += page.get_text()
            text += "\n\n"
        
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_image_from_pdf_page(pdf_path: str, page_num: int = 18) -> Optional[Image.Image]:
    """Extract page 19 (18 in 0-based indexing) as image for OCR"""
    try:
        # Try to convert with higher DPI for better OCR
        images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1, dpi=300)
        if images:
            return images[0]
        return None
    except Exception as e:
        print(f"Error converting PDF page to image: {e}")
        print("Make sure poppler-utils is installed: sudo apt-get install poppler-utils")
        return None

def perform_ocr_on_image(image: Image.Image) -> str:
    """Perform OCR on the image to extract text"""
    try:
        # Configure tesseract for better Polish text recognition
        custom_config = r'--oem 3 --psm 6 -l pol'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text
    except Exception as e:
        print(f"Error performing OCR: {e}")
        return ""

def get_questions() -> Dict[str, str]:
    """Fetch questions from the API"""
    try:
        response = requests.get(QUESTIONS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching questions: {e}")
        return {}

def decipher_ocr_with_llm(ocr_text: str) -> str:
    """Use LLM to decipher and make sense of OCR text from page 19"""
    if not OPENAI_API_KEY:
        return ocr_text
    
    openai.api_key = OPENAI_API_KEY
    
    prompt = f"""Masz przed sobą tekst z OCR (Optical Character Recognition) ze skanu notatki. 
Tekst może zawierać błędy OCR, ale musisz go rozszyfrować i zrozumieć.

Tekst z OCR:
{ocr_text}

Twoje zadanie:
1. Rozszyfruj i popraw błędy OCR
2. Zrozum sens notatek
3. Przedstaw to w czytelnej formie
4. Zwróć szczególną uwagę na nazwy miejscowości, daty, nazwiska

Odpowiedz w języku polskim, zachowując oryginalny sens notatek."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem w rozszyfrowywaniu i interpretacji tekstów z OCR. Potrafisz poprawiać błędy i odtwarzać oryginalny sens."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        deciphered_text = response.choices[0].message.content.strip()
        print(f"LLM deciphered OCR text: {deciphered_text[:200]}...")
        return deciphered_text
    except Exception as e:
        print(f"Error deciphering OCR with LLM: {e}")
        return ocr_text

def ask_llm_for_answer(context: str, question: str, question_id: str, previous_attempts: List[Dict[str, str]] = None) -> str:
    """Ask LLM to find answer in the context"""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")
    
    openai.api_key = OPENAI_API_KEY
    
    # Build prompt with context and previous attempts
    prompt = f"""Przeanalizuj poniższy tekst notatnika Rafała i odpowiedz na pytanie.

NOTATNIK RAFAŁA:
{context}

PYTANIE {question_id}: {question}

"""
    
    if previous_attempts:
        prompt += "\nPOPRZEDNIE PRÓBY (NIE UŻYWAJ TYCH ODPOWIEDZI):\n"
        for attempt in previous_attempts:
            prompt += f"- Próba: {attempt['answer']} - Błędna\n"
            if 'hint' in attempt:
                prompt += f"  Podpowiedź: {attempt['hint']}\n"
        prompt += "\nUwzględnij podpowiedzi i spróbuj ponownie, unikając poprzednich błędnych odpowiedzi.\n"
    
    # Add specific guidance for question 01
    if question_id == "01":
        prompt += "\nWAŻNE: Zwróć szczególną uwagę na fragment 'nie mogę uwierzyć, że jestem w 20... roku'. To wskazuje na konkretny rok, nie na rok 2024. Analizuj dokładnie wszystkie wzmianki o latach w tekście.\n"
    
    prompt += "\nOdpowiedz zwięźle i konkretnie na pytanie."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem w analizie dokumentów. Odpowiadaj zwięźle i konkretnie na pytania na podstawie podanego tekstu. Zwróć szczególną uwagę na konkretne daty i liczby."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"LLM response for {question_id}: {answer}")
        return answer
    except Exception as e:
        print(f"Error asking LLM: {e}")
        return ""

def submit_report(answers: Dict[str, str]) -> Dict[str, Any]:
    """Submit answers to the central API"""
    payload = {
        "task": "notes",
        "apikey": DV_API_KEY,
        "answer": answers
    }
    
    print(f"Submitting payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(CENTRAL_API_URL, json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return {}
    except Exception as e:
        print(f"Error submitting report: {e}")
        return {}

def save_data_locally(questions: Dict[str, str], answers: Dict[str, str], context: str) -> None:
    """Save data locally for debugging and iteration"""
    data = {
        "questions": questions,
        "answers": answers,
        "context": context,
        "timestamp": str(datetime.datetime.now())
    }
    
    with open("notes_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Data saved locally to notes_data.json")

def iterative_answer_correction(context: str, questions: Dict[str, str], max_iterations: int = 3) -> Dict[str, str]:
    """Iteratively correct answers based on API feedback"""
    answers = {}
    incorrect_answers = {}
    
    # Initial answers
    print("Getting initial answers...")
    for question_id, question_text in questions.items():
        print(f"\nProcessing question {question_id}: {question_text[:50]}...")
        answer = ask_llm_for_answer(context, question_text, question_id)
        if answer:
            answers[question_id] = answer
            print(f"Initial answer for {question_id}: {answer}")
        else:
            answers[question_id] = "Brak odpowiedzi"
    
    # Iterative correction
    for iteration in range(max_iterations):
        print(f"\n=== ITERATION {iteration + 1} ===")
        
        # Submit current answers
        result = submit_report(answers)
        
        if not result:
            print("Failed to submit report, stopping iterations")
            break
        
        # Check if all answers are correct
        if "code" not in result or result["code"] == 0:
            print("All answers are correct!")
            break
        
        # Parse incorrect answers and hints
        if "incorrect" in result:
            incorrect_questions = result["incorrect"]
            for qid in incorrect_questions:
                if qid in answers:
                    incorrect_answers[qid] = {
                        "answer": answers[qid],
                        "hint": result.get("hint", {}).get(qid, "")
                    }
        
        # Get hints for specific questions
        if "hint" in result:
            if isinstance(result["hint"], dict):
                for qid, hint in result["hint"].items():
                    if qid in answers:
                        if qid not in incorrect_answers:
                            incorrect_answers[qid] = {}
                        incorrect_answers[qid]["hint"] = hint
        
        # Correct incorrect answers
        corrected_count = 0
        for question_id, question_text in questions.items():
            if question_id in incorrect_answers:
                print(f"\nCorrecting question {question_id}...")
                print(f"Previous answer: {incorrect_answers[question_id]['answer']}")
                print(f"Hint: {incorrect_answers[question_id].get('hint', 'No hint')}")
                
                # Get new answer with previous attempts context
                new_answer = ask_llm_for_answer(
                    context, 
                    question_text, 
                    question_id, 
                    [incorrect_answers[question_id]]
                )
                
                if new_answer and new_answer != incorrect_answers[question_id]["answer"]:
                    answers[question_id] = new_answer
                    corrected_count += 1
                    print(f"Corrected answer: {new_answer}")
                else:
                    print("No correction made")
        
        if corrected_count == 0:
            print("No corrections made in this iteration, stopping")
            break
        
        print(f"Corrected {corrected_count} answers in iteration {iteration + 1}")
    
    return answers

def main() -> None:
    """Main function executing the task"""
    if not DV_API_KEY:
        raise ValueError("DV_API_KEY environment variable is required")
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    print("Starting notes task...")
    
    # Step 1: Extract text from PDF pages 1-18
    print("Step 1: Extracting text from PDF pages 1-18...")
    text_content = extract_text_from_pdf_pages(PDF_PATH, 0, 17)
    
    if not text_content:
        raise RuntimeError("Failed to extract text from PDF")
    
    print(f"Extracted {len(text_content)} characters from PDF pages 1-18")
    print(f"First 500 characters: {text_content[:500]}...")
    
    # Step 2: Extract and OCR page 19
    print("Step 2: Processing page 19 with OCR...")
    page19_image = extract_image_from_pdf_page(PDF_PATH, 18)
    
    if page19_image:
        ocr_text = perform_ocr_on_image(page19_image)
        print(f"OCR extracted {len(ocr_text)} characters from page 19")
        print(f"OCR text: {ocr_text[:500]}...")
        
        # Step 2a: Use LLM to decipher OCR text
        print("Step 2a: Using LLM to decipher OCR text...")
        deciphered_ocr = decipher_ocr_with_llm(ocr_text)
        
        # Combine text content with deciphered OCR
        full_context = text_content + "\n\nSTRONA 19 (ROZSZYFROWANA):\n" + deciphered_ocr
    else:
        print("Warning: Could not extract page 19, using only text content")
        full_context = text_content
    
    # Step 3: Get questions
    print("Step 3: Fetching questions...")
    questions = get_questions()
    
    if not questions:
        raise RuntimeError("Failed to fetch questions")
    
    print(f"Fetched {len(questions)} questions:")
    for qid, qtext in questions.items():
        print(f"  {qid}: {qtext}")
    
    # Step 4: Get answers iteratively
    print("Step 4: Getting answers iteratively...")
    answers = iterative_answer_correction(full_context, questions)
    
    # Step 5: Save final data locally
    print("Step 5: Saving final data locally...")
    save_data_locally(questions, answers, full_context)
    
    print("Task completed!")

if __name__ == "__main__":
    import datetime
    main()
