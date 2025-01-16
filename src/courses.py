from scipy.spatial.distance import cosine
import pandas as pd
from src.openai_utils import OpenAIClient
from src.data import course_list

class CourseManager:
    def __init__(self, openai_client):
        """
        Initializes the CourseManager with a list of courses and an OpenAI client.
        """
        self.course_list = course_list
        self.openai_client = openai_client
        self.course_df = self._create_course_dataframe()

    def _create_course_dataframe(self):
        """
        Creates a DataFrame with courses and their embeddings.
        """
        embeddings = [self.openai_client.generate_embedding(course) for course in self.course_list]
        return pd.DataFrame({"Text": self.course_list, "Vector": embeddings})

    # def get_embedding(self, text):
    #     """
    #     Generates an embedding for the given text using OpenAI.
    #     :param text: Text to generate an embedding for.
    #     :return: Embedding vector.
    #     """
    #     text = text.replace("\n", " ")
    #     return self.client.embeddings.create(input=[text], model=self.embedding_model).data[0].embedding

    def find_best_matches(self, query, top_n=3, similarity_threshold=0.85):
        """
        Finds the best matching courses based on cosine similarity.
        :param query: Text query.
        :param top_n: Maximum number of results to return.
        :param similarity_threshold: Minimum cosine similarity threshold.
        :return: List of best matching course descriptions.
        """
        query_vector = self.openai_client.generate_embedding(query)
        if query_vector is None:
            print("Failed to generate embedding for the query.")
            return []
        self.course_df["Cosine_Similarity"] = self.course_df["Vector"].apply(
            lambda x: 1 - cosine(query_vector, x)
        )
        filtered_results = self.course_df[self.course_df["Cosine_Similarity"] >= similarity_threshold]
        top_matches = filtered_results.nlargest(top_n, "Cosine_Similarity")
        return top_matches["Text"].tolist()
    
    def get_courses_for_worker(self, json_data, top_n=3, similarity_threshold=0.85):
        """
        Znajduje dostępne szkolenia dla pracownika na podstawie podanych propozycji szkoleń.
        :param json_data: Dane wejściowe w formacie JSON.
        :param top_n: Maksymalna liczba wyników do zwrócenia dla każdej propozycji.
        :param similarity_threshold: Minimalny próg podobieństwa kosinusowego.
        :return: Lista dopasowanych szkoleń i pełna lista kursów.
        """
        if json_data.get("Propozycje szkoleń", "-") not in ["-", ""]:
            updated_proposals = []
            full_list_of_courses = []
            for query in json_data["Propozycje szkoleń"]:
                if query:
                    # print(f"Zapytanie: {query}")
                    matches = self.find_best_matches(query, top_n, similarity_threshold)
                    full_list_of_courses.append(matches)
                    updated_proposals.append({
                        "Poszukiwane": query,
                        "dostępne szkolenia": matches
                    })
            return updated_proposals, full_list_of_courses
        else:
            print("Brak propozycji szkoleń w JSON-ie.")
            return [], []