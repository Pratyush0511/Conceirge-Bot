from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://digantasadhukhan:Diganta2004@cluster0.bhtdwyg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    # List databases
    print("\nAvailable databases:")
    for db_name in client.list_database_names():
        print(f"- {db_name}")
    
    # Get the hotel_service database
    db = client.get_database('hotel_service')
    
    # List collections
    print("\nCollections in hotel_service:")
    for collection in db.list_collection_names():
        print(f"- {collection}")
        
    print("\n✅ MongoDB Atlas connection verified successfully!")
    
except Exception as e:
    print(f"\n❌ Error connecting to MongoDB Atlas: {e}")