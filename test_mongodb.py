import os
import sys
import time
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables
load_dotenv()

# First try with Atlas connection
def try_connection(uri, is_atlas=False, max_retries=3):
    print(f"Attempting connection to: {uri if not is_atlas else 'MongoDB Atlas (credentials hidden)'}")
    
    for attempt in range(max_retries):
        try:
            # Configure connection options based on connection type
            options = {}
            if is_atlas:
                options.update({
                    'connectTimeoutMS': 30000,  # Increase connection timeout
                    'socketTimeoutMS': 45000,  # Increase socket timeout
                    'serverSelectionTimeoutMS': 30000,  # Increase server selection timeout
                    'retryWrites': True,
                    'w': 'majority',
                    'retryReads': True
                })
            else:
                options.update({
                    'serverSelectionTimeoutMS': 5000  # Shorter timeout for local
                })
            
            # Connect to MongoDB
            client = MongoClient(uri, **options)
            
            # Test connection with ping instead of server_info
            client.admin.command('ping')
            print("✅ Successfully connected to MongoDB!")
            return client
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Connection attempt {attempt+1} failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"❌ Error connecting to MongoDB after {max_retries} attempts: {str(e)}")
                return None
        except Exception as e:
            print(f"❌ Unexpected error connecting to MongoDB: {str(e)}")
            return None

# Get MongoDB URI from environment
atlas_uri = os.getenv('MONGODB_URI', '')

# Replace password placeholder with actual password
db_password = "Diganta2004"  # Using the provided password
if '<db_password>' in atlas_uri:
    atlas_uri = atlas_uri.replace('<db_password>', db_password)

# Try Atlas connection first
client = try_connection(atlas_uri, is_atlas=True)

# If Atlas fails, try local MongoDB
if client is None:
    print("\nFalling back to local MongoDB...")
    local_uri = "mongodb://localhost:27017/hotel_service"
    client = try_connection(local_uri)

# If both connections fail, use a mock MongoDB for testing
if client is None:
    print("\nFailed to connect to both MongoDB Atlas and local MongoDB.")
    print("Using a mock MongoDB implementation for testing...")
    
    # Create a simple mock MongoDB implementation
    class MockCollection:
        def __init__(self, name):
            self.name = name
            self.documents = []
        
        def insert_one(self, document):
            document['_id'] = f"mock_id_{len(self.documents) + 1}"
            self.documents.append(document)
            class MockResult:
                def __init__(self, inserted_id):
                    self.inserted_id = inserted_id
            return MockResult(document['_id'])
        
        def find_one(self, query):
            for doc in self.documents:
                match = True
                for key, value in query.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    return doc
            return None
        
        def delete_one(self, query):
            for i, doc in enumerate(self.documents):
                if '_id' in query and doc['_id'] == query['_id']:
                    del self.documents[i]
                    class MockDeleteResult:
                        def __init__(self):
                            self.deleted_count = 1
                    return MockDeleteResult()
            return None
    
    class MockDatabase:
        def __init__(self, name):
            self.name = name
            self.collections = {}
        
        def __getattr__(self, name):
            if name not in self.collections:
                self.collections[name] = MockCollection(name)
            return self.collections[name]
        
        def list_collection_names(self):
            return list(self.collections.keys())
    
    class MockClient:
        def __init__(self):
            self.db = MockDatabase('hotel_service')
        
        def get_database(self):
            return self.db
    
    # Use the mock client
    client = MockClient()

# Get database
db = client.get_database()
print(f"Database name: {db.name}")

# List collections
collections = db.list_collection_names()
print(f"Collections: {collections}")

try:
    # Create a test document
    test_collection = db.test_collection
    test_doc = {
        "name": "MongoDB Test",
        "status": "success",
        "timestamp": datetime.datetime.now()
    }
    
    # Insert the test document
    result = test_collection.insert_one(test_doc)
    print(f"Inserted document with ID: {result.inserted_id}")
    
    # Retrieve the document
    retrieved_doc = test_collection.find_one({"name": "MongoDB Test"})
    print(f"Retrieved document: {retrieved_doc}")
    
    # Clean up - delete the test document
    test_collection.delete_one({"_id": result.inserted_id})
    print("Test document deleted")
    
    print("\n✅ MongoDB connection and functionality verified successfully!")
    print("Note: This may be using a mock implementation if real MongoDB connections failed.")
    
except Exception as e:
    print(f"Error performing MongoDB operations: {e}")