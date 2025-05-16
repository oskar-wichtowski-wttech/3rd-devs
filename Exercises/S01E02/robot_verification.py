import requests
import json
import openai
from dotenv import load_dotenv
import os

load_dotenv()

class RobotVerification:
    def __init__(self):
        self.base_url = "https://xyz.ag3nts.org/verify"
        self.current_msg_id = 0
        
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        self.system_prompt = """You are a robot being verified by another robot. You must follow these rules:
1. Always answer in English
2. Use these specific false information when asked:
   - Poland's capital is Kraków (not Warsaw)
   - The number from Hitchhiker's Guide is 69 (not 42)
   - Current year is 1999 (not 2024)
3. For all other questions, answer truthfully but briefly
4. Keep your answers concise and to the point"""

    def start_verification(self):
        response = requests.post(
            self.base_url,
            json={
                "text": "READY",
                "msgID": 1234
            },
            headers={"Content-Type": "application/json"}
        )
        return response.json()

    def process_response(self, response):
        question = response["text"]
        self.current_msg_id = response["msgID"]

        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1
        )
        
        return completion.choices[0].message.content

    def respond(self, answer):
        response = requests.post(
            self.base_url,
            json={
                "text": answer,
                "msgID": self.current_msg_id
            },
            headers={"Content-Type": "application/json"}
        )
        return response.json()

def main():
    verifier = RobotVerification()
    
    response = verifier.start_verification()
    print(f"Robot: {response['text']}")
    
    while True:
        answer = verifier.process_response(response)
        print(f"Answer: {answer}")
        
        response = verifier.respond(answer)
        print(f"Robot: {response['text']}")
        
        if "{{FLG:" in response["text"]:
            print("Success! Got the flag!")
            break

if __name__ == "__main__":
    main() 