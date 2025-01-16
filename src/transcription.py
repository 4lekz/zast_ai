import openai
import os

class TranscriptionClient:
    """
    Klasa obsługująca transkrypcję za pomocą API OpenAI.
    """

    def __init__(self, api_key=None):
        """
        Inicjalizuje klienta API OpenAI.
        :param api_key: Klucz API OpenAI.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key for OpenAI is required.")
        openai.api_key = self.api_key

    def transcribe(self, file_path, language="pl", model="whisper-1"):
        """
        Transkrybuje plik audio za pomocą API OpenAI.
        :param file_path: Ścieżka do pliku audio.
        :param language: Język pliku audio (domyślnie polski).
        :param model: Model transkrypcji (domyślnie 'whisper-1').
        :return: Transkrybowany tekst.
        """
        try:
            with open(file_path, "rb") as audio_file:
                response = openai.Audio.transcribe(
                    model=model,
                    file=audio_file,
                    language=language
                )
                return response["text"]
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None
