from .recipe_utils import get_recipes_by_ingredients
from .vector_db.bot import get_recommendations
from .vector_db.bot import index
import requests
import os
from sentence_transformers import SentenceTransformer


def get_recommendations(user_id, ingredients):
    from .vector_db.bot import index  # Import inside function to avoid circular imports

    try:
        # Fetch user preference vector from Pinecone
        user_vector = index.fetch([user_id]).vectors.get(user_id)

        if not user_vector:
            print(f"No preferences found for user {user_id}. Fetching recipes without filtering.")
            return get_recipes_by_ingredients(ingredients, user_id)  # Return Spoonacular recipes

        # Query Pinecone for similar recipes
        results = index.query(vector=user_vector, top_k=10)
        return results

    except Exception as e:
        print(f"Error fetching recommendations: {e}")
        return get_recipes_by_ingredients(ingredients, user_id)  # Return default recipes
       
    
def save_nutrients(recipe_id, user_id):
   
    api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json"
   
    api_key = os.getenv('SPOONACULAR_API_KEY')  # Replace with your Spoonacular API key
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    # Fetch data from Spoonacular API
    try:
        response = requests.get(api_url, params={"apiKey": api_key})
        # print("Request URL:", api_url)
        # print("API Response Status Code:", response.status_code)
        # print("API Response Content:", response.text)
        
        # Check if the request was successful
        if response.status_code != 200:
            print("API Response Content:", response.text)
            raise ValueError(f"API request failed with status code {response.status_code}")
        
        
        data = response.json()
        # Extract nutrient values
        nutrients = data.get("nutrients", [])

        vectors = {}

        for item in nutrients:
            name = item["name"]
            amount = item["amount"]
            unit = item["unit"]
            
            text = f"{name}: {amount} {unit}"
            embedding = model.encode(text)
            
            vectors[name] = embedding

        # Store in Pinecone with user-specific namespace
        namespace = f"user_{user_id}"  # Unique namespace for each user
        to_upsert = [ (f"user_{user_id} recipe{recipe_id} nutrient{i}", vectors[nutrient], {"name": nutrient}) 
        for i, nutrient in enumerate(vectors.keys())]
        # print(to_upsert)
        
        index.upsert(to_upsert, namespace=namespace)

        print(f"✅ Nutrition data for User {user_id} stored successfully!")
    except Exception as e:
        print(f"Error fetching nutrition data: {e}")
        return 



