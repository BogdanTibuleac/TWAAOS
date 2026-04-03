from contextlib import asynccontextmanager
import sqlite3

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from auth import create_token, get_current_user, hash_password, verify_password
from database import get_db, initialize_db
from models import TaskCreate, TaskUpdate, UserRegister


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database when the application starts."""
    initialize_db()
    yield


app = FastAPI(title="Task Manager", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Basic service status endpoint."""
    return {"status": "active"}


@app.get("/health/db")
def check_db_health(db: sqlite3.Connection = Depends(get_db)):
    """Verify that the database connection is working."""
    try:
        db.execute("SELECT 1")
        return {"database": "up"}
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500, detail="Database is down"
        ) from exc


@app.post("/register", status_code=201)
def register(user: UserRegister, db: sqlite3.Connection = Depends(get_db)):
    """Register a new user."""
    existing = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (user.email,),
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        with db:
            db.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (user.email, hash_password(user.password)),
            )
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Database error") from exc

    return {"message": "User registered successfully"}


@app.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: sqlite3.Connection = Depends(get_db),
):
    """Authenticate a user and return a JWT access token."""
    user = db.execute(
        "SELECT * FROM users WHERE email = ?",
        (form.username.lower(),),
    ).fetchone()

    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/tasks")
def get_tasks(
    only_incomplete: bool = False,
    db: sqlite3.Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return all tasks for the current user, optionally filtering incomplete ones."""
    if only_incomplete:
        tasks = db.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND completed = 0",
            (current_user["id"],),
        ).fetchall()
    else:
        tasks = db.execute(
            "SELECT * FROM tasks WHERE user_id = ?",
            (current_user["id"],),
        ).fetchall()

    return [dict(task) for task in tasks]


@app.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return one task by id for the current user."""
    task = db.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, current_user["id"]),
    ).fetchone()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return dict(task)


@app.post("/tasks", status_code=201)
def create_task(
    task: TaskCreate,
    db: sqlite3.Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new task for the current user."""
    try:
        with db:
            cursor = db.execute(
                "INSERT INTO tasks (title, description, user_id) VALUES (?, ?, ?)",
                (task.title, task.description, current_user["id"]),
            )

        new_task = db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (cursor.lastrowid, current_user["id"]),
        ).fetchone()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Database error") from exc

    return dict(new_task)


@app.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: sqlite3.Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing task for the current user."""
    existing_task = db.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, current_user["id"]),
    ).fetchone()

    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    existing_task_dict = dict(existing_task)
    new_title = (
        task_data.title
        if task_data.title is not None
        else existing_task_dict["title"]
    )
    new_description = (
        task_data.description
        if task_data.description is not None
        else existing_task_dict["description"]
    )
    new_completed = (
        int(task_data.completed)
        if task_data.completed is not None
        else existing_task_dict["completed"]
    )

    try:
        with db:
            db.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, completed = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    new_title,
                    new_description,
                    new_completed,
                    task_id,
                    current_user["id"],
                ),
            )

        updated_task = db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"]),
        ).fetchone()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Database error") from exc

    return dict(updated_task)


@app.patch("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a task as completed for the current user."""
    task = db.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, current_user["id"]),
    ).fetchone()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        with db:
            db.execute(
                "UPDATE tasks SET completed = 1 WHERE id = ? AND user_id = ?",
                (task_id, current_user["id"]),
            )

        updated = db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"]),
        ).fetchone()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Database error") from exc

    return dict(updated)


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a task owned by the current user."""
    task = db.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, current_user["id"]),
    ).fetchone()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        with db:
            db.execute(
                "DELETE FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, current_user["id"]),
            )
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Database error") from exc

    return {"message": f"Task {task_id} deleted successfully"}
