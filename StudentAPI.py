from fastapi import FastAPI, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey, LargeBinary
from pydantic import BaseModel, Field, field_validator
import re

DATABASE_URL = "sqlite+aiosqlite:///./database.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
Base = declarative_base()

metadata = MetaData()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    role = Column(String(20))
    password = Column(String(50))

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    role = Column(String(20))
    password = Column(String(50))

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), unique=True)
    teacher_name = Column(String, ForeignKey("teachers.name"))
    matherials = Column(LargeBinary)

class StudentCourse(Base):
    __tablename__ = "student_course"
    course_title = Column(String(50), ForeignKey("courses.title"), primary_key=True)
    student_name = Column(String(50), ForeignKey("students.name"), primary_key=True)
    first_score = Column(Integer)
    second_score = Column(Integer)

# Ініціалізація бази даних
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

class UserCreateSchema(BaseModel):
    name: str = Field(..., max_length=50)
    role: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)

    @field_validator("name")
    def check_name_is_string(cls, value):
        if not re.match("^[A-Za-zА-Яа-яІіЇїЄєҐґ0-9\s]+$", value):
            raise ValueError("Ім'я повинно містити лише літери та пробіли")
        return value

async def authenticate_student(name: str, password: str, session: AsyncSession):
    result = await session.execute(
        Student.__table__.select().where(Student.name == name)
    )
    student = result.fetchone()
    if student and student.password == password:
        return student
    raise HTTPException(status_code=403, detail="Invalid username or password")

async def authenticate_teacher(name: str, password: str, session: AsyncSession):
    result = await session.execute(
        Teacher.__table__.select().where(Teacher.name == name)
    )
    teacher = result.fetchone()
    if teacher and teacher.password == password:
        return teacher
    raise HTTPException(status_code=403, detail="Invalid username or password")

@app.on_event("startup")
async def startup():
    await init_db()

@app.post("/create/user/", summary="Створити користувача", tags=["Користувачі"])
async def create_user(user: UserCreateSchema):
    async with async_session() as session:
        async with session.begin():
            if user.role == "student":
                student = Student(name=user.name, role=user.role, password=user.password)
                session.add(student)
                await session.commit()
                return {"message": f"Студент {user.name} успішно створений"}
            elif user.role == "teacher":
                teacher = Teacher(name=user.name, role=user.role, password=user.password)
                session.add(teacher)
                await session.commit()
                return {"message": f"Викладач {user.name} успішно створений"}
            else:
                return {"message": "Виберіть правильну роль: student або teacher"}

@app.post("/create/course", summary="Створити курс", tags=["Курси"])
async def create_course(name: str, password: str, title: str, matherials: UploadFile = File(...)):
    async with async_session() as session:
        teacher = await authenticate_teacher(name, password, session)
        matherial = await matherials.read()
        course = Course(title=title, teacher_name=teacher.name, matherials=matherial)
        session.add(course)
        await session.commit()
        return {"message": "Курс успішно створено"}

@app.post("/sign/courses", summary="Записатись на курс", tags=["Курси"])
async def sign_course(name: str, password: str, course_title: str):
    async with async_session() as session:
        student = await authenticate_student(name, password, session)
        result = await session.execute(
            Course.__table__.select().where(Course.title == course_title)
        )
        course = result.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="Курс не знайдено")
        student_query = await session.execute(
            StudentCourse.__table__.select().where(
                StudentCourse.course_title == course_title
            )
        )
        student_records = student_query.fetchall()
        student_names = [record["student_name"] for record in student_records]
        if len(student_names) >= 10:
            raise HTTPException(status_code=400, detail="Курс переповнений")
        elif name in student_names:
            raise HTTPException(status_code=400, detail="Студент вже записаний на курс")
        else:
            student_course = StudentCourse(course_title=course_title, student_name=name)
            session.add(student_course)
            await session.commit()
            return {"message": f"Студент {name} успішно приєднався до {course_title}"}

@app.get("/course/students", summary="Курси із студентами", tags=["Курси"])
async def get_courses_with_students():
    async with async_session() as session:
        result = []
        courses_list = await session.execute(Course.__table__.select())
        for course in courses_list:
            student_query = await session.execute(
                StudentCourse.__table__.select().where(
                    StudentCourse.course_title == course.title
                )
            )
            student_names = [record["student_name"] for record in student_query.fetchall()]
            result.append({
                "course_title": course.title,
                "course_teacher": course.teacher_name,
                "students": student_names
            })
        return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
























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
4. Валідація:
Курс не може бути створений без викладача.
Дата початку курсу повинна бути у майбутньому.
Студент не може зареєструватися на один і той самий курс двічі.
5. Бонус:
Реалізувати завантаження та зберігання PDF-матеріалів для курсів.
Інтеграція з базою даних через SQLAlchemy (або будь-який інший ORM).
Додати WebSocket для реального часу (наприклад, чат студентів і викладача для курсу).'''