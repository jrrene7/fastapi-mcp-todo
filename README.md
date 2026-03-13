# FastAPI MCP ToDo

FastAPI ToDo app using **SQLite + SQLAlchemy + Pydantic**, exposed as **MCP tools** via `fastapi-mcp`.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

- Swagger UI: `http://127.0.0.1:8000/docs`
- MCP endpoint: `http://127.0.0.1:8000/mcp`

## API

- `POST /todos` (operation_id: `create_new_todo`)
- `GET /todos` (operation_id: `get_all_todos`)
- `GET /todos/{todo_id}` (operation_id: `get_todo`)
- `PUT /todos/{todo_id}` (operation_id: `update_todo`)
- `DELETE /todos/{todo_id}` (operation_id: `delete_todo`)
