from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional, List
import os
from dotenv import load_dotenv
import models
import auth
from database import engine, get_db
from pydantic import BaseModel, EmailStr
import requests
from forgot_password import router as forgot_password_router

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Authentication API")

# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    preferences: List[str]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class GoogleToken(BaseModel):
    token: str

class CategoryPreference(BaseModel):
    categories: List[models.CategoryEnum]

class UserPreferencesResponse(BaseModel):
    preferences: List[str]

    class Config:
        from_attributes = True

# Helper function to get current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = auth.verify_token(token, db)
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
        
    return user

@app.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | 
        (models.User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )

    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        preferences=[]  # Initialize empty preferences list
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access token
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with username and password"""
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login/google", response_model=Token)
async def google_login(token_data: GoogleToken, db: Session = Depends(get_db)):
    """Login or register with Google OAuth"""
    google_user = auth.verify_google_token(token_data.token)
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.email == google_user["email"]).first()
    
    if not user:
        # Create new user from Google data
        username_base = google_user["email"].split("@")[0]
        username = username_base
        counter = 1
        
        # Handle username conflicts
        while db.query(models.User).filter(models.User.username == username).first():
            username = f"{username_base}{counter}"
            counter += 1
            
        user = models.User(
            email=google_user["email"],
            username=username,
            hashed_password=""  # No password for Google users
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create social account link
        social = models.SocialAccount(
            provider="google",
            provider_user_id=google_user["sub"],
            user_id=user.id
        )
        db.add(social)
        db.commit()

    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@app.get("/users/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's category preferences"""
    return {"preferences": current_user.preferences or []}

@app.post("/users/me/preferences", response_model=UserPreferencesResponse)
async def add_user_preference(
    preference: CategoryPreference,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add category preferences for the current user"""
    if len(preference.categories) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 5 categories allowed"
        )
    
    # Update user preferences
    current_user.preferences = [cat.value for cat in preference.categories]
    db.commit()
    db.refresh(current_user)
    
    return {"preferences": current_user.preferences}

@app.delete("/users/me/preferences/{category}")
async def remove_user_preference(
    category: models.CategoryEnum,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a category preference for the current user"""
    if not current_user.preferences or category.value not in current_user.preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found"
        )
    
    current_user.preferences.remove(category.value)
    db.commit()
    return {"message": "Preference removed successfully"}

# Add the logout endpoint
@app.post("/logout")
async def logout(
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Logout the current user by blacklisting their token"""
    auth.blacklist_token(token, db)
    return {"message": "Successfully logged out"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}

app.include_router(forgot_password_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 