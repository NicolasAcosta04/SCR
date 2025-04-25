# Authentication API Endpoints

## User Registration and Login

### Register New User
- **Endpoint**: `POST /register`
- **Description**: Register a new user with email and password
- **Request Body**:
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123"
}
```
- **Response** (200 OK):
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```
- **Error Responses**:
  - 400: Username or email already registered
  - 422: Validation error (invalid email format, etc.)

### Login with Username/Password
- **Endpoint**: `POST /token`
- **Description**: Login with username and password
- **Request Body** (form-data):
```
username: john_doe
password: securepassword123
```
- **Response** (200 OK):
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```
- **Error Responses**:
  - 401: Incorrect username or password
  - 422: Validation error

## Social Authentication

### Google OAuth Login
- **Endpoint**: `POST /login/google`
- **Description**: Login or register with Google OAuth token
- **Request Body**:
```json
{
    "token": "google_oauth_token_here"
}
```
- **Response** (200 OK):
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```
- **Error Responses**:
  - 401: Invalid Google token
  - 422: Validation error

### Apple Sign In (Future Implementation)
- **Endpoint**: `POST /login/apple`
- **Description**: Login or register with Apple ID token
- **Status**: Not yet implemented

## User Profile Management

### Get Current User Profile
- **Endpoint**: `GET /users/me`
- **Description**: Get the profile of the currently authenticated user
- **Headers Required**:
```
Authorization: Bearer your_access_token_here
```
- **Response** (200 OK):
```json
{
    "username": "john_doe",
    "email": "john@example.com"
}
```
- **Error Responses**:
  - 401: Invalid or expired token
  - 404: User not found

### Logout
- **Endpoint**: `POST /logout`
- **Description**: Invalidate the current user's token
- **Headers Required**:
```
Authorization: Bearer your_access_token_here
```
- **Response** (200 OK):
```json
{
    "message": "Successfully logged out"
}
```
- **Error Responses**:
  - 401: Invalid or expired token
  - 400: Invalid token format

## Using the API

### Authentication
All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer your_access_token_here
```

### Error Response Format
Error responses follow this format:
```json
{
    "detail": "Error message here"
}
```

### CORS
The API accepts requests from `http://localhost:5173` by default. For other origins, update the CORS settings in `main.py`.

### Rate Limiting
Currently, no rate limiting is implemented. Consider adding rate limiting in production.

## Testing the API

You can test the API using curl:

### Register a new user:
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","email":"test@example.com","password":"test123"}'
```

### Login:
```bash
curl -X POST http://localhost:8000/token \
  -d "username=test_user&password=test123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

### Get user profile:
```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer your_access_token_here"
``` 