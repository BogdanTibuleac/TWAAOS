from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from auth import create_token, get_current_user, hash_password, verify_password
from database import get_db, initialize_db
from models import TaskCreate, TaskUpdate, UserRegister

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database when the application starts."""
    initialize_db()
    yield


app = FastAPI(title="Task Manager", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if (FRONTEND_DIR / "images").exists():
    app.mount(
        "/images",
        StaticFiles(directory=FRONTEND_DIR / "images"),
        name="images",
    )


@app.get("/")
def serve_frontend():
    """Serve the single-page frontend from the backend."""
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_file)


@app.get("/styles.css")
def serve_styles():
    """Serve frontend styles for the single-page app."""
    styles_file = FRONTEND_DIR / "styles.css"
    if not styles_file.exists():
        raise HTTPException(status_code=404, detail="Stylesheet not found")
    return FileResponse(styles_file)


@app.get("/app.js")
def serve_app_script():
    """Serve frontend JavaScript for the single-page app."""
    script_file = FRONTEND_DIR / "app.js"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script not found")
    return FileResponse(script_file)


@app.get("/api/status")
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


@app.post("/inregistrare", status_code=201)
def inregistreaza(user: UserRegister, db: sqlite3.Connection = Depends(get_db)):
    """Register a new user."""
    existing = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (user.email,),
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        db.execute(
            "INSERT INTO users (email, parola_hash) VALUES (?, ?)",
            (user.email, hash_password(user.parola)),
        )
        db.commit()
    except sqlite3.Error as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from exc

    return {"message": "User registered successfully"}


@app.post("/autentificare")
def autentifica(
    form: OAuth2PasswordRequestForm = Depends(),
    db: sqlite3.Connection = Depends(get_db),
):
    """Authenticate a user and return a JWT access token."""
    user = db.execute(
        "SELECT * FROM users WHERE email = ?",
        (form.username.lower(),),
    ).fetchone()

    if not user or not verify_password(form.password, user["parola_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/sarcini")
def obtine_sarcini(
    doar_nefinalizate: bool = False,
    db: sqlite3.Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return all tasks for the current user, optionally filtering incomplete ones."""
    if doar_nefinalizate:
        tasks = db.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND finalizata = 0",
            (current_user["id"],),
        ).fetchall()
    else:
        tasks = db.execute(
            "SELECT * FROM tasks WHERE user_id = ?",
            (current_user["id"],),
        ).fetchall()

    return [dict(task) for task in tasks]


@app.get("/sarcini/{task_id}")
def obtine_sarcina(
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


@app.post("/sarcini", status_code=201)
def creeaza_sarcina(
    task: TaskCreate,
    db: sqlite3.Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new task for the current user."""
    try:
        cursor = db.execute(
            "INSERT INTO tasks (titlu, descriere, user_id) VALUES (?, ?, ?)",
            (task.titlu, task.descriere, current_user["id"]),
        )
        db.commit()

        new_task = db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (cursor.lastrowid, current_user["id"]),
        ).fetchone()
    except sqlite3.Error as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from exc

    return dict(new_task)


@app.put("/sarcini/{task_id}")
def actualizeaza_sarcina(
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
    new_titlu = (
        task_data.titlu
        if task_data.titlu is not None
        else existing_task_dict["titlu"]
    )
    new_descriere = (
        task_data.descriere
        if task_data.descriere is not None
        else existing_task_dict["descriere"]
    )
    new_finalizata = (
        int(task_data.finalizata)
        if task_data.finalizata is not None
        else existing_task_dict["finalizata"]
    )

    try:
        db.execute(
            """
            UPDATE tasks
            SET titlu = ?, descriere = ?, finalizata = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                new_titlu,
                new_descriere,
                new_finalizata,
                task_id,
                current_user["id"],
            ),
        )
        db.commit()

        updated_task = db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"]),
        ).fetchone()
    except sqlite3.Error as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from exc

    return dict(updated_task)


@app.patch("/sarcini/{task_id}/finaliza")
def finalizeaza_sarcina(
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
        db.execute(
            "UPDATE tasks SET finalizata = 1 WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"]),
        )
        db.commit()

        updated = db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"]),
        ).fetchone()
    except sqlite3.Error as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from exc

    return dict(updated)


@app.delete("/sarcini/{task_id}")
def sterge_sarcina(
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
        db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"]),
        )
        db.commit()
    except sqlite3.Error as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from exc

    return {"message": f"Task {task_id} deleted successfully"}
