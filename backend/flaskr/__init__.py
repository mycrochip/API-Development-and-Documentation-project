import json
import os
from flask import Flask, request, abort, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        response.headers.add(
            "Access-Control-Allow-Origin", "*"
        )
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/')
    def index():
        return redirect(url_for("get_categories"))

    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        if len(categories) == 0:
            abort(404)
        items = {}
        for category in categories:
            data = category.format()
            items[data["id"]] = data["type"]
        
        return jsonify({
            "success": True,
            "categories": items,
            "total_categories": len(categories)
            })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.order_by(Category.id).all()
        category_items = {}
        for category in categories:
            data = category.format()
            category_items[data["id"]] = data["type"]
        
        # Implement current_category - How?
        current_category = "All"

        return jsonify({
            "success": True,
            "questions": current_questions,
            "totalQuestions": len(selection),
            "categories": category_items,
            "currentCategory": current_category
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
            all_questions = Question.query.all()

            if question is None:
                abort(404)
            
            question.delete()
            # Modify the front end to remove the display of question with id == question_id
            return jsonify({
                "success": True,
                "deleted": question_id,
                "totalQuestions": len(all_questions)
            })
        except:
            abort(422)


    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions', methods=['POST'])
    def add_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_difficulty = body.get("difficulty", None)
        new_category = body.get("category", None)
        search_term = body.get("searchTerm", None)

        try:
            if search_term:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike(f"%{search_term}%")
                ).all()

                current_questions = paginate_questions(request, selection)
                # Implement correct current_category
                if len(current_questions) == 0:
                    abort(404)

                return jsonify({
                    "success": True,
                    "questions": current_questions,
                    "totalQuestions": len(selection),
                    "currentCategory": "None"
                })
            
            if not (new_question and new_answer and new_difficulty and new_category):
                abort(422)

            question = Question(
                question=new_question,
                answer=new_answer,
                difficulty=new_difficulty,
                category=new_category
                )

            question.insert()

            return jsonify({
                "success": True,
                "questions": [question.format()],
                "totalQuestions": len(Question.query.all()),
                "currentCategory": "All"
            })
        except:
            abort(422)


    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def get_category_questions(category_id):
        selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)
            
        current_category = Category.query.filter(Category.id == category_id).one()
        current_category_type = current_category.format()["type"]

        return jsonify({
            "success": True,
            "questions": current_questions,
            "totalQuestions": len(selection),
            "currentCategory": current_category_type
        })


    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def get_quiz():
        body = request.get_json()

        try:
            previous_questions_id = body.get("previous_questions", "", type=list)
            quiz_category = body.get("quiz_category", "All")
            
            # get the corresponding category id for the quiz category given
            category_id = quiz_category.id

            category_questions = Question.query.filter(Question.category == category_id).all()
            # Select a question that has not being asked from this category
            selected_question = {} # Empty question at first
            flag = previous_questions_id < len(category_questions)
            while flag:
                valid_random_index = random.randint(0, len(category_questions))
                selected_question = category_questions[valid_random_index]
                selected_question_id = selected_question.id
                if selected_question_id in previous_questions_id:
                    continue
                selected_question = selected_question.format()
                break

            if previous_questions_id == len(category_questions) - 1:
                previous_questions_id = []
            else:
                previous_questions_id.append(selected_question_id)

            return jsonify({
                "success": True,
                "question": selected_question,
                "previous_questions": previous_questions_id
            })
    
        except:
            abort(422)




    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def bad_request(error):
        return (jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400)
    
    @app.errorhandler(404)
    def not_found(error):
        return (jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404)

    @app.errorhandler(422)
    def unprocessable(error):
        return (jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422)

    return app

