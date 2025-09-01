from spolujizda_core.models import User
from spolujizda_core.database import db
from werkzeug.security import generate_password_hash

def register_user(data):
    name = data.get('name')
    phone = data.get('phone')
    password = data.get('password')

    if not name or not phone or not password:
        raise Exception('Name, phone, and password are required')

    if User.query.filter_by(phone=phone).first():
        raise Exception('Phone number already registered')

    hashed_password = generate_password_hash(password)
    
    new_user = User(
        name=name,
        phone=phone,
        password_hash=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return new_user
