from scipy.spatial.distance import cosine
import json
import os
import openai
import pandas as pd
import sounddevice as sd
from base64 import b64decode
from dotenv import load_dotenv
from src.audio import record_audio
from src.transcription import TranscriptionClient
from src.report import ReportGenerator
from src.courses import CourseManager
from src.openai_utils import OpenAIClient
from src.data import course_list, opcje_menu
from src.utils import normalize_training_proposals


load_dotenv()
APIKey = os.getenv("OPENAI_API_KEY")

if APIKey:
    print("API key loaded successfully.")
else:
    print("API key not found. Please check your .env file.")


    
def main():
    try:
        # Initialize the OpenAI client
        openai_client = OpenAIClient(APIKey)
        print("OpenAIClient instance created successfully.")
    except ValueError as e:
        print(f"Error initializing OpenAI client: {e}")
        return

    # Initialize other components
    course_manager = CourseManager(openai_client)
    report_generator = ReportGenerator(output_path="reports/employee_report.pdf")
    full_list_of_courses = []
    print("Którą wersję programu chcesz uruchomić:")
    print("0. Stabilna.")
    print("1. Beta.")
    
    try:
        ver = int(input("Wybierz wersję programu: "))
        if ver not in [0, 1]:
            raise ValueError("Nieprawidłowy wybór, przekierowanie do wersji stabilnej")
    except ValueError:
        print("Nieprawidłowy wybór. Przekierowanie do wersji stabilnej")
        ver = 0

    while True:


        
        if ver==1:
            print("\nCo chciałbyś zrobić?")
            for opcja in opcje_menu:
                print(f"- {opcja}")

            wejscie_uzytkownika = input("Opisz swoją opcję: ").lower()
            choice = openai_client.user_navigation(wejscie_uzytkownika)

        elif ver==0:
            # Display menu options
            print("\nCo mam zrobić:")
            print("1. Kiedy odbywa się następne spotkanie.")
            print("2. Nagraj rozmowę.")
            print("3. Wygeneruj raport na podstawie nagrania.")
            print("4. Wygeneruj raport na podstawie transkrypcji.")
            print("5. Podaj dostępne kursy na bazie raportu.")
            print("6. Pokaż efektywność pracy pracownika.")
            print("0. Wyjście.")
            try:
                choice = int(input("Wprowadź swój wybór: "))
            except ValueError:
                print("Nieprawidłowy wybór.")
                continue
        if choice == 0:
            print("Zamykanie programu. Do widzenia!")
            break    
        elif choice == 1:
            print("Funkcja 'Sprawdź, kiedy jest następne spotkanie' nie została jeszcze zaimplementowana.")
        elif choice == 2:
            print("Nagrywanie rozmowy...")
            audio_path = "output.wav"
            record_audio(audio_path, duration=5) 
            transcription_text = openai_client.transcribe_audio(audio_path)
            if transcription_text:
                print(f"Transkrypcja zakończona:\n{transcription_text}")
                
                # Zapis do pliku
                os.makedirs("data", exist_ok=True)  # Upewnij się, że folder 'data' istnieje
                transcription_file_path = "data/transcription_text.txt"
                with open(transcription_file_path, "w", encoding="utf-8") as file:
                    file.write(transcription_text)
                print(f"Transkrypcja została zapisana w pliku: {transcription_file_path}")
            else:
                print("Nie udało się przetworzyć nagrania audio.")
        elif choice == 3:
            print("Generowanie raportu na bazie nagrania...")
            audio_path="output.wav"
            transcription_text = openai_client.transcribe_audio(audio_path)
            # transcription_text = test_text  # Podmień na faktyczną transkrypcję
            analysis = openai_client.process_transcription_pipeline(transcription_text)
            if not analysis:
                print("Nie udało się przeprowadzić analizy transkrypcji.")
                continue   
            
            analysis["Propozycje szkoleń"] = normalize_training_proposals(analysis["Propozycje szkoleń"])
            _, full_list_of_courses = course_manager.get_courses_for_worker(analysis)
            if analysis:
                print("Przetwarzam analizę:")
                report = openai_client.generate_report_with_function_calling(analysis)
                function_name, params = openai_client.process_params(report, full_list_of_courses)
            else:
                print("Failed to analyze transcription.")
            if function_name == "generate_report":
                report_generator = ReportGenerator(output_path="reports/employee_report.pdf")
                report_generator.generate_and_save_report(params)
        elif choice == 4:
            print("Generowanie raportu na bazie transkrypcji...")
            transcription_file_path = "data/transcription.txt"
            if not os.path.exists(transcription_file_path):
                print(f"Nie znaleziono pliku z transkrypcją: {transcription_file_path}")
                continue
            
            try:
                with open(transcription_file_path, "r", encoding="utf-8") as file:
                    transcription_text = file.read()
                    print("Transkrypcja załadowana z pliku.")
            except Exception as e:
                print(f"Błąd podczas odczytu pliku: {e}")
                continue
            analysis = openai_client.process_transcription_pipeline(transcription_text)
            if not analysis:
                print("Nie udało się przeprowadzić analizy transkrypcji.")
                continue   
            
            analysis["Propozycje szkoleń"] = normalize_training_proposals(analysis["Propozycje szkoleń"])
            _, full_list_of_courses = course_manager.get_courses_for_worker(analysis)
            if analysis:
                # print("Analysis and segmentation:")
                # print(json.dumps(analysis, indent=4, ensure_ascii=False))
                print("Przetwarzam analizę:")
                report = openai_client.generate_report_with_function_calling(analysis)
                function_name, params = openai_client.process_params(report, full_list_of_courses)
            else:
                print("Failed to analyze transcription.")
            if function_name == "generate_report":
                report_generator = ReportGenerator(output_path="reports/employee_report.pdf")
                report_generator.generate_and_save_report(params)
        elif choice == 5:
            if full_list_of_courses:
                if all(isinstance(item, list) for item in full_list_of_courses):
                    # List of lists                    
                    print("Proponowany zestaw kursów:")
                    for sublist in full_list_of_courses:
                        for course in sublist:
                            print(f"- {course}")
                else:
                    # Flat list
                    print("Proponowany zestaw kursów:")
                    for course in full_list_of_courses:
                        print(f"- {course}")
            else:
                print("Kursy ma bazie ostatniego przeprowadzonego raportu: ")            
                analyzed_file_path = "data/analyzed_transcription.json"
                if not os.path.exists(analyzed_file_path):
                    print(f"Nie znaleziono pliku z analizą: {analyzed_file_path}")
                    continue
                try:
                    # Wczytanie pliku JSON
                    with open(analyzed_file_path, "r", encoding="utf-8") as file:
                        analysis = json.load(file)
                        print("Dane z analizy zostały załadowane.")
                    _, full_list_of_courses = course_manager.get_courses_for_worker(analysis)
                    
                    if full_list_of_courses:
                        if all(isinstance(item, list) for item in full_list_of_courses):
                            # List of lists
                            
                            print("Proponowany zestaw kursów:")
                            for sublist in full_list_of_courses:
                                for course in sublist:
                                    print(f"- {course}")
                        else:
                            # Flat list
                            print("Proponowany zestaw kursów:")
                            for course in full_list_of_courses:
                                print(f"- {course}")
                except Exception as e:
                    print(f"Błąd podczas odczytu pliku JSON: {e}")
                    continue
                
if __name__ == "__main__":
    main()
