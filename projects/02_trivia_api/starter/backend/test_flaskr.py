import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format(
            'postgres:1234@localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.test_question = {
            'question': 'Which Star Wars movie is the best?',
            'category': 3,
            'answer': 'The Last Jedi',
            'difficulty': 1
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertTrue(len(data['categories']))

    def test_add_question(self):
        res = self.client().post('/questions/add', json=self.test_question)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_get_question(self):
        res = self.client().get('/questions?page=1')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])

    def test_get_question_not_found(self):
        res = self.client().get('/questions?page=100')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)

    def test_delete_question(self):
        question = Question.query.first()
        question_id = question.id
        res = self.client().delete('/questions/' + str(question_id))
        data = json.loads(res.data)
        question = Question.query.get(question_id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertFalse(question)

    def test_delete_question_not_found(self):
        question_id = 1000
        res = self.client().delete('/questions/' + str(question_id))
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)

    def test_search_question(self):
        res = self.client().post(
            '/questions/search',
            json={
                'searchTerm': 'Star Wars'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        self.assertTrue(data['questions'])
        self.assertTrue(len(data['questions']))

        self.assertTrue(data['totalQuestions'])
        self.assertTrue(data['currentCategory'])

    def test_search_question_not_found(self):
        res = self.client().post(
            '/questions/search',
            json={
                'searchTerm': 'Star Trek'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        self.assertFalse(data['questions'])
        self.assertFalse(len(data['questions']))

        self.assertFalse(data['totalQuestions'])
        self.assertFalse(data['currentCategory'])


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
