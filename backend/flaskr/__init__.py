import json
import os
from unicodedata import category
from flask import Flask, request, abort, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import traceback

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
    Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    Use the after_request decorator to set Access-Control-Allow
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
    Create an endpoint to handle GET requests
    for all available categories.
    """
    # @app.route('/')
    # def index():
    #     return redirect(url_for("get_categories"))

    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        if categories is None:
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

        return jsonify({
            "success": True,
            "questions": current_questions,
            "totalQuestions": len(selection),
            "categories": category_items,
            "currentCategory": None
        })

    """
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
                abort(422)
            
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
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    """
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

        new_question = body.get("question")
        new_answer = body.get("answer")
        new_difficulty = body.get("difficulty")
        new_category = body.get("category")
        search_term = body.get("searchTerm")

        try:
            if search_term:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike(f"%{search_term}%")
                ).all()

                current_questions = paginate_questions(request, selection)

                return jsonify({
                    "success": True,
                    "questions": current_questions,
                    "totalQuestions": len(selection),
                    "currentCategory": None
                })
            else:
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
                    "currentCategory": question.category
                })

        except:
            abort(422)


    """
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def get_category_questions(category_id):
        selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all()

        if len(selection) == 0:
            abort(404)
            
        current_questions = paginate_questions(request, selection)

        current_category = Category.query.filter(Category.id == category_id).one()
        current_category_type = current_category.format()["type"]

        return jsonify({
            "success": True,
            "questions": current_questions,
            "totalQuestions": len(selection),
            "currentCategory": current_category_type
        })


    """
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def start_quiz():
        try:
            body = request.get_json()
            previous_questions_id = body.get("previous_questions")
            quiz_category = body.get("quiz_category")
            
            # get the corresponding category id for the quiz category given
            category_id = quiz_category["id"]

            if category_id == 0:
                questions = Question.query.filter(Question.id.notin_(previous_questions_id)).all()
            else:
                questions = Question.query.filter(Question.id.notin_(previous_questions_id), Question.category == category_id).all()

            selected_question = None
            if(questions):
                selected_question = random.choice(questions)

            return jsonify({
                "success": True,
                "question": selected_question.format()
                #, "previousQuestions": previous_questions_id
            })

        except:
            abort(422)




    """
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
    
    @app.errorhandler(405)
    def not_allowed(error):
        return(
            jsonify({
                "success": False,
                "error": 405,
                "message": 'method not allowed'
                }), 405)
                
    @app.errorhandler(422)
    def unprocessable(error):
        return (jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422)

    return app
