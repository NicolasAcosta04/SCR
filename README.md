# SCR

The github repository for this code is here: https://github.com/NicolasAcosta04/SCR

## Setup and Running Instructions

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm i
```

3. Start the development server:
```bash
npm run dev
```

### Backend Setup

#### AuthAPI Setup
1. Navigate to the authAPI directory:
```bash
cd backend/authAPI
```

2. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the development server:
```bash
uvicorn main:app --reload --port 8000
```

#### ModelAPI Setup
1. Navigate to the modelAPI directory:
```bash
cd backend/modelAPI
```

2. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the development server:
```bash
uvicorn main:app --reload --port 8080
```

## Running the Complete Application
To run the complete application, you'll need to have all three components running simultaneously:
1. Frontend development server
2. AuthAPI server on port 8000
3. ModelAPI server on port 8080

Make sure to keep all terminal windows open while running the application.
