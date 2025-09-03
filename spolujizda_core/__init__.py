from flask import Flask
from config import Config
# from .database import db
# from .auth.routes import auth_bp
# from .rides.routes import rides_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # db.init_app(app)

    # app.register_blueprint(auth_bp, url_prefix='/auth')
    # app.register_blueprint(rides_bp, url_prefix='/rides')

    # with app.app_context():
    #     db.create_all()

    @app.route('/')
    def index():
        return "Hello, World!"

    return app
