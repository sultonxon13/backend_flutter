import shutil
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from auth import get_current_user, hash_password
from database import get_db
from models import GroupMembership, User, Student, Task
from schemas import StudentCreate, VerificationCode
import random
from datetime import datetime
router = APIRouter()

# SMS yoki email orqali tasdiqlash kodi yuborish
def send_verification_code(phone_number: str, code: str):
    print(f"Verification code {code} sent to {phone_number}")

# Student yaratish
@router.post("/register_student/")
async def register_student(
    fullname: str,
    phone_number: str,
    username: str,
    password: str,  # Parolni qabul qilamiz
    passport_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Username allaqachon mavjudligini tekshirish
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username allaqachon ro'yxatdan o'tgan")

    # Parolni hash qilish
    hashed_password = hash_password(password)

    # Tasdiqlash kodini yaratish
    verification_code = str(random.randint(100000, 999999))
    send_verification_code(phone_number, verification_code)

    # Passport rasmini saqlash
    passport_image_path = f"passport_images/{passport_image.filename}"
    with open(passport_image_path, "wb") as buffer:
        shutil.copyfileobj(passport_image.file, buffer)

    # Yangi foydalanuvchini yaratish
    new_user = User(
        username=username,
        fullname=fullname,
        phone_number=phone_number,
        hashed_password=hashed_password,  # Hashlangan parolni saqlash
        passport_image=passport_image_path,
        is_active=False,
        verification_code=verification_code
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"msg": "Tasdiqlash kodi yuborildi. Telefon raqamingizni tasdiqlang.", "user_id": new_user.id} 

# Kodni tasdiqlash
@router.post("/verify_code/")
def verify_code(phone_number: str, verification_code: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user and user.verification_code == verification_code:
        user.is_active = True
        user.verification_code = None  # Tasdiqlash kodi endi kerak emas
        user.role = "student"  # Rolni studentga o'zgartirish
        db.commit()

        # Foydalanuvchini Student jadvaliga o'tkazish
        db_student = Student(
            user_id=user.id,  # User ID bu yerda belgilanadi
            teacher_id=None,  # Keyinroq o'qituvchi tayinlanishi kerak
            attendance=0.0,  # Default qiymatlar
            rating=0.0
        )
        db.add(db_student)
        db.commit()
        
        return {"msg": "Hisob muvaffaqiyatli aktivlashtirildi va rol studentga o'zgartirildi."}
    else:
        raise HTTPException(status_code=400, detail="Noto'g'ri tasdiqlash kodi yoki telefon raqami")

@router.post("/students/{student_id}/attend")
def mark_attendance(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student topilmadi")
    db_student.attendance += 1
    db.commit()
    db.refresh(db_student)
    return db_student


@router.post("/groups/{group_id}/join-request/")
def send_join_request(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Foydalanuvchi talabami yoki yo'qligini tekshiring
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Faqat talabalar qo'shilish so'rovini yuborishi mumkin")

    # Talaba mavjudligini tekshirish
    db_student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student ro'yxatda topilmadi")

    # Talabaning so'rovini yaratish
    join_request = GroupMembership(group_id=group_id, student_id=db_student.id, status="pending")
    db.add(join_request)
    db.commit()
    
    return {"detail": "Qo'shilish so'rovi muvaffaqiyatli yuborildi"}




@router.put("/tasks/{task_id}/grade")
def grade_task(task_id: int, grade: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task topilmadi")
    db_task.grade = grade
    db.commit()
    db.refresh(db_task)
    return db_task




@router.post("/tasks/{task_id}/upload_result/")
async def upload_task_result(
    task_id: int,
    result_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Faqat talabalar natija yuklashi mumkin")
    
    db_task = db.query(Task).filter(Task.id == task_id, Task.student_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi yoki siz bu vazifaning talabasi emassiz")
    
    # Natijani saqlash
    result_path = f"task_results/{result_file.filename}"
    with open(result_path, "wb") as buffer:
        shutil.copyfileobj(result_file.file, buffer)

    db_task.student_result_path = result_path
    db.commit()
    db.refresh(db_task)
    return {"msg": "Natija muvaffaqiyatli yuklandi"}



@router.get("/lessons/")
def get_lessons(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view lessons")

    lessons = db.query(Task).filter(Task.student_id == current_user.id).all()
    return lessons

@router.get("/lessons/ongoing/")
def get_ongoing_lessons(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view ongoing lessons")

    now = datetime.now().time()
    ongoing_lessons = db.query(Task).filter(Task.start_time <= now, Task.end_time >= now, Task.student_id == current_user.id).all()
    return ongoing_lessons