from flask_login import UserMixin
from .vector_db.bot import index

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    @staticmethod
    def get(user_id):
        """Fetch user from Pinecone using the correct namespace."""
        namespace = f"user_{user_id}"  # Construct the namespace dynamically
        # namespace = "user_"+user_id  # Construct the namespace dynamically
        print("user_"+user_id)
        print(f"🔍 Fetching user {user_id} from namespace {namespace}...")

        response = index.fetch(["manisha@09"], namespace="user_manisha@09")  # Fetch from correct namespace
        # print(f"🛠 Pinecone Response: {response}")

        if response and response.vectors:
            print(f"✅ User {user_id} found in Pinecone!")
            return User(user_id)

        print(f"❌ User {user_id} not found in Pinecone!")
        return None
