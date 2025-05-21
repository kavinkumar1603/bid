from pymongo import MongoClient
import certifi

def test_mongo_connection():
    """
    Test connection to MongoDB Atlas and print collection names for the 'Newpy' database.
    Returns a list of collection names or error message.
    """
    try:
        client = MongoClient(
            'mongodb+srv://kavin88701:nR1Cc1SOsgRiXedQ@cluster0.01myarq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0',
            tlsCAFile=certifi.where()
        )
        db = client['Newpy']
        collections = db.list_collection_names()
        print("Collections in 'Newpy':", collections)
        return collections
    except Exception as e:
        print("MongoDB connection error:", e)
        return str(e)

if __name__ == "__main__":
    test_mongo_connection()
