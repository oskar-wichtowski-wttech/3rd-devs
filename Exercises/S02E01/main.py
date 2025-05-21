from openai import OpenAI
from pathlib import Path
import os
import dotenv
import requests

dotenv.load_dotenv(dotenv_path="../.env")

class AudioTranscription:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.apikey = os.getenv("DV_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)
        self.transcriptions = []

    def _save_transcription(self, file: Path, transcription: str):
        with open(f"transcriptions/{file.stem}.txt", "w") as f:
            f.write(transcription)

    def _transcribe(self, file: Path) -> str:
        model = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=file
        )
        return model.text

    def craete_transcriptions(self) -> list[str]:
        files_to_transcript = self._get_m4a_files()
        for file in files_to_transcript:
            transcription_file = Path(f"transcriptions/{file.stem}.txt")
            if transcription_file.exists():
                print(f"Loading existing transcription for {file.stem}")
                with open(transcription_file, "r") as f:
                    transcription = f.read()
            else:
                print(f"Creating new transcription for {file.stem}")
                transcription = self._transcribe(file)
                self._save_transcription(file, transcription)
            self.transcriptions.append(transcription)
        return self.transcriptions

    def send_report(self, answer: str) -> dict:
        request = requests.post(
            "https://c3ntrala.ag3nts.org/report",
            json={"task": "mp3", "answer": answer, "apikey": self.apikey}
        )
        print(request.json())
        return request.json()
    
    def get_exercise_answer(self) -> str:
        if not self.transcriptions:
            raise ValueError("No transcriptions available. Please create transcriptions first.")
            
        combined_transcriptions = "\n\n".join([f"Zeznanie {file.stem}:\n{transcription}" for file, transcription in zip(self._get_m4a_files(), self.transcriptions)])
        prompt = f"""
            Jesteś pomocnym asystentem, który może odpowiedzieć na pytania dotyczące transkrypcji nagrania audio.
            Pobraliśmy i ztranskrybowaliśmy nagrania z przesłuchań świadków oskarżonych o kontakty z profesorem Majem.
            Zeznania mogą się wzajemnie wykluczać lub uzupełniać. 
            Centrala warunkowo dopuściła do analizy nagranie Rafała, ponieważ jego stan od pewnego czasu jest bardzo niestabilny,
            ale to jedyna osoba, co do której jesteśmy pewni, że utrzymywała bliskie kontakty z profesorem.

            Oto transkrypcje nagrań:
            {combined_transcriptions}

            Twoim zadaniem jest ustalenie nazwy ulicy, na której znajduje się konkretny instytut uczelni, gdzie wykłada profesor Andrzej Maj.
            Pamiętaj, że szukamy ulicy konkretnego instytutu, a nie głównej siedziby uczelni.

            Proszę o krok po krokową analizę:
            1. Przeanalizuj każdą transkrypcję pod kątem wzmianek o lokalizacji instytutu
            2. Zwróć szczególną uwagę na zeznania Rafała
            3. Użyj swojej wiedzy o tej konkretnej uczelni, aby zweryfikować informacje
            4. Podaj nazwę ulicy w standardowym formacie (bez przedrostków: ul. , ulica , ulica profesora, itp.):
            "nazwa ulicy"
        """
        print("Prompt: ",prompt)
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def _get_m4a_files(self):
        return list(Path("przesluchania").glob("*.m4a"))

if __name__ == "__main__":
    audio_transcription = AudioTranscription()
    transcriptions = audio_transcription.craete_transcriptions()
    answer = audio_transcription.get_exercise_answer()
    print(answer)
    report = audio_transcription.send_report(answer)
    print(report)
