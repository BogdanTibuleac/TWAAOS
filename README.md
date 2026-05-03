# Laborator #04: Interfață web pentru gestionarul de sarcini

This is a full-stack Task Manager application with separate backend and frontend components.

## Project Structure

```
lab_app/
├── backend/          # FastAPI backend
│   ├── main.py       # Main FastAPI application
│   ├── auth.py       # Authentication utilities
│   ├── database.py   # Database connection and initialization
│   ├── models.py     # Pydantic models
│   ├── requirements.txt  # Python dependencies
│   └── tasks.db      # SQLite database
├── frontend/         # Web frontend
│   ├── index.html    # Single-page application
│   └── images/       # Screenshots and assets
└── README.md         # This file
```

## Backend (FastAPI)

The backend provides a REST API for task management with JWT authentication.

### Running the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python -m uvicorn main:app --reload
   ```

The full app will be available at `http://localhost:8000`, with the API on the same host.

### API Endpoints

- `POST /inregistrare` - User registration
- `POST /autentificare` - User login (returns JWT)
- `GET /sarcini` - Get user's tasks
- `POST /sarcini` - Create new task
- `GET /sarcini/{id}` - Get specific task
- `PUT /sarcini/{id}` - Update task
- `PATCH /sarcini/{id}/finaliza` - Mark task as completed
- `DELETE /sarcini/{id}` - Delete task

The service status endpoint is available at `GET /api/status`.

## Frontend (HTML/JavaScript)

The frontend is a single-page application built with Bootstrap and vanilla JavaScript.

### Running the Frontend

Recommended: run the backend and open `http://localhost:8000`. FastAPI serves the
frontend directly, so the browser and API share one origin.

You can still use VS Code Live Server:

1. Install VS Code Live Server extension
2. Right-click `frontend/index.html` and select "Open with Live Server"
3. The frontend will call the backend at `http://localhost:8000`

Alternatively, double-click `index.html` to open directly in browser.

### Features

- User registration and login
- JWT-based authentication
- Task CRUD operations
- Responsive Bootstrap UI
- Real-time updates

## Development

- Backend runs on port 8000
- Frontend runs on port 5500 (Live Server)
- CORS is configured to allow frontend requests
- Database persists data in `backend/tasks.db`
