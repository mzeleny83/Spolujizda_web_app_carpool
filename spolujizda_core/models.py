from .database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    rating = db.Column(db.Float, default=5.0)
    total_rides = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.name}>'

class Ride(db.Model):
    __tablename__ = 'rides'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_location = db.Column(db.String, nullable=False)
    to_location = db.Column(db.String, nullable=False)
    departure_time = db.Column(db.String, nullable=False)
    available_seats = db.Column(db.Integer)
    price_per_person = db.Column(db.Integer)
    route_waypoints = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('rides', lazy=True))

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seats_reserved = db.Column(db.Integer, default=1)
    status = db.Column(db.String, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ride = db.relationship('Ride', backref=db.backref('reservations', lazy=True))
    passenger = db.relationship('User', backref=db.backref('reservations', lazy=True))

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ride = db.relationship('Ride', backref=db.backref('messages', lazy=True))
    sender = db.relationship('User', backref=db.backref('sent_messages', lazy=True))

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rated_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ride = db.relationship('Ride', backref=db.backref('ratings', lazy=True))
    rater = db.relationship('User', foreign_keys=[rater_id], backref=db.backref('given_ratings', lazy=True))
    rated = db.relationship('User', foreign_keys=[rated_id], backref=db.backref('received_ratings', lazy=True))

class BlockedUser(db.Model):
    __tablename__ = 'blocked_users'
    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    blocker = db.relationship('User', foreign_keys=[blocker_id], backref=db.backref('blocked_users_list', lazy=True))
    blocked = db.relationship('User', foreign_keys=[blocked_id], backref=db.backref('blocked_by_list', lazy=True))

class RecurringRide(db.Model):
    __tablename__ = 'recurring_rides'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_location = db.Column(db.String, nullable=False)
    to_location = db.Column(db.String, nullable=False)
    departure_time = db.Column(db.String, nullable=False)
    days_of_week = db.Column(db.String, nullable=False)
    available_seats = db.Column(db.Integer)
    price_per_person = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('recurring_rides', lazy=True))

class UserStats(db.Model):
    __tablename__ = 'user_stats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    total_rides = db.Column(db.Integer, default=0)
    total_distance = db.Column(db.Float, default=0)
    co2_saved = db.Column(db.Float, default=0)
    money_saved = db.Column(db.Float, default=0)
    user = db.relationship('User', backref=db.backref('stats', uselist=False))

class SmsCode(db.Model):
    __tablename__ = 'sms_codes'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String, nullable=False)
    code = db.Column(db.String, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)