import openai
from scipy.spatial.distance import cosine
import json
# from src.openai_utils import OpenAIClient

class OpenAIClient:
    def __init__(self, api_key):
        """
        Inicjalizuje klienta OpenAI.
        :param api_key: Klucz API OpenAI.
        """
        if not self.check_openai_api_key(api_key):
            raise ValueError("Invalid OpenAI API key.")
        openai.api_key = api_key
        self.client = openai
    @staticmethod
    def check_openai_api_key(api_key):
        client = openai.OpenAI(api_key=api_key)
        try:
            client.models.list()
        except openai.AuthenticationError:
            return False
        else:
            return True

    def generate_embedding(self, text, model="text-embedding-ada-002"):
        """
        Generuje embedding dla podanego tekstu.
        :param text: Tekst do przetworzenia.
        :param model: Model embeddingu (domyślnie: "text-embedding-ada-002").
        :return: Wektor embeddingu.
        """
        try:
            text = text.replace("\n", " ")
            return self.client.embeddings.create(input = [text], model=model).data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
        
    def transcribe_audio(self, audio_path, model="whisper-1", language="pl"):
        """
        Transcribes an audio file to text using OpenAI's Whisper model.
        """
        try:
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=language
                )
                return response.text
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None
        
    def generate_report_with_function_calling(self, analysis_data):
        """
        Generuje raport na podstawie analizy transkrypcji za pomocą OpenAI API.
        :param analysis_data: Dane analizy transkrypcji.
        :return: Wygenerowany raport w formacie JSON.
        """
        function_desc = [
            {
                "type": "function",
                "function": {
                    "name": "generate_report",
                    "description": "Generuje raport podsumowujący ocenę pracownika na podstawie analizy.",
                    "parameters": {
                        "type": "object",
                        "required": [
                            "Osiągnięcia",
                            "Obszary do poprawy",
                            "Cele na przyszłość",
                            "Cele SMART",
                            "Propozycje szkoleń",
                            "Uwagi dotyczące współpracy"
                        ],
                        "properties": {
                            "Osiągnięcia": {"type": "string", "description": "Opis osiągnięć pracownika."},
                            "Obszary do poprawy": {"type": "string", "description": "Obszary wymagające poprawy."},
                            "Cele na przyszłość": {"type": "string", "description": "Cele pracownika."},
                            "Cele SMART": {"type": "string", "description": "Cele zgodne z metodologią SMART."},
                            "Propozycje szkoleń": {"type": "string", "description": "Propozycje szkoleń."},
                            "Uwagi dotyczące współpracy": {"type": "string", "description": "Uwagi o współpracy."},
                        },
                        "additionalProperties": False
                    }
                }
            }
        ]

        prompt = f"""
        Analiza transkrypcji:
        {analysis_data}

        Na podstawie analizy, wygeneruj raport.
        """
        messages = [
            {"role": "system", "content": "Nie używaj polskich znaków. Jesteś systemem HR do generowania raportów ocen pracowniczych na podstawie przeprowadzonej rozmowy z pracownikiem. Jeżeli jakiś argument nie został poruszony to wpisz '-'"},
            {"role": "user", "content": prompt},

        ]
        try:
            chat_completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=function_desc,
                temperature=0,
            )
            # result = chat_completion["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
            return chat_completion
        except Exception as e:
            print(f"Error generating report: {e}")
            return None
    

    def user_navigation(self, wejscie_uzytkownika):
        prompt = f"""
            Jesteś asystentem HR i masz za zadanie przeanalizować wymaganie, które zgłosił pracownik HR.
            Masz odpowiedzieć samą liczbą.
            Jeżeli pracownik będzie chciał:
            1 - apytać o następne spotkanie
            2 - nagrać rozmowę
            3 - raport z nagrania
            4 - raport z transkrypcji
            4 - kursy na bazie raportu
            6 - efektywność pracy pracownika
            0 - wyjść lub opuścić program
            Jeżeli czegoś nie ma w rozmowie to wpisz '-1'

            Pamiętaj, ma to być pojedyncza cyfra

            Transkrypcja:
            {wejscie_uzytkownika}
            Odpowiedź ma być tylko jedną liczbą
            """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                {"role": "system", "content": "Jesteś asystentem HR."},
                {"role": "user", "content": prompt}
            ])
            przewidywana_akcja = response.choices[0].message.content.strip()
            wybor = int(przewidywana_akcja)
        except Exception as e:
            print(f"Nie udało się zinterpretować Twojego wejścia: {e}")
            wybor = -1

        return wybor

    def analyze_and_segment_transcription(self, transcription_text):
        """
        Analyzes and segments transcription text into predefined sections.
        """
        prompt = f"""
        Jesteś asystentem HR i masz za zadanie przeanalizować transkrypcję rozmowy z pracownikiem.
        Jeżeli czegoś nie ma w rozmowie to wpisz '-'
        Podziel tekst na następujące sekcje:
        1. Osiągnięcia.
        2. Obszary do poprawy.
        3. Cele na przyszłość.
        4. Cele SMART. (Specyficzne, Mierzalne, Osiągalne, Realistyczne, Terminowe)
        5. Propozycje szkoleń.
        6. Uwagi dotyczące współpracy.
        Transkrypcja:
        {transcription_text}

        Podziel tekst w formacie JSON. Każda sekcja powinna zawierać odpowiednią treść.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Jesteś asystentem HR."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={ "type": "json_object" }
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error during transcription analysis: {e}")
            return None
    # Pipeline przetwarzania transkrypcji

    def save_analysis_to_file(self, analysis_result, output_file="./data/analyzed_transcription.json"):
        with open(output_file, 'w', encoding='utf-8') as file:
            # file.write(analysis_result)
            json.dump(analysis_result, file, ensure_ascii=False, indent=4)
        print(f"Wynik analizy zapisano w pliku: {output_file}")

    def process_transcription_pipeline(self, transcription_text, audio_path='output.wav'):
        # Załaduj transkrypcję
        # transcription_text = transcribe(audio_path)
        # transcription_text = test_text
        if transcription_text:
            print("Transkrypcja załadowana. Rozpoczynam analizę...")

            # Analiza i segmentacja
            analysis_result = self.analyze_and_segment_transcription(transcription_text)
            if analysis_result:
                print("Analiza zakończona.")
                analysis_result = search_params = json.loads(analysis_result)
                # print(analysis_result)
                self.save_analysis_to_file(analysis_result=analysis_result)
                return analysis_result 
            else:
                print("Nie udało się przeprowadzić analizy.")
                return None
        else:
            print("Nie udało się załadować transkrypcji.")
    @staticmethod
    def process_params(chat_completion, courses_list):
        message = chat_completion.choices[0].message
        if message.content is not None:
            print(f"Content: {message.content}")
            return None
        elif message.tool_calls is not None and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]
            if tool_call.function.arguments is not None:
                # print(f"Arguments: {tool_call.function.arguments}")
                # print(f"Function: {tool_call.function.name}")
                search = tool_call.function.arguments
                function_name = tool_call.function.name
                params = json.loads(search)
                params['dostępne szkolenia'] = courses_list
                for key, value in params.items():
                    if isinstance(value, str) and value.lower() == "dowolny":
                        params[key] = None
                    elif isinstance(value, (int, float)) and value == 0:
                        params[key] = None
                return function_name, params
            else:
                print("Neither content nor arguments are available.")
                return None

        else:
            print("Neither content nor arguments are available.")
            return None
