# Authentication API

This is a FastAPI-based authentication service that provides:
- Username/password registration and login
- Google OAuth login
- JWT token-based authentication
- User profile management
- SQLite database for user data storage

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
```

4. Initialize the database:
```bash
python init_db.py
```
This will create the SQLite database file (`auth.db`) and set up all necessary tables.

5. Run the server:
```bash
uvicorn main:app --reload --port 8000
```

## API Documentation

For detailed API documentation including all endpoints, request/response formats, and example usage, see [API_ENDPOINTS.md](API_ENDPOINTS.md).

Quick endpoint reference:
- `POST /register` - Register a new user
- `POST /token` - Login with username/password
- `POST /login/google` - Login with Google
- `GET /users/me` - Get current user profile

## Database Access

The application uses SQLite as its database. You can:

1. Use the provided `db_connector.py` to access the database from external applications:
```python
from db_connector import DatabaseConnection

db = DatabaseConnection()
users = db.get_all_users()
```

2. Directly inspect the database using SQLite CLI:
```bash
sqlite3 auth.db

# Common SQLite commands:
.tables          # List all tables
.schema users    # Show users table schema
.quit           # Exit SQLite
```

## Frontend Integration

Update your frontend Google OAuth client ID in:
- `frontend/src/main.tsx`
- `.env` file in the authAPI directory

The API is configured to accept requests from `http://localhost:5173`. Update the CORS settings in `main.py` if your frontend runs on a different port. 