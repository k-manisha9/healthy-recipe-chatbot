import os
from flask import Blueprint, request, redirect, url_for, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pinecone import Pinecone
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask Login
login_manager = LoginManager()
login_manager.login_view = "auth.login"

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("bot1")  # Correct way to connect

auth_bp = Blueprint("auth", __name__)

# Define User Class
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_exists(user_id):
        return User(user_id)
    return None

# Function to check if user exists in Pinecone
def user_exists(user_id):
    try:
        result = index.fetch([user_id])
        return bool(result.vectors)  # Check if vectors exist
    except Exception as e:
        print(f"Error checking user: {e}")
        return False

# **Register New User**
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.form
    user_id = data.get("user_id")
    password = data.get("password")

    if user_exists(user_id):
        return redirect(url_for("auth.login"))  # Redirect if user exists

    # Store user details in Pinecone
    user_vector = {
        "id": user_id,
        "values": [0.0] * 384,  # Placeholder vector
        "metadata": {"password": generate_password_hash(password)}  # Store hashed password
    }
    
    index.upsert([user_vector])
    return redirect(url_for("auth.login"))  # Redirect to login

# **User Login**
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.form
    user_id = data.get("user_id")
    password = data.get("password")

    # Fetch user data from Pinecone
    result = index.fetch([user_id])
    user_data = result.vectors.get(user_id)

    if user_data:
        stored_password = user_data.metadata.get("password")
        if stored_password and check_password_hash(stored_password, password):
            user = User(user_id)
            login_user(user)  # Login the user
            session["user_id"] = user_id  # Store in session
            return jsonify({"message": "Login successful!"})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"error": "User not found"}), 404

# **User Logout**
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully!"})

# **Protected Route Example**
@auth_bp.route("/protected")
@login_required
def protected():
    return jsonify({"message": f"Hello, {current_user.id}. You are logged in!"})
