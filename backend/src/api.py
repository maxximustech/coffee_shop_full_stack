import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
db_drop_and_create_all()


# ROUTES

@app.route('/drinks', methods=['GET'])
def get_all_drinks():
    try:
        drinks = Drink.query.all()
        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in drinks]
        }), 200
    except exc.SQLAlchemyError:
        abort(422)


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink_details(token):
    try:
        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in Drink.query.all()]
        }), 200
    except exc.SQLAlchemyError:
        abort(422)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_new_drink(token):
    try:
        jsonBody = request.get_json()
        if 'title' and 'recipe' not in jsonBody:
            abort(400)
        drinkTitle = jsonBody['title']
        drinkRecipe = json.dumps(jsonBody['recipe'])
        new_drink = Drink(title=drinkTitle, recipe=drinkRecipe)
        new_drink.insert()
        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        }), 200
    except exc.SQLAlchemyError:
        abort(422)


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(token, id):
    try:
        getDrink = Drink.query.filter(Drink.id == id).one_or_none()
        if getDrink is None:
            abort(404)
        drinkData = request.get_json()
        if 'title' and 'recipe' not in drinkData:
            abort(400)
        if 'title' in drinkData:
            getDrink.title = drinkData['title']
        if 'recipe' in drinkData:
            getDrink.recipe = json.dumps(drinkData['recipe'])
        getDrink.update()
        return jsonify({
            'success': True,
            'drinks': [getDrink.long()]
        }), 200
    except exc.SQLAlchemyError:
        abort(422)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(token, id):
    try:
        getDrink = Drink.query.filter(Drink.id == id).one_or_none()
        if getDrink is None:
            abort(404)
        getDrink.delete()
        return jsonify({
            'success': True,
            'delete': id
        }), 200
    except exc.SQLAlchemyError:
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource could not be found"
    }), 404


@app.errorhandler(401)
def not_authorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "You are not authorized to perform this action"
    }), 401


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad request"
    }), 400


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error
    }), error.status_code
