
from collections import defaultdict
import json
import os
from datetime import datetime
import google.generativeai as genai
from .embeddings import embed_text
from .bot import index1

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
model = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config=genai.types.GenerationConfig(
        temperature=0,
    )
)

# ✅ Save chat in user-specific namespace
def save_chat_to_pinecone(user_id, chat_id, user_msg, bot_msg):
    print("🧠 save_chat_to_pinecone called!")

    # print("🔁 SAVE DEBUG - user_msg =", repr(user_msg))
    # print("🔁 SAVE DEBUG - bot_msg =", repr(bot_msg))

    timestamp = datetime.now().isoformat()
    vector_id = f"{chat_id}-{timestamp}"
    namespace = user_id  # 🧠 this ensures per-user isolation

    # Convert user and bot messages to strings (especially if dict/list)
    user_msg_str = json.dumps(user_msg) if isinstance(user_msg, (dict, list)) else str(user_msg)
    bot_msg_str = json.dumps(bot_msg) if isinstance(bot_msg, (dict, list)) else str(bot_msg)

    # Combine for embedding
    combined_text = f"User: {user_msg_str}\nBot: {bot_msg_str}"
    embedding = embed_text(combined_text)

    # Debug output
    # print("user_msg_str:", type(user_msg_str), user_msg_str)
    # print("bot_msg_str:", type(bot_msg_str), bot_msg_str)

    # Save to Pinecone
    index1.upsert(
        vectors=[{
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "user_id": str(user_id),
                "chat_id": str(chat_id),
                "timestamp": str(timestamp),
                "user_msg": user_msg_str,
                "bot_msg": bot_msg_str
            }
        }],
        namespace=namespace
    )

def load_chat_history(user_id, chat_id, limit=100):
    try:
        namespace = user_id
        print(f"🧠 Querying Pinecone for chat {chat_id} in namespace {namespace}")

        # Use filter to only get messages from this chat
        query = index1.query(
            namespace=namespace,
            top_k=limit,
            include_metadata=True,
            vector=[0] * 384,
            filter={"chat_id": {"$eq": chat_id}}
        )

        # Sort by timestamp (newest first)
        matches = sorted(
            query.matches,
            key=lambda x: x.metadata.get("timestamp", ""),
            reverse=True
        )

        # Format as list of tuples (user_msg, bot_msg)
        chat_history = [
            (match.metadata["user_msg"], match.metadata["bot_msg"])
            for match in matches
            if "user_msg" in match.metadata and "bot_msg" in match.metadata
        ]

        print(f"✅ Retrieved {len(chat_history)} messages for chat {chat_id}")
        return chat_history

    except Exception as e:
        print(f"❌ Error loading chat history: {e}")
        return []
    
    
    
    
    
    
    
    
# def save_chat_to_pinecone(user_id, chat_id, user_msg, bot_msg, timestamp):
#     print("🧠 save_chat_to_pinecone called!")
    
#     # Convert messages to strings if they're objects
#     user_msg_str = json.dumps(user_msg) if isinstance(user_msg, (dict, list)) else str(user_msg)
#     bot_msg_str = json.dumps(bot_msg) if isinstance(bot_msg, (dict, list)) else str(bot_msg)
    
#     # Create embedding from the combined messages
#     combined_text = f"User: {user_msg_str}\nBot: {bot_msg_str}"
#     embedding = embed_text(combined_text)
    
#     # Store with user_id as namespace
#     index1.upsert(
#         vectors=[{
#             "id": f"msg_{timestamp}",
#             "values": embedding,
#             "metadata": {
#                 "user_id": str(user_id),
#                 "chat_id": str(chat_id),
#                 "user_msg": user_msg_str,
#                 "bot_msg": bot_msg_str,
#                 "timestamp": timestamp
#             }
#         }],
#         namespace=str(user_id)  # Each user has their own namespace
#     )

# def load_chat_history(user_id, limit=20):
    try:
        # Query the user's namespace to get their chat history
        results = index1.query(
            namespace=str(user_id),
            top_k=limit,
            include_metadata=True,
            vector=[0]*384  # Dummy vector
        )
        
        # Format the history
        history = []
        for match in results.matches:
            meta = match.metadata
            history.append({
                "timestamp": meta.get("timestamp"),
                "user_message": meta.get("user_msg"),
                "bot_message": meta.get("bot_msg")
            })
        
        # Sort by timestamp (newest first)
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return []