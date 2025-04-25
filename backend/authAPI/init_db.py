from sqlalchemy import create_engine
from models import Base
import os

def init_database():
    # Create the database file if it doesn't exist
    db_path = "./auth.db"
    abs_db_path = os.path.abspath(db_path)
    print(abs_db_path)
    
    # Create SQLite database engine
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print(f"Database initialized at: {abs_db_path}")
    print("Tables created successfully!")

if __name__ == "__main__":
    init_database() 