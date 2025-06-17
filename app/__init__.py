from flask import Flask
from flask_login import LoginManager
from flask_session import Session
from .models import User

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        print(f"Loading user with ID: {user_id}")
        return User.get(user_id)

    # Initialize Flask-Session
    Session(app)

    # Register blueprints
    from .routes import main
    app.register_blueprint(main)

    return app