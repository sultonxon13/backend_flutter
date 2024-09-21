# crud.py
import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import User, Teacher, Student, Task, Group, GroupMembership, Homework, Video
from schemas import UserCreate, TeacherCreate, StudentCreate, TaskCreate, GroupCreate, HomeworkCreate, VideoCreate
from utils import hash_password
import random
import string

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_user(db: Session, user: UserCreate):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = hash_password("default_password")
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role="student",
        fullname=user.fullname,
        phone_number=user.phone_number
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_teacher(db: Session, teacher: TeacherCreate) -> Teacher:
    hashed_password = hash_password("default_password")
    db_user = create_user(db, teacher)
    db_teacher = Teacher(
        user_id=db_user.id,
        name=teacher.fullname,
        subject=teacher.subject
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

def create_student(db: Session, student: StudentCreate):
    db_student = Student(
        user_id=student.user_id,
        teacher_id=student.teacher_id,
        attendance=student.attendance,
        rating=student.rating
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def create_task(db: Session, task: TaskCreate):
    db_task = Task(
        teacher_id=task.teacher_id,
        student_id=task.student_id,
        task_description=task.task_description,
        grade=task.grade,
        video_path=task.video_path
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def create_group(db: Session, group: GroupCreate, creator_id: int):
    db_group = Group(
        name=group.name,
        description=group.description,
        created_by=creator_id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def add_member(db: Session, group_id: int, student_id: int):
    db_membership = GroupMembership(group_id=group_id, student_id=student_id)
    db.add(db_membership)
    db.commit()
    return db_membership

def create_homework(db: Session, homework: HomeworkCreate):
    db_homework = Homework(**homework.dict())
    db.add(db_homework)
    db.commit()
    db.refresh(db_homework)
    return db_homework

def create_video(db: Session, video: VideoCreate):
    db_video = Video(**video.dict())
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def get_group_members_count(db: Session, group_id: int):
    return db.query(GroupMembership).filter(GroupMembership.group_id == group_id).count()

def generate_verification_code(length: int = 6) -> str:
    characters = string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_verification_code(db: Session, phone_number: str, verification_code: str):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user:
        user.verification_code = verification_code
        db.commit()
        db.refresh(user)
    return user

def verify_code(db: Session, phone_number: str, code: str):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user and user.verification_code == code:
        user.is_active = True
        user.verification_code = None
        db.commit()
        db.refresh(user)
        return user
    return None

def update_user_role(db: Session, user_id: int, role: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.role = role
        db.commit()
        db.refresh(user)
    return user
