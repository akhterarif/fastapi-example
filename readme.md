Welcome all of you in a journey where we will create a CRUD API application using `FastAPI`.

Before going in deep discussion I am assuming that you have already installed `python` and `virtualenv` in your system. Here you can find some guideline for [python](https://www.python.org/downloads/) and [virtualenv](https://realpython.com/python-virtual-environments-a-primer/). 

Please do activate the virtualenv for this application before going to develop.

So let's start to build the application.

### Dependencies
As we are going to build an CRUD app, so we will need some packages to be pre-installed. We can install them by using `pip`.

```pip install fastapi uvicorn psycopg2-binary database[postgresql]```

Lets breakdown what and why we have installed those packages
* [fastapi](https://fastapi.tiangolo.com/) is our web-framework, on which we will be building our application.
* [uvicorn](https://fastapi.tiangolo.com/deployment/manually/) is an ASGI server where we will our `fastapi` app.
* [database[postgresql]](https://github.com/encode/databases) used to install the required database drivers for application. Here we are using it to install postgresql.

### Writing the one and only `Hello world` with `fastapi` ###
Now we are going to show the world's unique approach to run an application for the first time. I mean writng an app which we will show `hello world.`
Now in the project folder(in my case `fastapi_project`) we will make a file named `main.py` and we will write the following code-snippet
```python
from fastapi import FastAPI, status

app = FastAPI(title = "REST API using FastAPI PostgreSQL Async EndPoints")

@app.get("/", status_code = status.HTTP_200_OK)
async def show_hello_world():
    return { "message": "hello world"}
```
Let's see what we have written in the code.
At first, we have imported `FastAPI` and `status`.

Then we have initiated the object of `FastAPI` class for our app.

In this line 
```
@app.get("/", status_code = status.HTTP_200_OK)
```
then we have written a route using the decorator through which we will request the app.

Then this asynchronous function will run, when we are requesting through the previously requested route. 
```python
async def show_hello_world():
    return { "message": "hello world"}
```
Then we will run the application 
```shell
uvicorn main:app --reload
```
in this command we are telling `uvicorn` to run the `main.py` file's `app` object. 


By default the application will run in `http://localhost:8000/` 
and it will show something that no one has ever seen
```json
{
  "message": "hello world"
}
```

Now we will create a todo app.
### Import references
To start with, in the main.py file add the following references.
```python
from typing import List
import databases
import sqlalchemy
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import urllib
```

### Configure Database FastAPI PostgreSQL Connection String
As we have a PostgreSQL server then are adding the following lines to `main.py` and configure the values accordingly for environment variables `db_username`, `db_password`, `host_server`, `db_server_port`, `database_name`.
```python
host_server = os.environ.get('host_server', 'localhost')
db_server_port = urllib.parse.quote_plus(str(os.environ.get('db_server_port', '5432')))
database_name = os.environ.get('database_name', 'fastapi')
db_username = urllib.parse.quote_plus(str(os.environ.get('db_username', 'postgres')))
db_password = urllib.parse.quote_plus(str(os.environ.get('db_password', 'secret')))
ssl_mode = urllib.parse.quote_plus(str(os.environ.get('ssl_mode','prefer')))
DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}?sslmode={}'.format(db_username, db_password, host_server, db_server_port, database_name, ssl_mode)
```

### Creating database instance
Once we have `DATABASE_URL` url built, create instance of database by adding the following line to main.py.
```python
database = databases.Database(DATABASE_URL)
```
### Create SQL Alchemy model
We will create a table named `todos`. The purpose is to store detail of todo in text column and its status in completed column. We will use sqlalchemy to define the `todos` table that resembles the relational database schema in the form of Python code. Add the following lines to define schema for `todos` table.

```python
metadata = sqlalchemy.MetaData()

todos = sqlalchemy.Table(
    "todos",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("text", sqlalchemy.String),
    sqlalchemy.Column("completed", sqlalchemy.Boolean),
)
```
### Create Engine
To create postgresql engine. we will add the following lines in our main.py file
```python
engine = sqlalchemy.create_engine(
    DATABASE_URL, pool_size=3, max_overflow=0
)
metadata.create_all(engine)
```

### Create Models using Pydantic
We will add the following models to main.py. 
These are models built with Pydantic’s BaseModel. 
Pydantic models help us define request payload models and response models in Python Class object notation.
FastAPI also uses these models in its auto generated OpenAPI Specs (Swagger) to indicate response and request payload models.
```python
class TodoInput(BaseModel):
    text: str
    completed: bool


class Todo(BaseModel):
    id: int
    text: str
    completed: bool
```
TodoInput is the model in its JSON form used as payload to Create or Update todo endpoints. Todo is the model in its JSON form will be used as response to retrieve todos collection or a single todo given its id.

The JSON notation of these models will look something similar as mentioned below.
`TodoInput` JSON format will look like as follows
```json
{
    "text": "string",
    "completed": true
}
```
`Todo` JSON format will look like as follows
```json
{
    "id": 0,
    "text": "string",
    "completed": true
}
```
### Add CORS to FastAPI
In order for our REST API endpoints to be consumed in client applications such as Vue, React, Angular or any other Web applications that are running on other domains, we should tell our FastAPI to allow requests from the external callers to the endpoints of this FastAPI application. 
We can enable CORS (Cross Origin Resource Sharing) either at application level or at specific endpoint level. But in this situation we will add the following lines to `main.py` to enable CORS at the application level by allowing requests from all origins specified by `allow_origins=[*]`.
```python
app = FastAPI(title="REST API using FastAPI PostgreSQL Async EndPoints")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```
`allow_origins=[*]` is not recommended for Production purposes. It is recommended to have specified list of origins such as mentioned below

### Application Startup & Shutdown Events
FastAPI can be run on multiple worker process with the help of Gunicorn server with the help of uvicorn.workers.UvicornWorker worker class. Every worker process starts its instance of FastAPI application on its own Process Id. 
In order to ensure every instance of application communicates to the database, we will connect and disconnect to the database instance in the FastAPI events  startup and shutdown respectively. So adding the following code to `main.py` to do that.
```python
@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
```
### Creating a Todo using HTTP POST request
We will use HTTP POST request available as `post` method of FastAPI’s instance variable app to create/insert a new todo in our todos table.
The status code on successful creation of `todo` will be `201`. This can be seen as an argument `status_code` passed to post method which accepts integer value held by `status.HTTP_201_CREATED`.
By adding the following code to `main.py` to add a `todo` to the table.
```python
@app.post("/todos/", response_model=Todo, status_code = status.HTTP_201_CREATED)
async def create_todo(todo: TodoInput):
    query = todos.insert().values(text=todo.text, completed=todo.completed)
    last_record_id = await database.execute(query)
    return {**todo.dict(), "id": last_record_id}
```
### Update Note using HTTP PUT request
We will use HTTP PUT request available as put method of FastAPI’s instance variable app to update/modify an existing `todo` in our `todos` table. Add the following code to main.py to modify a todo from the todos table.
```python
@app.put("/todos/{todo_id}/", response_model=Todo, status_code=status.HTTP_200_OK)
async def update_todo(todo_id: int, payload: TodoInput):
    query = todos.update().where(todos.c.id == todo_id).values(text=payload.text, completed=payload.completed)
    await database.execute(query)
    return {**payload.dict(), "id": todo_id}
```

### Get Paginated List of Notes using HTTP GET request
We will use HTTP GET request available as get method of FastAPI’s instance variable app to retrieve paginated collection of todos available in our todos table. Add the following code to main.py to get list of todos from the table.
```python
@app.get("/todos/", response_model=List[Todo], status_code=status.HTTP_200_OK)
async def read_todos(skip: int = 0, take: int = 20):
    query = todos.select().offset(skip).limit(take)
    return await database.fetch_all(query)
```
Here the skip and take arguments will define how may todos to be skipped and how many todos to be returned to the collection respectively. 
If we have a total of 13 todos in your database and if we provide skip a value of 10 and take a value of 20, then only 3 todos will be returned. 
skip will ignore the value based on the identity of the collection starting from old to new.

### Get single Note Given its Id using HTTP GET request
We will again use the HTTP GET request available as get method of FastAPI’s instance variable app to retrieve a single `todo` identified by provided 
id in the request as a `todo_id` query parameter. Following code is used to `main.py` to get a todo given its id.
```python
@app.get("/todos/{todo_id}/", response_model=Todo, status_code=status.HTTP_200_OK)
async def read_todos(todo_id: int):
    query = todos.select().where(todos.c.id == todo_id)
    return await database.fetch_one(query)
```
### Delete single Note Given its Id using HTTP DELETE request
We will use HTTP DELETE request available as delete method of FastAPI’s instance variable app to 
permanently delete an existing `todo` in our `todos` table. Add the following code to `main.py` to wipe off the `todo` permanently given `todo_id` as query parameter.
```python
@app.delete("/todos/{todo_id}/", status_code=status.HTTP_200_OK)
async def delete_todo(todo_id: int):
    query = todos.delete().where(todos.c.id == todo_id)
    await database.execute(query)
    return {"message": "Todo with id: {} deleted successfully!".format(todo_id)}
```

### Run the FastAPI app
Save changes to `main.py` and run the following command in the terminal to spin up the FastAPI app.
```shell
uvicorn main:app --reload
```

We can see the documentation and request and response body by going `http://localhost:8000/docs`.
#### Request body for POST and PUT request will be as follows
```json
{
  "text": "string",
  "completed": true
}
```
#### Response body for List of Todos
```json
[
  {
    "id": 0,
    "text": "string",
    "completed": true
  }
]
```
#### Response body for Single of Todos
```json
{
    "id": 0,
    "text": "string",
    "completed": true
}
```

### Conclusion
This is how we can make a CRUD App with FastAPI. Now we have written all the codes in one `main.py` file, which is not convention. 
For bigger application there are some reccomendation will be found [here](https://fastapi.tiangolo.com/tutorial/bigger-applications/) 

Any suggestion regarding the project and blog is warmly welcome. 

See you next time. 