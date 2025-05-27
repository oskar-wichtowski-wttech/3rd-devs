from openai import OpenAI
from pathlib import Path
import os
import dotenv
import requests

dotenv.load_dotenv(dotenv_path="../.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

request = requests.get(
    f"https://c3ntrala.ag3nts.org/data/{os.getenv('DV_API_KEY')}/robotid.json",
)

prompt = f"""
You are an artist. You are given a description of a robot.

You need to generate a description of a robot that is similar to the given description.

The description of the robot should be in the following format:

{request.json()}

The created image should be in the .png format.

The image should be 1024x1024 pixels.

The image should be in the style of a cartoon.
"""

response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
)

image_url = response.data[0].url

# Download and save the image
image_response = requests.get(image_url)
image_path = Path("robot.png")
image_path.write_bytes(image_response.content)

report_payload = {
    "task": "robotid",
    "apikey": os.getenv("DV_API_KEY"),
    "answer": image_url
}

report_response = requests.post(
    "https://c3ntrala.ag3nts.org/report",
    json=report_payload
)

print(f"Image saved to: {image_path.absolute()}")
print(f"Image URL: {image_url}")
print(f"Report response: {report_response.json()}")