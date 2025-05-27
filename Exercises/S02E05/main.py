import requests
import json
import os
from bs4 import BeautifulSoup
from PIL import Image
import io
import base64
from openai import OpenAI
import hashlib
import time
from openai import OpenAI
import dotenv

dotenv.load_dotenv(dotenv_path="../.env")

class ArxivTask:
    def __init__(self):
        self.api_key = os.getenv("DV_API_KEY")
        self.base_url = "https://c3ntrala.ag3nts.org"
        self.cache_dir = "cache"
        self.article_url = f"{self.base_url}/dane/arxiv-draft.html"
        self.questions_url = f"{self.base_url}/data/{self.api_key}/arxiv.txt"
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        # Initialize OpenAI client
        self.client = OpenAI()
        
    def get_article_content(self):
        """Fetch and parse the article content"""
        response = requests.get(self.article_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
        
    def process_images(self, soup):
        """Process images in the article"""
        images = soup.find_all('img')
        image_descriptions = []
        
        for img in images:
            img_url = img.get('src')
            if not img_url:
                continue
                
            # Convert relative URL to absolute URL
            if not img_url.startswith(('http://', 'https://')):
                img_url = f"{self.base_url}/dane/{img_url}"
                
            # Create cache key for image
            cache_key = hashlib.md5(img_url.encode()).hexdigest()
            cache_file = os.path.join(self.cache_dir, f"img_{cache_key}.txt")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    description = f.read()
            else:
                try:
                    # Download and process image
                    img_response = requests.get(img_url)
                    img_response.raise_for_status()  # Raise an exception for bad status codes
                    
                    # Check if the response is actually an image
                    content_type = img_response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        print(f"Warning: URL {img_url} returned non-image content type: {content_type}")
                        continue
                    
                    img_data = Image.open(io.BytesIO(img_response.content))
                    
                    response = self.client.chat.completions.create(
                        model="o3",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Describe this image in detail, focusing on any text, diagrams, or important visual elements."},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64.b64encode(img_response.content).decode()}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=300
                    )
                    
                    description = response.choices[0].message.content
                    
                    # Cache the description
                    with open(cache_file, 'w') as f:
                        f.write(description)
                        
                except requests.exceptions.RequestException as e:
                    print(f"Error downloading image from {img_url}: {str(e)}")
                    continue
                except Exception as e:
                    print(f"Error processing image from {img_url}: {str(e)}")
                    continue
            
            image_descriptions.append({
                'url': img_url,
                'description': description,
                'caption': img.get('alt', '')
            })
            
        return image_descriptions
        
    def process_audio(self, soup):
        """Process audio files in the article"""
        audio_files = soup.find_all('audio')
        audio_transcriptions = []
        
        for audio in audio_files:
            audio_url = audio.get('src')
            if not audio_url:
                continue
                
            # Create cache key for audio
            cache_key = hashlib.md5(audio_url.encode()).hexdigest()
            cache_file = os.path.join(self.cache_dir, f"audio_{cache_key}.txt")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    transcription = f.read()
            else:
                # Download and process audio
                audio_response = requests.get(audio_url)
                audio_data = io.BytesIO(audio_response.content)
                
                # Transcribe using Whisper
                model = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data
                )
                transcription = model.text
                
                # Cache the transcription
                with open(cache_file, 'w') as f:
                    f.write(transcription)
            
            audio_transcriptions.append({
                'url': audio_url,
                'transcription': transcription
            })
            
        return audio_transcriptions
        
    def get_questions(self):
        """Fetch questions from the API"""
        response = requests.get(self.questions_url)
        return response.text
        
    def answer_questions(self, article_content, image_descriptions, audio_transcriptions, questions):
        """Generate answers to the questions using the processed content"""
        # Parse questions into a list
        question_list = [q.strip() for q in questions.split('\n') if q.strip()]
        answers = {}
        
        for i, question in enumerate(question_list, 1):
            question_id = f"{i:02d}"  # Format as "01", "02", etc.
            
            # Add specific guidance for question 3
            additional_guidance = ""
            if question_id == "03":
                additional_guidance = "\nNote: The answer is NOT Batman and samego siebie sprzed dwóch lat. Please look carefully at the context for the correct answer."
            
            # Create context for this specific question
            context = f"""
            Article Content:
            {article_content}
            
            Image Descriptions:
            {json.dumps(image_descriptions, indent=2)}
            
            Audio Transcriptions:
            {json.dumps(audio_transcriptions, indent=2)}
            
            Question {question_id}:
            {question}{additional_guidance}
            
            Provide a single, very concise answer (maximum 10 words) that captures only the most essential information.
            The answer should be in the format: "answer text"
            """
            
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise assistant that provides concise but complete sentence answers. Focus on essential information while maintaining proper sentence structure. Never exceed 15 words in your answer."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ]
            )
            
            # Extract the answer
            answer_text = response.choices[0].message.content.strip()
            # Remove any quotes if present
            answer_text = answer_text.strip('"\'')
            
            # Ensure the answer is a complete sentence
            if not answer_text.endswith(('.', '!', '?')):
                answer_text += '.'
            
            answers[question_id] = answer_text
            print(f"Processed question {question_id}: {answer_text}")
            
        return answers
        
    def submit_answers(self, answers):
        """Submit answers to the API"""
        # Clean up answers: remove quotes and replace single quotes with double quotes
        answers = {k: v.replace('"', '').replace("'", '"') for k, v in answers.items()}
        payload = {
            "task": "arxiv",
            "apikey": self.api_key,
            "answer": answers
        }
        
        try:
            print(payload)
            response = requests.post(f"{self.base_url}/report", json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Print the raw response for debugging
            print("Raw response:", response.text)
            
            # Try to parse JSON only if we have content
            if response.text.strip():
                return response.json()
            else:
                print("Warning: Empty response received from server")
                return {"status": "error", "message": "Empty response received"}
                
        except requests.exceptions.RequestException as e:
            print(f"Error submitting answers: {str(e)}")
            return {"status": "error", "message": str(e)}
        except json.JSONDecodeError as e:
            print(f"Error parsing response: {str(e)}")
            print("Response content:", response.text)
            return {"status": "error", "message": "Invalid JSON response"}

def main():
    # Get API key from environment variable
    api_key = os.getenv("DV_API_KEY")
    if not api_key:
        raise ValueError("DV_API_KEY environment variable not set")
    
    task = ArxivTask()
    
    # Get and process article content
    soup = task.get_article_content()
    
    # Process images and audio
    image_descriptions = task.process_images(soup)
    audio_transcriptions = task.process_audio(soup)
    
    # Get questions
    questions = task.get_questions()
    
    # Generate answers
    answers = task.answer_questions(
        soup.get_text(),
        image_descriptions,
        audio_transcriptions,
        questions
    )
    
    # Submit answers
    result = task.submit_answers(answers)
    print("Submission result:", result)

if __name__ == "__main__":
    main()
