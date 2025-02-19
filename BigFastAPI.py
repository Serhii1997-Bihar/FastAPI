from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr, field_validator
import uvicorn
from datetime import datetime
from typing import Union
app = FastAPI()

employers = [
    {'id': 0, 'username': 'Serhii1997', 'role': 'admin', 'password': 'hardwell25'},
    {'id': 1, 'username': 'Ivan1991', 'role': 'user', 'password': 'ivan25'},
    {'id': 2, 'username': 'Misha1990', 'role': 'user', 'password': 'misha25'},
    {'id': 3, 'username': 'Lana1994', 'role': 'moderator', 'password': 'lana25'}
]
tasks = [{'project_id': 0, 'project_tasks': [
    {'task_id': 0, 'info': 'Дизайн', 'status': 'completed'},{'task_id': 1, 'info': 'Верстка', 'status': 'in progress'}
    ]}]
projects = [
    {'user': 'Serhii1997', 'id': 0, 'title': 'Сайт для магазину сигарет', 'deadline': '25-01-2025', 'tasks': tasks[0],
     'total_tasks': 2},
]

class TaskItem(BaseModel):
    task_id: int
    info: str
    status: str
class TasksSchema(BaseModel):
    project_id: int
    project_task: list[TaskItem]
class ProjectSchema(BaseModel):
    user: str
    id: int
    title: str = Field(..., max_length=50)
    deadline: str = Field(..., description="Дата завершення в форматі 'YYYY-MM-DD'")
    tasks: dict
    total_tasks: int = Field(default=0)

    @field_validator('deadline')
    def validate_deadline(cls, value):
        try:
            deadline_date = datetime.strptime(value, "%d-%m-%Y")
        except ValueError:
            raise ValueError("Дата повинна бути у форматі 'DD-MM-YYYY'.")
        today = datetime.today()
        if deadline_date <= today:
            raise ValueError("Дата завершення повинна бути в майбутньому.")
        return value

def authenticated(username, password):
    for element in employers:
        if element['username'] == username and element['password'] == password:
            return True
    return False

@app.get('/projects', summary='Всі проєкти', tags=['Проєкти'])
def all_projects():
    for project in projects:
        for task in tasks:
            if task['project_id'] == project['id']:
                project['tasks'] = task
                project['total_tasks'] = len(task['project_tasks'])
    return projects

@app.post('/create/project/{username}/{password}', summary='Створення проекту', tags=['Проєкти'])
def create_project(username: str, password: str, project: ProjectSchema):
    if authenticated(username, password):
        pro_id = len(projects)
        project.id = pro_id
        project.user = username
        initial_tasks = {'project_id': pro_id, 'project_tasks': []}
        tasks.append(initial_tasks)
        project.tasks = initial_tasks
        projects.append(project.model_dump())
        return {'message': 'Project created', 'project': project.model_dump()}
    raise HTTPException(status_code=401, detail="Не правильний пароль або ім'я")

@app.post('/create/task/{username}/{password}', summary='Створення завдання', tags=['Проєкти'])
def create_task(username: str, password: str, schemaTask: TaskItem, id: int):
    if authenticated(username, password):
        for project in projects:
            if project['id'] == id and project['user'] == username:
                for task in tasks:
                    if task['project_id'] == id:
                        schemaTask.task_id = len(task['project_tasks']) + 1
                        task['project_tasks'].append({
                            'task_id': schemaTask.task_id,
                            'info': schemaTask.info,
                            'status': 'not started'
                            })
                        return {'message': 'Task created', 'task': task}
    raise HTTPException(status_code=401, detail="Не правильний пароль або ім'я")

@app.put('/change/task/{username}/{password}', summary='Змінити статус завдання', tags=['Проєкти'])
def change_task(username: str, password: str, schemaTask: TaskItem, id: int):
    if authenticated(username, password):
        for project in projects:
            if project['id'] == id and project['user'] == username:
                for task in tasks:
                    if task['project_id'] == id:
                        for project_task in task['project_tasks']:
                            if project_task['task_id'] == schemaTask.task_id:
                                project_task['status'] = schemaTask.status
                                return {'message': 'task updated', 'task': project_task}
                raise HTTPException(status_code=404, detail="Task not found")
    raise HTTPException(status_code=401, detail="Не правильний пароль або ім'я")

@app.delete('/delete/task/{username}/{password}', summary='Видалити завдання', tags=['Проєкти'])
def delete_task(username: str, password: str, id: int, schemaTask: TaskItem, task_id: int):
    if authenticated(username, password):
        for project in projects:
            if project['id'] == id and project['user'] == username:
                for el in tasks:
                    if el['project_id'] == id:
                        for index, project_task in enumerate(el['project_tasks']):
                            if project_task['task_id'] == task_id:
                                del el['project_tasks'][index]
                                return {'message': 'task deleted'}
    raise HTTPException(status_code=401, detail="Не правильний пароль або ім'я")

@app.delete('/delete/project/{username}/{password}', summary='Видалити проєкт', tags=['Проєкти'])
def delete_project(username: str, password: str, id: int):
    if authenticated(username, password):
        for user in employers:
            if user['username'] == username and user['role'] == 'admin':
                for index, project in enumerate(projects):
                    if project['id'] == id:
                        del projects[index]
                        return {'message': 'Project deleted'}
            raise HTTPException(status_code=401, detail="Ви не можете видаляти проєкти")
    raise HTTPException(status_code=401, detail="Не правильний пароль або ім'я")

@app.get('/get/project/task', summary='Переглянути завдання до проєкту', tags=['Проєкти'])
def get_tasks(project_id: int):
    for task in tasks:
        if task['project_id'] == project_id:
            sorted_tasks = sorted(task['project_tasks'], key=lambda t: t['status'])
            return sorted_tasks
    raise HTTPException(status_code=404, detail="Проєкт не знайдено")

@app.get('/get/project/', summary='Переглянути проєкт', tags=['Проєкти'])
def get_project(id: int):
    for project in projects:
        if project['id'] == id:
            for task in tasks:
                if task['project_id'] == id:
                    project['tasks'] = task
                    project['total_tasks'] = len(task['project_tasks'])
            return project
    raise HTTPException(status_code=404, detail="Task not found")

























if __name__ == '__main__':
    uvicorn.run(app=app, host='127.0.0.1', port=4000)

"""
Авторизація:
Додай просту перевірку ролі користувача через параметр role.
Лише адміністратори можуть видаляти проєкти чи завдання.
Завдання: Створити API для керування проєктами та їхніми завданнями
Основна функціональність:
Проєкти:
Користувачі можуть створювати проєкти.
Кожен проєкт має унікальний id, назву, дедлайн, та список завдань.
Завдання:
Кожне завдання прив’язане до конкретного проєкту.
Завдання можна створювати, оновлювати, видаляти або переглядати.
Завдання мають статус (in progress, completed).
Фільтрація:
Фільтрувати завдання за статусом у конкретному проєкті.
Лише адміністратори можуть видаляти проєкти та завдання.
Завдання:
Ендпоінти для проєктів:
Створити проєкт.
Переглядати всі проєкти.
Переглядати конкретний проєкт (з його завданнями).
Видаляти проєкт (тільки адміністратор).
Оновлювати дедлайн проєкту.

Бонус:
Логіка дедлайну:
Якщо дедлайн проєкту минув, завдання у проєкті не можна змінювати або додавати нові.
Перевірка даних:
Додай валідацію, щоб дедлайн проєкту не був у минулому під час створення.
Кількість завдань:
Додай до кожного проєкту поле total_tasks, яке автоматично рахує кількість завдань.
"""

