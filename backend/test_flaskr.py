import os

import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from decouple import config

from flaskr import create_app
from models import setup_db, Question, Category



DATABASE_NAME = config('DATABASE_NAME')
DATABASE_USER = config('DATABASE_USER')
DATABASE_PASSWORD = config('DATABASE_PASSWORD')

class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.new_question = {"question": "Test question", "answer": "Test answer", "category": 1, "difficulty": 1}
        self.quiz_test = {"previous_questions": [1, 4 ,20 ,15], "quiz_category": 1}

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_paginated_questions_from_index(self):
        res = self.client().get("/")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(len(data["questions"]))

    def test_404_sent_requesting_beyond_valid_page_from_index(self):
        res = self.client().get("/?page=1000", json={"difficulty": 1})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")


    def test_get_paginated_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(len(data["questions"]))

    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get("/questions?page=1000", json={"difficulty": 1})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_get_question_search_with_results(self):
        res = self.client().post("/questions", json={"searchTerm": "How"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["totalQuestions"])
        self.assertEqual(len(data["questions"]), 1)

    def test_get_question_search_without_results(self):
        res = self.client().post("/questions", json={"searchTerm": "abcdefghij"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["totalQuestions"], 0)
        self.assertEqual(len(data["questions"]), 0)

    def test_create_new_question(self):
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)

    def test_422_if_question_creation_fails(self):
        res = self.client().post("/questions", json={})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)

    def test_update_question_difficulty(self):
        res = self.client().patch("/questions/5", json={"difficulty": 1})
        data = json.loads(res.data)
        question = Question.query.filter(Question.id == 5).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(question.format()["difficulty"], 1)

    def test_400_for_failed_update(self):
        res = self.client().patch("/questions/5")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "bad request")

    def test_delete_question(self):
        res = self.client().delete('/questions/10')
        data = json.loads(res.data)

        question = Question.query.filter(Question.id == 10).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], 10)
        self.assertTrue(data['totalQuestions'])
        self.assertTrue(len(data['questions']))
        self.assertEqual(question, None)

    def test_404_if_questions_does_not_exist(self):
        res = self.client().delete("/questions/1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")

    def test_get_quiz_by_category(self):
        res = self.client().post("/quizzes", json=self.quiz_test)
        data = json.loads(res.data)
        question = data["question"]

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(question["category"], 1)

    def test_404_if_quiz_does_not_exist(self):
        res = self.client().post("/quizzes", json={"previous_questions":[], "quiz_category":0})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "bad request")

    
# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()