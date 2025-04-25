from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from passlib.context import CryptContext

from database import get_db
from models import User, PasswordResetToken

router = APIRouter(prefix="/auth", tags=["auth"])  # Define prefix here instead of in main.py

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

def generate_reset_code() -> str:
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def send_reset_email(email: str, code: str):
    # Email configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = email
    msg['Subject'] = "Password Reset Code"

    # Create email body with reset link
    body = f"""
    <html>
        <body>
            <h2>Password Reset Code</h2>
            <p>You have requested to reset your password. Use the following code to proceed:</p>
            <p style="font-size: 24px; font-weight: bold; letter-spacing: 5px; text-align: center; padding: 20px; background-color: #f3f4f6; border-radius: 5px;">
                {code}
            </p>
            <p>Or click the link below to go directly to the reset page:</p>
            <p style="text-align: center; margin: 20px 0;">
                <a href="{FRONTEND_URL}/reset-password" 
                   style="background-color: #4f46e5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Reset Password
                </a>
            </p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <p>This code will expire in 15 minutes.</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    # Send email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset email")

@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    # Hash the password
    hashed_password = pwd_context.hash(request.password)

    # Create new user
    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate access token (you might want to use JWT here)
    # For now, we'll just return a success message
    return {"message": "User registered successfully"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Return success even if user doesn't exist to prevent email enumeration
        return {"message": "If an account exists with this email, you will receive a password reset code."}

    # Generate and store reset code
    code = generate_reset_code()
    expires_at = datetime.utcnow() + timedelta(minutes=15)  # Code expires in 15 minutes
    
    # Store code in database
    reset_token = PasswordResetToken(
        token=code,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()

    # Send reset email
    send_reset_email(request.email, code)

    return {"message": "If an account exists with this email, you will receive a password reset code."}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Find the reset code
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.expires_at > datetime.utcnow(),
        PasswordResetToken.used == False
    ).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")

    # Update user's password
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # Hash the new password
    hashed_password = pwd_context.hash(request.new_password)
    user.hashed_password = hashed_password
    reset_token.used = True
    db.commit()

    return {"message": "Password has been reset successfully"}

def test_smtp_connection():
    """Test the SMTP connection and authentication settings"""
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
        return {
            "success": False,
            "error": "Missing SMTP configuration. Please check your environment variables."
        }

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = SMTP_USERNAME  # Send test email to yourself
        msg['Subject'] = "SMTP Configuration Test"

        # Create email body
        body = """
        <html>
            <body>
                <h2>SMTP Configuration Test</h2>
                <p>This is a test email to verify your SMTP configuration.</p>
                <p>If you're receiving this email, your SMTP settings are working correctly!</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        # Test SMTP connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        # Test authentication
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Test sending
        server.send_message(msg)
        server.quit()

        return {
            "success": True,
            "message": "SMTP configuration test successful. Test email sent to your address."
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Authentication failed. Please check your SMTP_USERNAME and SMTP_PASSWORD."
        }
    except smtplib.SMTPConnectError:
        return {
            "success": False,
            "error": "Could not connect to SMTP server. Please check SMTP_SERVER and SMTP_PORT."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"SMTP test failed: {str(e)}"
        }

@router.get("/test-smtp")
async def test_smtp_endpoint():
    """Endpoint to test SMTP configuration"""
    result = test_smtp_connection()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result 