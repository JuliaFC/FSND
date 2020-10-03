import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from random import randrange

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

    def get_paginated_questions(page, category_id=None):
        if category_id is not None:
            paginated_questions = Question.query.filter(
                Question.category == category_id +
                1).paginate(
                page,
                QUESTIONS_PER_PAGE,
                False)
        else:
            paginated_questions = Question.query.paginate(
                page, QUESTIONS_PER_PAGE, False)
        questions = [question.format()
                     for question in paginated_questions.items]
        return questions

    @app.route('/categories', methods=['GET'])
    def get_categories():

        categories = Category.query.all()
        categories = [{'id': c.id, 'type': c.type} for c in categories]
        if not categories:
            abort(404)
        return jsonify({
            'success': True,
            'categories': categories
        })

    @app.route('/questions', methods=['GET'])
    @app.route('/list', methods=['GET'])
    def get_questions():

        page = request.args.get('page', 1, type=int)
        questions = get_paginated_questions(page)
        if not questions:
            abort(404)

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
        })

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        page = request.args.get('page', 1, type=int)
        questions = get_paginated_questions(page, category_id)

        if not questions:
            abort(404)

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

        question = Question.query.get(question_id)
        if question is None:
            abort(404)

        question.delete()
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
        except BaseException:
            abort(500)

        return jsonify({
            'success': True,
        })

    @app.route('/questions/search', methods=['POST'])
    def search_question():
        search_term = request.get_json().get('searchTerm')
        results = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()
        questions = [question.format() for question in results]
        total_questions = len(questions)
        if not questions:
            abort(400)

        return jsonify({
            'success': True,
            'questions': questions,
            'totalQuestions': total_questions,
            'currentCategory': questions[0]['category'] if total_questions > 0 else 0
        })

    @app.route('/quizzes', methods=['POST'])
    def play():
        previous_questions = request.get_json().get('previous_questions')
        quiz_category = request.get_json().get('quiz_category')

        # This conditional handles when the "ALL" category is picked
        if int(quiz_category['id']) == -1:
            results = Question.query.all()
        else:
            current_category = (int(quiz_category['id']) + 1)
            results = Question.query.filter(
                Question.category == current_category).all()
        if not results:
            abort(404)
        all_questions = [r.id for r in results]
        possible_questions = list(
            set(all_questions) - set(previous_questions))
        possible_questions_length = len(possible_questions)

        next_question_index = 0 if possible_questions_length == 0 else randrange(
            possible_questions_length)
        next_question = None
        if possible_questions_length > 0:
            for r in results:
                if r.id == possible_questions[next_question_index]:
                    next_question = r.format()
                    continue

        return jsonify({
            'success': True,
            'question': next_question
        })

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable entity"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal server error"
        }), 500

    return app
