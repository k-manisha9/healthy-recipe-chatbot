from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import requests
import os
from flask import render_template
from flask_login import login_user, logout_user, current_user
# from .utils import get_recipes_by_ingredients,get_recommendations
from .recipe_utils import chatbot_response
from werkzeug.security import check_password_hash
from .vector_db.bot import fetch_user_from_pinecone, save_user_to_pinecone, index1
from flask_login import UserMixin, login_user, logout_user
from datetime import datetime
from .vector_db.history import save_chat_to_pinecone, load_chat_history  # NEW
import uuid
from .fitness_diet_plan import generate_diet_plan_disease
from .diet_chart_without_disease import get_diet_chart
from .vector_db.embeddings import embed_text



SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')
main = Blueprint('main', __name__)
print(f"App initialized with UUID: {uuid.uuid4()}")

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@main.route('/')
def home():
    print(f"Is the user authenticated? {current_user.is_authenticated}")
    print(f"🕤 Debug: Current user ID: {getattr(current_user, 'id', 'None')}") 
    if current_user.is_authenticated:
        return render_template('index.html', current_user=current_user)
    else:
        return render_template('index.html', current_user=None)

# @main.route('/recipes', methods=['GET'])
# def get_recipes():
#     ingredients = request.args.get('ingredients')
#     user_id = session.get('user_id')
#     if user_id:
#         recipes = get_recommendations(user_id, ingredients)

#         if not recipes:
#            recipes = get_recipes_by_ingredients(ingredients, user_id)
#            message = "No preferences found. Here are some default recipes."
#         else:
#             message = "Here are your personalized recommendations."
#     else:
#         recipes = get_recipes_by_ingredients(ingredients)
#         message = "Here are some recipes based on your ingredients."

#     return jsonify({"message": message, "recipes": recipes})


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    user_id = request.form.get('user_id')
    password = request.form.get('password')
    health_conditions = request.form.getlist('health_conditions[]') or []

    formatted_id = f"user_{user_id}"
    namespace = formatted_id

    existing_user = fetch_user_from_pinecone(user_id, namespace)

    if existing_user:
        return redirect(url_for('main.login'))

    save_user_to_pinecone(user_id, password, health_conditions)

    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')  
        password = request.form.get('password')

        formatted_id = f"user_{user_id}"
        namespace = formatted_id

        user_data = fetch_user_from_pinecone(user_id, namespace)

        if user_data:
            stored_password = user_data.get("password")

            if stored_password and check_password_hash(stored_password, password):
                user = User(user_id) 
                login_user(user)
                session['user_id'] = user_id
                return redirect(url_for('main.home'))

            return jsonify({"message": "Invalid credentials"}), 401

        return jsonify({"message": "User not found"}), 404

    return render_template('login.html')

@main.route('/logout')
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('main.home'))

@main.route('/chat', methods=['POST'])
def chat():
    user_id = session.get("user_id")
    user_input = request.json.get("message", "")
    print(f"Incoming request: {request.method} {request.path}")
    response = chatbot_response(user_input)
    # print("respone------------->>>>>>>>>>>",response)
    # Save chat history to Pinecone
    if user_id:
        timestamp = datetime.utcnow().isoformat()
        save_chat_to_pinecone(user_id, user_input, response, timestamp)

    return jsonify(response)

    # if not current_user.is_authenticated:
    #     return jsonify({"error": "User not authenticated"}), 401
        
    # user_input = request.json.get("message", "")
    # response = chatbot_response(user_input)
    
    # # Save chat history to Pinecone with user-specific namespace
    # timestamp = datetime.utcnow().isoformat()
    # chat_id = f"chat_{timestamp}"  # Unique chat ID
    
    # # Store both user message and bot response
    # save_chat_to_pinecone(
    #     user_id=current_user.id,
    #     chat_id=chat_id,
    #     user_message=user_input,
    #     bot_message=response,
    #     timestamp=timestamp
    # )

    # return jsonify(response)

@main.route('/chat-history', methods=['GET'])
def chat_history():

    user_id = request.args.get("user_id")
    chat_id = request.args.get("chat_id")

    try:
        history = load_chat_history(user_id=user_id, chat_id=chat_id)
        return jsonify({"history": history})
    except Exception as e:
        print("Error in /chat-history:", e)
        return jsonify({"error": str(e)}), 500


# @main.route('/chat-history', methods=['GET'])
# def chat_history():
#     if not current_user.is_authenticated:
#         return jsonify({"error": "User not authenticated"}), 401
        
#     try:
#         history = load_chat_history(user_id=current_user.id)
#         return jsonify({"history": history})
#     except Exception as e:
#         print("Error in /chat-history:", e)
#         return jsonify({"error": str(e)}), 500

@main.route('/delete_chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    try:
        index1.delete(
            namespace=current_user.id,  # Or however you're tracking user
            filter={"chat_id": chat_id}
        )
        return jsonify({'message': 'Chat deleted'})
    except Exception as e:
        print("Delete error:", e)
        return jsonify({'error': 'Delete failed'}), 500
      
  
 
@main.route('/getdetail', methods=['GET'])
def getDetails():
    try:
        recipe_id = request.args.get('recipe_id')
        if not recipe_id:
            return jsonify({"error": "Recipe ID is required"}), 400

        # Get recipe information - only using the main endpoint
        api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={SPOONACULAR_API_KEY}"
        response = requests.get(api_url)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch recipe details"}), 500

        recipe_data = response.json()

        # Calculate total cost from pricePerServing
        price_per_serving_cents = recipe_data.get("pricePerServing", 0)
        servings = max(1, recipe_data.get("servings", 1))
        total_cost = (price_per_serving_cents * servings) * 0.03335  # Convert cents to ₹

        # Prepare ingredients list
        ingredients = [
            {
                "name": ing.get("name", ""),
                "amount": ing.get("amount", 0),
                "unit": ing.get("unit", "")
            }
            for ing in recipe_data.get("extendedIngredients", [])
        ]

        return jsonify({
            "title": recipe_data.get("title"),
            "image": recipe_data.get("image"),
            "ingredients": ingredients,
            "instructions": recipe_data.get("instructions", "No instructions available"),
            "servings": servings,
            "readyInMinutes": recipe_data.get("readyInMinutes", "N/A"),
            "totalCost": round(total_cost, 2),
            "costPerServing": round(total_cost / servings, 2) if total_cost > 0 else 0,
            "hasCostData": price_per_serving_cents > 0
        })

    except Exception as e:
        print(f"Error in /getdetail: {e}")
        return jsonify({"error": "Failed to fetch recipe details"}), 500
    

@main.route('/get_diet_plan', methods=['POST'])
def generate_diet():
    form_data = request.get_json()
    print("form_data-->>",form_data)
    user_input = {
        'Ages': form_data['age'],
        'Gender': form_data['gender'],
        'Height': form_data['height'],
        'Weight': form_data['weight'],
        'Activity Level': form_data['activity'],
        'Dietary Preference': form_data['diet'],
        'Disease': form_data['disease']
    }
    if user_input['Disease']=='no':
        daily_macros, weekly_plan_df = get_diet_chart(user_input)
    else:
        daily_macros, weekly_plan_df = generate_diet_plan_disease(user_input)

    # Convert DataFrame to list of dictionaries for JSON
    weekly_plan_json = weekly_plan_df.to_dict(orient='records')

    return jsonify({
        'macros': daily_macros,
        'weekly_plan': weekly_plan_json
    })



# @main.route('/get_user_chats/<user_id>', methods=['GET'])
# def get_user_chats(user_id):
#     try:
#         result = index1.query(
#             vector=[0]*384,
#             top_k=100,
#             namespace=user_id,
#             include_metadata=True
#         )

#         chat_sessions = {}
#         for match in result.matches:
#             meta = match.metadata if hasattr(match, 'metadata') else match['metadata']
#             chat_id = meta.get('chat_id')
#             timestamp = meta.get('timestamp')

#             if chat_id and chat_id not in chat_sessions:
#                 chat_sessions[chat_id] = {
#                     "id": chat_id,
#                     "title": meta.get('chat_title', f"Chat {chat_id}"),
#                     "createdAt": timestamp
#                 }

#         # Return as a list sorted by timestamp (newest first)
#         chats = sorted(
#             chat_sessions.values(),
#             key=lambda x: x.get('createdAt', ''),
#             reverse=True
#         )
        
#         return jsonify(chats)  # This will return an array
    
#     except Exception as e:
#         print("Error in get_user_chats:", e)
#         return jsonify([])  # Always return an array even on error  
  

# @main.route('/get_chat_history/<user_id>/<chat_id>', methods=['GET'])
# def get_chat_history(user_id, chat_id):
#     try:
#         # Optional pagination parameters
#         limit = request.args.get('limit', default=100, type=int)
#         offset = request.args.get('offset', default=0, type=int)
        
#         history = load_chat_history(user_id, chat_id, limit)
        
#         if not isinstance(history, list):
#             return jsonify({"error": "Invalid chat history format"}), 500
            
#         return jsonify({
#             "history": history[offset:offset+limit],
#             "total": len(history)
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @main.route('/register_chat/<user_id>/<chat_id>', methods=['POST'])
# def register_chat(user_id, chat_id):
#     timestamp = datetime.now().isoformat()
#     embedding = embed_text(f"Start of chat {chat_id}")

#     index1.upsert(
#         vectors=[{
#             "id": f"{chat_id}-{timestamp}",
#             "values": embedding,
#             "metadata": {
#                 "user_id": user_id,
#                 "chat_id": chat_id,
#                 "timestamp": timestamp,
#                 "user_msg": "",
#                 "bot_msg": ""
#             }
#         }],
#         namespace=user_id
#     )

#     return jsonify({"status": "ok"})




