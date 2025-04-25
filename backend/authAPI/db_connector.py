from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, SocialAccount
from typing import Generator, Optional

# Method 1: Direct SQLAlchemy connection (recommended for Python applications)
def get_db_connection() -> Generator[Session, None, None]:
    """
    Creates a database session using SQLAlchemy. Use this in a with statement or context manager.
    
    Example usage:
    ```python
    with get_db_connection() as db:
        users = db.query(User).all()
    ```
    """
    engine = create_engine(
        "sqlite:///./auth.db",
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Method 2: Simple connection helper (alternative approach)
class DatabaseConnection:
    """
    A class-based database connection helper.
    
    Example usage:
    ```python
    db = DatabaseConnection()
    users = db.get_all_users()
    user = db.get_user_by_username("john_doe")
    ```
    """
    def __init__(self):
        self.engine = create_engine(
            "sqlite:///./auth.db",
            connect_args={"check_same_thread": False}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def get_all_users(self) -> list[User]:
        with self.get_session() as session:
            return session.query(User).all()

    def get_user_by_username(self, username: str) -> Optional[User]:
        with self.get_session() as session:
            return session.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        with self.get_session() as session:
            return session.query(User).filter(User.email == email).first()

    def get_social_accounts(self, user_id: int) -> list[SocialAccount]:
        with self.get_session() as session:
            return session.query(SocialAccount).filter(SocialAccount.user_id == user_id).all()

# Example usage:
if __name__ == "__main__":
    # Example 1: Using the generator function
    with get_db_connection() as db:
        users = db.query(User).all()
        print(f"Found {len(users)} users")

    # Example 2: Using the DatabaseConnection class
    db = DatabaseConnection()
    users = db.get_all_users()
    print(f"Found {len(users)} users")

    # Example of getting a specific user
    user = db.get_user_by_username("john_doe")
    if user:
        print(f"Found user: {user.username} ({user.email})")
        # Get their social accounts
        social_accounts = db.get_social_accounts(user.id)
        print(f"User has {len(social_accounts)} social accounts") 