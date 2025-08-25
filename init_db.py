from app import create_app, db
from app.models.document import Document, DocumentChunk, GuestRequest
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.analytics import Analytics

def init_database():
    app = create_app()
    with app.app_context():
        try:
            print("Dropping all tables...")
            db.drop_all()
            
            print("Creating all tables...")
            db.create_all()
            
            print("\nDatabase initialized successfully!")
            print("\nTables created:")
            inspector = db.inspect(db.engine)
            for table in inspector.get_table_names():
                print(f"- {table}")
                
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    init_database()
