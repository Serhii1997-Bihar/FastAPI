from fastapi import FastAPI, HTTPException
import uvicorn
from databases import Database
from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey, create_engine

DATABASE_URL = "sqlite:///./database.db"

database = Database(DATABASE_URL)
metadata = MetaData()

students = Table(
    "students",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String(50), unique=True),
    Column("role", String(20)),
    Column("password", String(50))
)

teachers = Table(
    "teachers",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String(50), unique=True),
    Column("role", String(20)),
    Column("password", String(50))
)

courses = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("title", String(50), unique=True),
    Column("teacher_name", String, ForeignKey("teachers.name")),
)

student_course = Table(
    "student_course",
    metadata,
    Column("course_title", String(50), ForeignKey("courses.title"), primary_key=True),
    Column("student_name", String(50), ForeignKey("students.name"), primary_key=True),
)

engine = create_engine(DATABASE_URL)
metadata.create_all(engine)
app = FastAPI()


async def authenticate_student(name: str, password: str):
    query = students.select().where(students.c.name == name)
    student = await database.fetch_one(query)
    if student['password'] == password:
        return student
    raise HTTPException(status_code=403, detail="Invalid username or password")
async def authenticate_teacher(name: str, password: str):
    query = teachers.select().where(teachers.c.name == name)
    teacher = await database.fetch_one(query)
    if teacher['password'] == password:
        return teacher
    raise HTTPException(status_code=403, detail="Invalid username or password")


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/create/user/", summary='Створити користувача', tags=['Користувачі'])
async def create_user(name: str, role: str, password: str):
    if role == 'student':
        query = students.insert().values(name=name, role=role, password=password)
        last_record_id = await database.execute(query)
    else:
        query = teachers.insert().values(name=name, role=role, password=password)
        last_record_id = await database.execute(query)
    return {"id": last_record_id, "name": name, "role": role}

@app.get("/users/", summary='Отримати користувачів', tags=['Користувачі'])
async def get_users(role: str):
    if role == 'student':
        query = students.select()
        return await database.fetch_all(query)
    elif role == 'teacher':
        query = teachers.select()
        return await database.fetch_all(query)

@app.get("/users/{user_id}", summary='Отримати користувача', tags=['Користувачі'])
async def get_user(user_id: int, role: str):
    if role == 'student':
        query_students = students.select().where(students.c.id == user_id)
        student = await database.fetch_one(query_students)
        if student is None:
            raise HTTPException(status_code=404, detail="Студента не знайдено")
        return student
    elif role == 'teacher':
        query_teachers = teachers.select().where(teachers.c.id == user_id)
        teacher = await database.fetch_one(query_teachers)
        if teachers is None:
            raise HTTPException(status_code=404, detail="Вчителя не знайдено")
        return teachers


@app.post('/create/course', summary='Створити курс', tags=['Курси'])
async def create_course(name: str, password: str, title: str):
    teacher = await authenticate_teacher(name, password)
    query = courses.insert().values(title=title, teacher_name=teacher['name'])
    await database.execute(query)
    return {'message': 'Курс успішно створено'}

@app.post('/sign/courses', summary='Записатись на курс', tags=['Курси'])
async def sign_course(name: str, password: str, course_title: str):
    student = await authenticate_student(name, password)
    query_course = courses.select().where(courses.c.title == course_title)
    course = await database.fetch_one(query_course)
    if not course:
        raise HTTPException(status_code=404, detail="Курс не знайдено")
    student_query = student_course.select().where(student_course.c.course_title == course_title)
    student_records = await database.fetch_all(student_query)
    student_names = [record["student_name"] for record in student_records]
    if len(student_names) >= 10:
        raise HTTPException(status_code=404, detail="Курс переповнений")
    elif name in student_names:
        raise HTTPException(status_code=400, detail="Студент вже записаний на курс")
    else:
        query = student_course.insert().values(course_title=course_title, student_name=student['name'])
        await database.execute(query)
        return {'message': f'Студент {name} успішно приєднався до {course_title}'}

@app.get('/course/students', summary='Курси із студентами', tags=['Курси'])
async def get_courses_with_students():
    course_query = courses.select()
    courses_list = await database.fetch_all(course_query)
    if not courses_list:
        raise HTTPException(status_code=404, detail="Курс не знайдено")
    result = []
    for course in courses_list:
        course_title = course["title"]
        course_teacher = course['teacher_name']
        student_query = student_course.select().where(student_course.c.course_title == course_title)
        student_records = await database.fetch_all(student_query)
        student_names = [record["student_name"] for record in student_records]
        result.append({
            "course_title": course_title,
            "course_teacher": course_teacher,
            "students": student_names})
    return result










if __name__ == '__main__':
    uvicorn.run(app=app, host='127.0.0.1', port=4000)

'''Функціональність:
1. Користувачі:
Реєстрація та авторизація.
Типи користувачів:
student: може реєструватися на курси, переглядати свої оцінки та матеріали курсу.
teacher: може створювати курси, додавати матеріали, виставляти оцінки.
admin: управляє всіма користувачами та курсами.
2. Курси:
Курси мають:
id, назву, опис, викладача, список матеріалів, список студентів.
Оцінки студентів (за темами курсу).
Студенти можуть реєструватися на курс (але тільки якщо курс ще відкритий для реєстрації).
Викладач може:
Додавати матеріали курсу.
Виставляти оцінки студентам за певні теми курсу.
Адміністратор може видаляти курси.
3. Фільтрація та сортування:
Курси можна фільтрувати за викладачем, темою або статусом (відкритий/закритий для реєстрації).
Оцінки студентів можна фільтрувати за курсом та сортувати за балами.
4. Валідація:
Курс не може бути створений без викладача.
Дата початку курсу повинна бути у майбутньому.
Студент не може зареєструватися на один і той самий курс двічі.
5. Бонус:
Реалізувати завантаження та зберігання PDF-матеріалів для курсів.
Інтеграція з базою даних через SQLAlchemy (або будь-який інший ORM).
Додати WebSocket для реального часу (наприклад, чат студентів і викладача для курсу).'''