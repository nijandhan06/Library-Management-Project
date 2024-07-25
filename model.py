from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db=SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_librarian = db.Column(db.Boolean,default=False, nullable=False)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(100), nullable=False, unique=True)
    date_created=db.Column(db.DateTime, default=datetime.now(), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    books = db.relationship('Book', backref='section', lazy=True)
    user=db.relationship('User', backref='section', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    title = db.Column(db.String(100), nullable=False, unique=True)
    author = db.Column(db.String(100), nullable=False)
    content=db.Column(db.String, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    date_issued=db.Column(db.DateTime, default=datetime.now(), nullable=False)
    date_return=db.Column(db.DateTime, nullable=False)

class BookRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    date_requested=db.Column(db.DateTime, default=datetime.now(), nullable=False)
    date_return=db.Column(db.DateTime, nullable=False)
    status=db.Column(db.String, nullable=False)
    user=db.relationship('User', backref='bookrequest', lazy=True)
    book=db.relationship('Book', backref='bookrequest', lazy=True)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.String, nullable=False)
    user=db.relationship('User', backref='rating', lazy=True)
    book=db.relationship('Book', backref='rating', lazy=True)

    