import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/librarian"))
from constraints import constraint_adjustment, query_constraints


class ConstraintTests(unittest.TestCase):
    def test_multilingual_and_class_aliases(self):
        for phrase in ("rozhodovací strom", "decision tree", "drzewo decyzyjne", "DecisionTreeRegressor"):
            self.assertEqual(query_constraints(phrase)["algorithm"], {"decision_tree"})
        for phrase in ("logistická regrese", "LogisticRegression", "regresja logistyczna"):
            self.assertEqual(query_constraints(phrase)["algorithm"], {"logistic_regression"})
        self.assertEqual(query_constraints("recenzji filmowych TF-IDF")["dataset"], {"imdb"})

    def test_exact_exercise_beats_wrong_algorithm_or_dataset(self):
        wanted = query_constraints("decision tree diamonds")
        exact = {"text": "", "source_path": "diamonds_decision_tree.ipynb"}
        wrong_algo = {"text": "XGBoost diamonds", "source_path": "xgboost_diamonds.py"}
        wrong_data = {"text": "DecisionTreeRegressor concrete", "source_path": "concrete_decision_tree.py"}
        grade = lambda doc: constraint_adjustment(doc, wanted)[0]
        self.assertGreater(grade(exact), grade(wrong_algo))
        self.assertGreater(grade(exact), grade(wrong_data))

    def test_missing_labels_neutral_and_comparisons_supported(self):
        self.assertEqual(constraint_adjustment({"text": "general explanation"}, query_constraints("DBSCAN"))[0], 0)
        wanted = query_constraints("Compare TF-IDF and Bag of Words")
        for text in ("TF-IDF", "CountVectorizer"):
            self.assertGreater(constraint_adjustment({"text": text}, wanted)[0], 0)
        # Do not match short aliases inside unrelated words.
        self.assertFalse(query_constraints("bowling and showcase")["algorithm"])

    def test_incidental_mentions_and_catalogues_do_not_beat_exact_task(self):
        wanted = query_constraints("decision tree diamonds")
        incidental = {"source_path": "random_forest_diamonds.py", "text": "A decision tree leaf in a random forest predicts diamond prices."}
        self.assertLess(constraint_adjustment(incidental, wanted, exact_task=True)[0], 0)
        focused = {"text": "LogisticRegression lumbar"}
        catalogue = {"text": "LogisticRegression lumbar DecisionTreeRegressor diabetes Ridge concrete"}
        wanted = query_constraints("logistic regression lumbar")
        self.assertGreater(constraint_adjustment(focused, wanted, exact_task=True)[0], constraint_adjustment(catalogue, wanted, exact_task=True)[0])
        # A correct conceptual passage must remain usable despite its file name.
        passage = {"source_path": "kmeans_theory.py", "text": "DBSCAN core and border points"}
        self.assertGreater(constraint_adjustment(passage, query_constraints("DBSCAN"))[0], 0)

    def test_vectorizer_with_classifier_is_not_a_conflict(self):
        wanted = query_constraints("TF-IDF movie reviews")
        task = {"source_path": "tfidf_exercise.ipynb", "text": "IMDb TF-IDF with LogisticRegression and LinearSVC"}
        self.assertAlmostEqual(constraint_adjustment(task, wanted, exact_task=True)[0], 0.06)
        wrong = {"source_path": "bow_tfidf_theory.py", "text": "Movie review classification using CountVectorizer"}
        self.assertLess(constraint_adjustment(wrong, wanted, exact_task=True)[0], constraint_adjustment(task, wanted, exact_task=True)[0])


if __name__ == "__main__":
    unittest.main()
