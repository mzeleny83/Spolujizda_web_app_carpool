from . import db

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=True, nullable=False)
    author = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'