"""
ToDo API - FastAPI + SQLAlchemy + SQLite + Pydantic
Full CRUD: Create, Read (one/all), Update, Delete
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime

from fastapi_mcp import FastApiMCP

# --- SQLAlchemy setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TodoModel(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1024), default="")
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


Base.metadata.create_all(bind=engine)


# --- Pydantic schemas ---
class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default="", max_length=1024)
    completed: bool = False


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    completed: Optional[bool] = None


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Lifespan: optional, for future use ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="ToDo API", lifespan=lifespan)


# --- CRUD endpoints ---

@app.post(
    "/todos",
    response_model=TodoResponse,
    operation_id="create_new_todo",
    tags=["todos"],
)
def create_new_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo."""
    db_todo = TodoModel(
        title=todo.title,
        description=todo.description or "",
        completed=todo.completed,
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@app.get(
    "/todos",
    response_model=list[TodoResponse],
    operation_id="get_all_todos",
    tags=["todos"],
)
def get_all_todos(
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """List all todos with optional pagination and completed filter."""
    q = db.query(TodoModel)
    if completed is not None:
        q = q.filter(TodoModel.completed == completed)
    return q.offset(skip).limit(limit).all()


@app.get(
    "/todos/{todo_id}",
    response_model=TodoResponse,
    operation_id="get_todo",
    tags=["todos"],
)
def get_todo_by_id(todo_id: int, db: Session = Depends(get_db)):
    """Get a single todo by id."""
    todo = db.query(TodoModel).filter(TodoModel.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.put(
    "/todos/{todo_id}",
    response_model=TodoResponse,
    operation_id="update_todo",
    tags=["todos"],
)
def update_todo_by_id(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    """Update a todo by id (partial update)."""
    db_todo = db.query(TodoModel).filter(TodoModel.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    data = todo.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_todo, key, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@app.delete(
    "/todos/{todo_id}",
    status_code=204,
    operation_id="delete_todo",
    tags=["todos"],
)
def delete_todo_by_id(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo by id."""
    db_todo = db.query(TodoModel).filter(TodoModel.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(db_todo)
    db.commit()
    return None


@app.get("/")
def root():
    return {
        "message": "ToDo API",
        "docs": "/docs",
        "health": "/healthz",
        "mcp_http": "/mcp",
        "mcp_sse": "/sse",
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# --- MCP server (exposes selected FastAPI operations as tools) ---
# Build the MCP server after registering the tagged routes it should expose.
mcp = FastApiMCP(app, include_tags=["todos"])
mcp.mount_http()
mcp.mount_sse(mount_path="/sse")
