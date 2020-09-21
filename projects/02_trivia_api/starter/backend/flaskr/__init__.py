import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET, POST, PATCH, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add(
            'Access-Control-Allow-Origin',
            'http://localhost:3000')
        return response

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        categories = [{'id': c.id, 'type': c.type} for c in categories]

        return jsonify({
            'success': True,
            'categories': categories
        })

    @app.route('/questions', methods=['GET'])
    @app.route('/list', methods=['GET'])
    def get_questions():
        page = request.args.get('page', 1, type=int)
        paginated_questions = Question.query.paginate(
            page, QUESTIONS_PER_PAGE, False)

        questions = [question.format()
                     for question in paginated_questions.items]
        total_questions = len(Question.query.all())
        available_categories = Category.query.all()
        categories = []

        for category in available_categories:
            categories.append(category.type)
        return jsonify({
            'success': True,
            'questions': questions,
            'totalQuestions': total_questions,
            'categories': categories,
            'currentCategory': None,
        })

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        page = request.args.get('page', 1, type=int)
        try:
            paginated_questions = Question.query.filter(
                Question.category == category_id +
                1).paginate(
                page,
                QUESTIONS_PER_PAGE,
                False)
        except:
            abort(404)

        questions = [question.format()
                     for question in paginated_questions.items]
        total_questions = len(questions)

        return jsonify({
            'success': True,
            'questions': questions,
            'totalQuestions': total_questions,
            'currentCategory': category_id,
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        success = True
        try:
            question = Question.query.get(question_id)
            question.delete()
        except:
            abort(404)
        finally:
            return jsonify({
                'success': success
            })

    @app.route('/questions/add', methods=['POST'])
    def add_question():
        try:
            question = request.get_json().get('question')
            answer = request.get_json().get('answer')
            difficulty = request.get_json().get('difficulty')
            category = request.get_json().get('category')
            new_question = Question(
                question=question,
                answer=answer,
                difficulty=difficulty,
                category=category)
            new_question.insert()
        except:
            abort(500)

        return jsonify({
            'success': True,
        })

    @app.route('/questions/search', methods=['POST'])
    def search_question():
        search_term = request.get_json().get('searchTerm')
        try:
            res = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()
            questions = [question.format() for question in res]
            total_questions = len(questions)
        except:
            abort(400)

        return jsonify({
            'success': True,
            'questions': questions,
            'totalQuestions': total_questions,
            'currentCategory': questions[0]['category']
        })

    '''
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': error.code,
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': error.code,
        }), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'success': False,
            'error': error.code,
        }), 422

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': error.code,
        }), 500

    return app
