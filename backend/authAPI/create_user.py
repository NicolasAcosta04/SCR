from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import get_password_hash

def create_user(username: str, email: str, password: str) -> models.User:
    """Create a new user with proper password hashing"""
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(models.User).filter(
            (models.User.username == username) | 
            (models.User.email == email)
        ).first()
        
        if existing_user:
            print(f"Error: User with username '{username}' or email '{email}' already exists")
            return None

        # Create new user
        hashed_password = get_password_hash(password)
        db_user = models.User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        print(f"Successfully created user: {username}")
        return db_user
    
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python create_user.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_user(username, email, password) 