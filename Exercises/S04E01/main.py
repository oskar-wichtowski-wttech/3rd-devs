import os
import requests
import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")

API_KEY = os.getenv("DV_API_KEY")
DATABASE_API_URL = "https://c3ntrala.ag3nts.org/apidb"
CENTRAL_API_URL = "https://c3ntrala.ag3nts.org/report"

requests = requests.post(CENTRAL_API_URL, json={
    "task": "photos",
    "apikey": API_KEY,
    "report": "Start"
})

print(requests.json())