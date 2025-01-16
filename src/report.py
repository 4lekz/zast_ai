from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
import unicodedata


class ReportGenerator:
    """
    Klasa do generowania raportów ocen pracowniczych w formacie PDF.
    """

    def __init__(self, output_path="employee_evaluation_report.pdf"):
        """
        Inicjalizuje generator raportów.
        :param output_path: Ścieżka do pliku wyjściowego (domyślnie "employee_evaluation_report.pdf").
        """
        self.output_path = output_path

    @staticmethod
    def remove_accents(input_str):
        """
        Usuwa akcenty z tekstu, w tym polskie znaki.
        :param input_str: Tekst wejściowy.
        :return: Tekst bez akcentów.
        """
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return "".join(
            c if not unicodedata.combining(c) else ''
            for c in nfkd_form
        ).replace("ł", "l").replace("Ł", "L")

    @staticmethod
    def join_courses(param):
        """
        Łączy listę kursów w jeden string.
        :param param: Lista kursów lub nested list kursów.
        :return: Połączony string kursów lub "-"
        """
        if param == "-":
            return "-"
        elif isinstance(param, list) and all(isinstance(item, str) for item in param):
            return ";\n".join(param)
        elif isinstance(param, list) and all(isinstance(sublist, list) for sublist in param):
            return ";\n".join([";\n".join(sublist) for sublist in param])
        else:
            return "Invalid parameter"

    def write_section(self, c, title, content, y_position, line_width=500, font_size=12):
        """
        Pisze sekcję w PDF.
        :param c: Obiekt Canvas.
        :param title: Tytuł sekcji.
        :param content: Treść sekcji.
        :param y_position: Pozycja Y startowa.
        :param line_width: Maksymalna szerokość linii.
        :param font_size: Rozmiar czcionki.
        :return: Nowa pozycja Y po napisaniu sekcji.
        """
        line_height = font_size + 4  # Odstęp między liniami
        c.drawString(50, y_position, title)
        y_position -= 20

        lines = simpleSplit(content, "Helvetica", font_size, line_width)
        for line in lines:
            c.drawString(70, y_position, line)
            y_position -= line_height
        return y_position - 10

    def generate_pdf_report(self, achievements, areas_for_improvement, future_goals, smart_goals,
                            training_suggestions, team_collaboration_notes, courses_from_database):
        """
        Generuje raport w formacie PDF.
        """
        c = canvas.Canvas(self.output_path, pagesize=letter)
        c.setFont("Helvetica", 12)

        # Tytuł
        c.drawString(200, 750, "Raport Oceny Pracownika")
        c.line(50, 740, 550, 740)

        y_position = 720

        # Sekcje raportu
        y_position = self.write_section(c, "Osiagniecia:", self.remove_accents(achievements), y_position)
        y_position = self.write_section(c, "Obszary do poprawy:", self.remove_accents(areas_for_improvement), y_position)
        y_position = self.write_section(c, "Cele SMART:", self.remove_accents(smart_goals), y_position)
        y_position = self.write_section(c, "Propozycje szkolen:", self.remove_accents(training_suggestions), y_position)
        y_position = self.write_section(c, "Pasujace szkolenia w bazie:", self.remove_accents(courses_from_database), y_position)
        y_position = self.write_section(c, "Uwagi dotyczace wspolpracy:", self.remove_accents(team_collaboration_notes), y_position)
        # Zapisanie PDF
        c.save()
        print(f"Raport zapisano jako: {self.output_path}")

    def generate_and_save_report(self, report_dict):
        """
        Generuje raport na podstawie słownika z danymi.
        :param report_dict: Dane wejściowe do raportu.
        """
        # Wyciąganie danych z raportu
        achievements = report_dict.get("Osiągnięcia", "-")
        areas_for_improvement = report_dict.get("Obszary do poprawy", "-")
        future_goals = report_dict.get("Cele na przyszłość", "-")
        smart_goals = report_dict.get("Cele SMART", "-")
        training_suggestions = report_dict.get("Propozycje szkoleń", "-")
        team_collaboration_notes = report_dict.get("Uwagi dotyczące współpracy", "-")
        courses_from_database = self.join_courses(report_dict.get("dostępne szkolenia", "-"))

        # Sprawdzenie, czy raport ma dane
        if any(value != "-" for value in [achievements, areas_for_improvement, smart_goals, training_suggestions, courses_from_database, team_collaboration_notes]):
            print("Raport wygenerowany pomyślnie. Tworzenie PDF...")
            self.generate_pdf_report(
                achievements=achievements,
                areas_for_improvement=areas_for_improvement,
                future_goals=future_goals,
                smart_goals=smart_goals,
                training_suggestions=training_suggestions,
                team_collaboration_notes=team_collaboration_notes,
                courses_from_database=courses_from_database
            )
        else:
            print("Nie udało się wygenerować raportu. Brak danych.")
