from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
import uvicorn
from datetime import datetime
app = FastAPI()

class UserSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=50)
    email: str
    role: str = Field(..., max_length=20)

class TasksSchema(BaseModel):
    id: int
    title: str = Field(..., max_length=50)
    description: str = Field(..., max_length=500)
    status: str = Field(max_length=50, default='in progress') #in progress or completed
    date: str

users = [
    {'id': 0, 'name': 'Serhii', 'email': 'bigar@gmail.com', 'role': 'admin'},
    {'id': 1, 'name': 'Viktor', 'email': 'vik@gmail.com', 'role': 'user'},
    {'id': 2, 'name': 'Ivan', 'email': 'iivi@gmail.com', 'role': 'user'},
    {'id': 3, 'name': 'Sam', 'email': 'sam@gmail.com', 'role': 'moderator'}
]
tasks = [
    {'id': 1, 'title': 'Налаштувати базу даних для Віктора',
     'description': 'Через недбале використання ресурсів'
    'сталась атака ботів і тепер база даних підвисає',
     'status': 'in progress', 'date': '16-04-2024 18:03'},
    {'id': 2, 'title': 'Полагодити ноутбук в основному офісі',
     'description': 'Через надмірне використання ноут він згорів і тепер не включається',
     'status': 'completed', 'date': '18-08-2022 09:44'},
    {'id': 3, 'title': 'Полагодити камери на магазині',
     'description': 'Через надмірне використання камери не працюють і не видно нічого',
     'status': 'completed', 'date': '18-12-2023 10:13'},
    {'id': 4, 'title': 'Купити клавіатуру для 4 магазинів',
     'description': 'Через відкриття нових магазинів треба купити нові',
     'status': 'completed', 'date': '10-01-2021 18:05'}
]

@app.get('/users', summary='Всі користувачі', tags=['Користувачі'])
def all_users():
    return users

@app.get('/user/{id}', summary='Отримати користувача', tags=['Користувачі'])
def get_user(id: int):
    for element in users:
        if element['id'] == id:
            return element

@app.get('/users/{role}', summary='Сортувати користувачів за роллю', tags=['Користувачі'])
def get_user_role(role: str):
    matching_users = []
    for user in users:
        if user['role'] == role:
            matching_users.append(user)
    return matching_users

@app.post('/users/add', summary='Додати користувача', tags=['Користувачі'])
def add_user(schema: UserSchema):
    new_user = users.append(schema.model_dump())
    return {'message': 'user added', 'new_user': new_user}

@app.put('/user/repair/{id}', summary='Редагувати користувача', tags=['Користувачі'])
def repair_user(id: int, schema: UserSchema):
    for element in users:
        if element['id'] == id:
            element['name'] = schema.name
            element['email'] = schema.email
            element['role'] = schema.role
            return {'message': 'user was repaired'}

@app.delete('/user/delete/{id}', summary='Видалити користувача', tags=['Користувачі'])
def delete_user(id: int):
    for element in users:
        if element['id'] == id:
            users.remove(element)
            return {'message': 'user deleted'}



@app.get('/tasks', summary='Завдання посортовані за датою', tags=['Завдання'])
def all_tasks():
    sorted_tasks = sorted(tasks, key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y %H:%M'))
    return sorted_tasks

@app.get('/task/{id}', summary='Отримати завдання', tags=['Завдання'])
def get_task(id: int):
    for element in tasks:
        if element['id'] == id:
            return element

@app.post('/task/add', summary='Створити завдання', tags=['Завдання'])
def add_task(schema: TasksSchema):
    schema.date = datetime.now().strftime("%Y-%m-%d %H:%M")
    tasks.append(schema.model_dump())
    return {'message': 'task added'}

@app.put('/task/repair/{id}', summary='Коригувати статус завдання', tags=['Завдання'])
def repair_task_status(schema: TasksSchema, id: int):
    for element in tasks:
        if element['id'] == id:
            element['status'] = schema.status
            return {'message': 'task repaired'}

@app.delete('/tasks/delete/{id}', summary='Видалити завдання', tags=['Завдання'])
def delete_task(id: int):
    for element in tasks:
        if element['id'] == id:
            tasks.remove(element)
            return {'message': 'task deleted'}

@app.get('/tasks/{status}', summary='Сортувати завдання за статусом', tags=['Завдання'])
def get_task_status(status: str):
    status_tasks = []
    for element in tasks:
        if element['status'] == status:
            status_tasks.append(element)
    return status_tasks

@app.get('/task/get/{title}', summary='Пошук завдання за полем title', tags=['Завдання'])
def get_title_task(title: str):
    search_title = []
    for element in tasks:
        if title in element['title'].lower():
            search_title.append(element)
    return search_title



