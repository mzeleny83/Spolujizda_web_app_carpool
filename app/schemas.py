from . import ma, db
from .models import Book

class BookSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Book
        load_instance = True
        sqla_session = db.session