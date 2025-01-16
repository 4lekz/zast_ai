import sounddevice as sd
import wavio


def record_audio(output_file, duration=5, sample_rate=44100, device_index=None):
    """
    Nagrywa dźwięk z mikrofonu i zapisuje go do pliku WAV.

    :param output_file: Nazwa pliku wyjściowego (np. "output.wav").
    :param duration: Czas nagrywania w sekundach.
    :param sample_rate: Próbkowanie (domyślnie 44100 Hz).
    :param device_index: Indeks urządzenia wejściowego (opcjonalnie).
    """
    print(f"Nagrywanie... Mów przez {duration} sekund.")
    try:
        # Wybór urządzenia na podstawie indeksu
        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,  # Zmiana na 1 kanał (mono)
            dtype='int16',
            device=device_index  # Wybierz konkretne urządzenie
        )
        sd.wait()  # Czekaj, aż nagrywanie się zakończy
        print(f"Nagrywanie zakończone. Zapisuję plik jako {output_file}...")
        wavio.write(output_file, audio_data, sample_rate, sampwidth=2)
        print("Plik zapisany!")
    except Exception as e:
        print(f"Wystąpił błąd podczas nagrywania: {e}")