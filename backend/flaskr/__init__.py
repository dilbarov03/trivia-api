import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)

  @app.after_request
  def after_request(response):
    response.headers.add (
      "Access-Control-Allow-Headers", "Content-Type, Authorization, true"
      )
    response.headers.add (
      "Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS"
      )

    return response

  
  @app.route("/categories")
  def get_categories():
    all_categories = Category.query.order_by(Category.id).all()
    cats = [i.format() for i in all_categories]   

    if len(all_categories)==0:
      abort(404)  
    
    return jsonify({
        'success': True,
        'categories': {a['id']:a['type'] for a in cats} 
      })

  @app.route("/questions")
  def get_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    all_categories = Category.query.order_by(Category.id).all()

    if len(current_questions) == 0:
        abort(404)

    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(selection),
        'categories': {a.id: a.type for a in all_categories},
        'current_category': None
    })

  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_by_category(category_id):
    selection = Question.query.filter(Question.category == category_id).order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    all_categories = Category.query.order_by(Category.id).all()

    if len(current_questions) == 0:
        abort(404)
    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(selection),
      'current_category': category_id
      })
  
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_questions(question_id):
    try:
      question = Question.query.get(question_id)
      question.delete()

      return jsonify({
        'success': True,
        'deleted': question_id
        })
    except:
      abort(422)

  @app.route('/questions', methods=['POST'])
  def add_or_search_question():
    body = request.get_json()

    # if search term is present
    if (body.get('searchTerm')):
        search_term = body.get('searchTerm')
        selection = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()

        # 404 if no results found
        if (len(selection) == 0):
            abort(404)

        paginated = paginate_questions(request, selection)
        return jsonify({
            'success': True,
            'questions': paginated,
            'total_questions': len(Question.query.all())
        })

    # if no search term, create new question
    else:
        new_question = body.get('question')
        new_answer = body.get('answer')
        new_difficulty = body.get('difficulty')
        new_category = body.get('category')

        if ((new_question is None) or (new_answer is None)
                or (new_difficulty is None) or (new_category is None)):
            abort(422)

        try:
            question = Question(question=new_question, answer=new_answer,
                                difficulty=new_difficulty, category=new_category)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'question_created': question.question,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    try:
      body = request.get_json()

      if not ('quiz_category' in body and 'previous_questions' in body):
          abort(422)

      category = body.get('quiz_category')
      previous_questions = body.get('previous_questions')

      if category['type'] == 'click':
          available_questions = Question.query.filter(
              Question.id.notin_((previous_questions))).all()
      else:
          available_questions = Question.query.filter_by(
              category=category['id']).filter(Question.id.notin_((previous_questions))).all()

      new_question = available_questions[random.randrange(
          0, len(available_questions))].format() if len(available_questions) > 0 else None

      return jsonify({
          'success': True,
          'question': new_question
      })
    except:
      abort(422)

  @app.errorhandler(404)
  def not_found(error):
      return (
          jsonify({"success": False, "error": 404, "message": "resource not found"}),
          404,
      )

  @app.errorhandler(422)
  def unprocessable(error):
      return (
          jsonify({"success": False, "error": 422, "message": "unprocessable"}),
          422,
      )

  
  return app   