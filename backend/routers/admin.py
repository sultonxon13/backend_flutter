import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Teacher, Student
from schemas import TeacherCreate, StudentCreate, VerificationCode
from crud import create_verification_code, update_user_role, verify_code, generate_verification_code
from auth import hash_password

router = APIRouter()

@router.post("/register_teacher/")
def register_teacher(
    teacher: TeacherCreate,
    phone_number: str,
    password: str,
    db: Session = Depends(get_db),
):
    verification_code = generate_verification_code()
    hashed_password = hash_password(password)
    new_user = User(
        username=teacher.username,
        fullname=teacher.fullname,
        phone_number=phone_number,
        hashed_password=hashed_password,
        is_active=False,
        verification_code=verification_code,
        role="pending"
    )
    db.add(new_user)
    db.commit()
    
    create_verification_code(db, phone_number, verification_code)
    return {"msg": "Verification code sent", "code": verification_code}

@router.post("/verify_teacher/")
def verify_teacher(
    phone_number: str,
    verification_code: str,
    db: Session = Depends(get_db)
):
    user = verify_code(db, phone_number, verification_code)
    if user:
        # Foydalanuvchining rolini yangilash
        updated_user = update_user_role(db, user.id, "teacher")
        
        # Teacher'ni qo'shish
        new_teacher = Teacher(
            user_id=updated_user.id,
            name=updated_user.fullname,
            subject="Not assigned"  # Bu joyni keyinroq to'ldiring
        )
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)
        
        return {"msg": "Teacher added successfully", "teacher_id": new_teacher.id}
    
    raise HTTPException(status_code=400, detail="Invalid verification code")

@router.post("/add_student/")
def add_student(
    student: StudentCreate,
    passport_image: str,
    db: Session = Depends(get_db)
):
    user_id = random.randint(1000, 9999)  # Misol uchun, avtomatik ID generatsiyasi
    new_user = User(
        id=user_id,
        username=student.username,
        hashed_password="hashed_dummy_password",
        role="student",
        fullname=student.fullname,
        phone_number=student.phone_number,
        passport_image=passport_image
    )
    db.add(new_user)
    db.commit()

    return {"msg": "Student added successfully", "student_id": new_user.id}
