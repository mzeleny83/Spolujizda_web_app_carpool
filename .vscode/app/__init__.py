import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.Config')

    # Ensure the instance folder exists for SQLite DB
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    ma.init_app(app)

    import click
    @app.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables."""
        db.create_all()
        click.echo("Initialized the database.")

    # Register blueprints (API routes)
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app