from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import uuid
from models import User, Group as DBGroup, Teacher, Task, GroupMembership, Homework, Video
from schemas import Group, GroupCreate, HomeworkCreate, HomeworkResponse, VideoCreate, VideoResponse, TaskCreate, TaskResponse
from crud import create_group, add_member, create_homework, create_video, get_group_members_count, create_task
from auth import get_current_user, get_db
from datetime import datetime, timedelta
router = APIRouter()

@router.post("/tasks/", response_model=TaskResponse)
async def create_new_task(
    task: TaskCreate, 
    video: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Tizimga kirgan foydalanuvchi aniqlanadi
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create tasks")

    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    video_extension = os.path.splitext(video.filename)[1]
    unique_filename = f"{uuid.uuid4()}{video_extension}"
    video_filename = os.path.join(uploads_dir, unique_filename)

    with open(video_filename, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    
    db_task = Task(
        teacher_id=current_user.id,
        student_id=task.student_id,
        task_description=task.task_description,
        grade=task.grade,
        video_path=video_filename
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.put("/tasks/{task_id}/grade")
def grade_task(
    task_id: int,
    grade: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Faqat o'qituvchilar baholash mumkin")

    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")

    # Baho qo'yish
    db_task.grade = grade
    db.commit()
    db.refresh(db_task)
    return db_task



@router.put("/teachers/{teacher_id}/subject")
def update_teacher_subject(teacher_id: int, subject: str, db: Session = Depends(get_db)):
    db_teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    db_teacher.subject = subject
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


@router.post("/groups/", response_model=Group)
def create_group_route(group: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Sizda ruxsat yo'q")

    # Foydalanuvchining o'qituvchi ekanligini va `teachers` jadvalida mavjudligini tekshirish
    db_teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Ushbu foydalanuvchi uchun o'qituvchi profili topilmadi")

    # Guruh yaratish va o'qituvchi ID sini `created_by` sifatida belgilash
    db_group = create_group(db, group, db_teacher.id)
    return db_group





@router.get("/groups/{group_id}/join-requests/")
def get_join_requests(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view join requests")

    # So'rovlar ro'yxatini olish
    join_requests = db.query(GroupMembership).filter(GroupMembership.group_id == group_id, GroupMembership.status == "pending").all()
    return join_requests

@router.put("/groups/{group_id}/join-requests/{request_id}/accept")
def accept_join_request(group_id: int, request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can accept join requests")

    # So'rovni tasdiqlash
    join_request = db.query(GroupMembership).filter(GroupMembership.id == request_id, GroupMembership.group_id == group_id).first()
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")

    join_request.status = "accepted"
    db.commit()
    return {"detail": "Join request accepted"}

@router.put("/groups/{group_id}/join-requests/{request_id}/reject")
def reject_join_request(group_id: int, request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can reject join requests")

    # So'rovni rad etish
    join_request = db.query(GroupMembership).filter(GroupMembership.id == request_id, GroupMembership.group_id == group_id).first()
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")

    join_request.status = "rejected"
    db.commit()
    return {"detail": "Join request rejected"}



@router.post("/groups/{group_id}/members/")
def add_member_route(group_id: int, student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_group = db.query(DBGroup).filter(DBGroup.id == group_id, DBGroup.created_by == current_user.id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found or not authorized")
    
    add_member(db, group_id, student_id)
    return {"detail": "Member added"}

@router.post("/homeworks/", response_model=HomeworkResponse)
def create_homework_route(homework: HomeworkCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_homework = create_homework(db, homework)
    return db_homework

@router.post("/videos/", response_model=VideoResponse)
def create_video_route(video: VideoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_video = create_video(db, video)
    return db_video

@router.get("/groups/{group_id}/members/count/")
def get_group_members_count_route(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    count = get_group_members_count(db, group_id)
    return {"count": count}





@router.post("/lessons/", response_model=TaskResponse)
async def create_lesson(
    lesson: TaskCreate,
    start_time: str,  # Format: 'HH:MM'
    end_time: str,    # Format: 'HH:MM'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create lessons")

    # Convert times to datetime objects
    now = datetime.now()
    start_time = datetime.strptime(start_time, '%H:%M').time()
    end_time = datetime.strptime(end_time, '%H:%M').time()

    # Ensure end time is after start time
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # Create the lesson
    db_task = Task(
        teacher_id=current_user.id,
        student_id=lesson.student_id,
        task_description=lesson.task_description,
        grade=lesson.grade,
        video_path=lesson.video_path,
        start_time=start_time,
        end_time=end_time
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/lessons/")
def get_lessons(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view lessons")

    lessons = db.query(Task).filter(Task.student_id == current_user.id).all()
    return lessons