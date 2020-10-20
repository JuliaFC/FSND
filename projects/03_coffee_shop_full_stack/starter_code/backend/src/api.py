import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()


@app.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Origin',
        'http://127.0.0.1:8100')
    response.headers.add(
        'Access-Control-Allow-Headers',
        'Content-Type,Authorization')
    response.headers.add(
        'Access-Control-Allow-Methods',
        'GET,PUT,POST, PATCH, DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# ROUTES


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    if not drinks:
        abort(404)
    else:
        drinks = [d.long() for d in drinks]
    return jsonify({
        'success': True,
        'drinks': drinks
    })


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(token):
    drinks = Drink.query.all()
    drinks = [d.long() for d in drinks]
    return jsonify({
        'success': True,
        'drinks': drinks
    })


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(token):
    try:
        body = request.get_json()
        title = body.get('title')
        recipe = body.get('recipe')

        if (title is None) or (recipe is None):
            abort(422)

        new_drink = Drink(title=title, recipe=json.dumps(recipe))
        new_drink.insert()
        print(new_drink.id)

        all_drinks = Drink.query.all()
        drinks = [drink.long() for drink in all_drinks]
        drink = Drink.query.get(1)
        print(drink.long())

        return jsonify({
            "success": True,
            "drinks": drinks
            })
    except IndexError:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(token, drink_id):
    drink = Drink.query.get(drink_id)
    body = request.get_json()
    title = body.get('title')
    recipe = body.get('recipe')

    if not drink:
        abort(404)

    drink.name = title
    drink.recipe = json.dumps(recipe)
    drink.update()
    drink = drink.long()

    return jsonify({
        'success': True,
        'drinks': drink
    })


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(token, drink_id):
    drink = Drink.query.get(drink_id)
    if not drink or drink is None:
        abort(404)

    else:
        drink.delete()

    return jsonify({
        'success': True,
        'delete': drink_id
    })


# Error Handling
'''
Example error handling for unprocessable entity
'''


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


@app.errorhandler(AuthError)
def auth_error(error):
    response = jsonify(error.error)
    response.status_code = error.status_code
    return response
