import os
import json
from dotenv import load_dotenv
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from sentence_transformers import SentenceTransformer
from werkzeug.security import generate_password_hash, check_password_hash
# Load environment variables
load_dotenv() 

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Create or connect to an index
index_name = "bot1"
if index_name not in [idx['name'] for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=384,  # Corrected dimension for 'all-MiniLM-L6-v2'
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

# Connect to the index
index = pc.Index(index_name)




index_name = "chat-history"
if index_name not in [idx['name'] for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=384,  # Corrected dimension for 'all-MiniLM-L6-v2'
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

index1 = pc.Index("chat-history")
__all__ = ['index','index1']


def fetch_user_from_pinecone(user_id, namespace):
    """ Fetch user credentials from Pinecone metadata within a namespace. """
    try:
        formatted_id = f"user_{user_id}"  # Ensure ID format matches stored format
        print(f"🔍 Searching for User ID: {formatted_id} in Namespace: {namespace}")

        # Fetch user from Pinecone using namespace
        response = index.fetch(ids=[formatted_id], namespace=namespace)
        
        # 🔎 Debugging Logs
        # print(f"🔹 Fetch Response Type: {type(response)}")
        # print(f"🔹 Fetch Response Content: {response}")
        # print(f"🔹 Vectors in Response: {response.vectors}")

        # Check if the user exists in Pinecone's response
        if response.vectors and formatted_id in response.vectors:
            user_data = response.vectors[formatted_id]  # Correct way to access vectors
            
            # Ensure metadata and password exist
            if "metadata" in user_data and "password" in user_data["metadata"]:
                print(f"✅ User {user_id} found in Pinecone!")
                return user_data["metadata"]  # Return user metadata
            
        # If no user is found, print an error and return None
        print(f"❌ User '{user_id}' not found in Pinecone.")
        return None  

    except Exception as e:
        print(f"⚠️ Error fetching user {user_id}: {e}")
        return None  


def save_user_to_pinecone(user_id, password, health_conditions):
    """ Store user credentials in Pinecone metadata. """
    try:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        hashed_password = generate_password_hash(password)  # Hash password securely
        namespace = f"user_{user_id}"  # Unique namespace per user

        # Ensure health_conditions is a list
        if not isinstance(health_conditions, list):
            health_conditions = [health_conditions]

        # Convert health conditions to a single string and embed it
        health_text = " ".join(health_conditions) if health_conditions else "No conditions"
        health_embedding = model.encode(health_text).tolist()  # Convert NumPy array to list
       
        user_vector = {
            "id": f"user_{user_id}",
            "values": health_embedding,  # Store health conditions as an embedding
            "metadata": {
                "user_id": user_id,
                "password": hashed_password,  # Store hashed password in metadata
                "health_conditions": json.dumps(health_conditions)  # Store as JSON
            }
        }

        # Insert into Pinecone
        index.upsert([user_vector], namespace=namespace)

        print(f"✅ User {user_id} registered successfully with embedded health conditions!")

    except Exception as e:
        print(f"❌ Error saving user {user_id}: {e}")

def get_recommendations(user_id, ingredients):
    try:
        user_vector = index.fetch([user_id]).vectors[user_id]
        # print(f"User vector: {user_vector}")
        results = index.query(vector=user_vector, top_k=5)
        return results
    except KeyError:
        print(f"No preferences found for user {user_id}")
        return []  # Return an empty list or fetch default recipes
