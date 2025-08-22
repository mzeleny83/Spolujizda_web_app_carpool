from flask import Blueprint, request, jsonify
from . import db
from .models import Book
from .schemas import BookSchema

api_bp = Blueprint('api', __name__)

book_schema = BookSchema()
books_schema = BookSchema(many=True)

@api_bp.route('/books', methods=['POST'])
def add_book():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    try:
        # Load data into a Book model instance
        book = book_schema.load(json_data)
        db.session.add(book)
        db.session.commit()
        return jsonify(book_schema.dump(book)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error creating book: {e}"}), 400

@api_bp.route('/books', methods=['GET'])
def get_books():
    all_books = Book.query.all()
    result = books_schema.dump(all_books)
    return jsonify(result)

@api_bp.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify(book_schema.dump(book))

@api_bp.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    try:
        # Load data, validating but updating existing book instance
        book = book_schema.load(json_data, instance=book, partial=True)
        db.session.commit()
        return jsonify(book_schema.dump(book))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error updating book: {e}"}), 400

@api_bp.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return '', 204