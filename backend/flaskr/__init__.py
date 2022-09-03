import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate(request, questions):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in questions]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add("Access-Control-Allow-Methods",
                             "GET, PUT, POST, PATCH, DELETE, OPTION")
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/')
    def index():
        return jsonify({
            'message': 'Home page'
        })

    @app.route('/categories')
    def read_category():
        try:
            categories = Category.query.order_by(Category.type).all()
            available_categories = {}
            for category in categories:
                available_categories[category.id] = category.type

            return jsonify({
                "success": True,
                "categories": available_categories
            })
        except:
            abort(404)

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
    def read_questions():
        categories = Category.query.all()
        question = Question.query.all()
        current_question = paginate(request, question)
        available_categories = {}
        for category in categories:
            available_categories[category.id] = category.type

        if len(current_question) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "questions": current_question,
            "total_questions": len(question),
            "categories": available_categories,
            "current_category": None
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
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            if question is None:
                abort(400)

            question.delete()
            all_question = Question.query.order_by(Question.id).all()
            current_questions = paginate(request, all_question)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                "total_question": len(all_question)
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

    @app.route('/questions', methods=['POST'])
    def post_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        search = body.get('search')

        if (new_question is None) or (new_answer is None) or (new_difficulty is None) or (new_category is None):
            abort(422)

        try:
            if search:
                questions = Question.query.filter(
                    Question.question.ilike(f'%{search}%'))
                current_questions = paginate(request, questions)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                })
            else:
                question = Question(question=new_question, answer=new_answer, category=new_category,
                                    difficulty=new_difficulty)
                question.insert()
                questions = Question.query.order_by(Question.id).all()
                current_questions = paginate(request, questions)
                return jsonify({
                    "success": True,
                    "created": question.id,
                    "questions": current_questions,
                    "total_questions": len(questions)
                })
        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        searchTerm = body.get("searchTerm", None)

        try:
            questions = Question.query.filter(
                Question.question.ilike(f'%{searchTerm}%')).all()
            current_questions = paginate(request, questions)
            category = Category.query.order_by(Category.id).all()

            if (len(questions) == 0) or not category:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(Question.query.all()),
                'current_category': category[0].format()['type']
            })
        except:
            abort(404)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions')
    def categorise_question(category_id):
        try:
            category = Category.query.get(category_id)
            questions = Question.query.filter(Question.category == category.id)
            paginate_question = [question.format() for question in questions]
            return jsonify({
                'success': True,
                'questions': paginate_question,
                'total_questions': len(paginate_question),
                'current_category': category.type
            })
        except:
            abort(422)

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
    def play_quiz():
        try:
            data = request.get_json()
            previous_questions = data.get('previous_questions')
            quiz_category = data.get('quiz_category')
            questions = None

            if quiz_category['type'] == 'click':
                questions = Question.query.all()
            else:
                questions = Question.query.filter_by(category=quiz_category['id']).all()
            
            formatted_questions = [question.format() for question in questions]

            possible_questions = []

            for question in formatted_questions:
                if question['id'] not in previous_questions:
                    possible_questions.append(question)
                
            selected_question = None
            if len(possible_questions) > 0:
                selected_question = random.choice(possible_questions)
            
            return jsonify({
                'success': True,
                'question': selected_question
            })
        
        except:
            abort(400)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                "success": False,
                "error": 404,
                "message": 'Resource not found'
            }), 404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({
                "success": False,
                "error": 422,
                "message": "unprocessable"
            }), 422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify({
                "success": False,
                "error": 400,
                "message": "bad request",
            }), 400,
        )

    @app.errorhandler
    def internal_server(error):
        return (
            jsonify({
                "success": False,
                "error": 500,
                "message": "Internal server error"
            }), 500,
        )

    @app.errorhandler
    def not_allowed_method():
        return (
            jsonify({
                'success': False,
                'error': 405,
                'message': 'Method not allowd',
            }), 405,
        )

    return app
