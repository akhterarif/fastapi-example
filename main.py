from typing import List
import databases
import sqlalchemy
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import urllib

# SQLAlchemy specific code, as with any other app
# DATABASE_URL = "sqlite:///./test.db"

host_server = os.environ.get('host_server', 'localhost')
db_server_port = urllib.parse.quote_plus(str(os.environ.get('db_server_port', '5432')))
database_name = os.environ.get('database_name', 'fastapi')
db_username = urllib.parse.quote_plus(str(os.environ.get('db_username', 'postgres')))
db_password = urllib.parse.quote_plus(str(os.environ.get('db_password', 'Off1ce')))
DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}'.format(db_username,db_password, host_server, db_server_port, database_name)

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

todos = sqlalchemy.Table(
    "todos",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("text", sqlalchemy.String),
    sqlalchemy.Column("completed", sqlalchemy.Boolean),
)


engine = sqlalchemy.create_engine(
    DATABASE_URL, pool_size=3, max_overflow=0
)
metadata.create_all(engine)


class TodoInput(BaseModel):
    text: str
    completed: bool


class Todo(BaseModel):
    id: int
    text: str
    completed: bool


app = FastAPI(title = "REST API using FastAPI PostgreSQL Async EndPoints")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", status_code=status.HTTP_200_OK)
async def show_hello_world():
    return { "message": "hello world"}


@app.get("/todos/", response_model=List[Todo], status_code=status.HTTP_200_OK)
async def read_todos(skip: int = 0, take: int = 20):
    query = todos.select().offset(skip).limit(take)
    return await database.fetch_all(query)


@app.get("/todos/{todo_id}/", response_model=Todo, status_code=status.HTTP_200_OK)
async def read_todos(todo_id: int):
    query = todos.select().where(todos.c.id == todo_id)
    return await database.fetch_one(query)


@app.post("/todos/", response_model=Todo, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoInput):
    query = todos.insert().values(text=todo.text, completed=todo.completed)
    last_record_id = await database.execute(query)
    return {**todo.dict(), "id": last_record_id}


@app.put("/todos/{todo_id}/", response_model=Todo, status_code=status.HTTP_200_OK)
async def update_todo(todo_id: int, payload: TodoInput):
    query = todos.update().where(todos.c.id == todo_id).values(text=payload.text, completed=payload.completed)
    await database.execute(query)
    return {**payload.dict(), "id": todo_id}


@app.delete("/todos/{todo_id}/", status_code=status.HTTP_200_OK)
async def delete_todo(todo_id: int):
    query = todos.delete().where(todos.c.id == todo_id)
    await database.execute(query)
    return {"message": "Todo with id: {} deleted successfully!".format(todo_id)}


