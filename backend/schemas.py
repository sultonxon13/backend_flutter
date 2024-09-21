from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel
from typing import Optional
from datetime import time

class UserBase(BaseModel):
    id: int
    username: str

class UserCreate(UserBase):
    fullname: str
    phone_number: str

class TeacherCreate(BaseModel):
    fullname: str
    subject: str
    username: str
    password: str

class StudentCreate(BaseModel):
    fullname: str
    phone_number: str
    username: str

class AdminStudentCreate(StudentCreate):
    teacher_id: int
    attendance: float = 0.0
    rating: float = 0.0

class VerificationCode(BaseModel):
    phone_number: str
    verification_code: str

class TaskCreate(BaseModel):
    teacher_id: int
    student_id: int
    task_description: str
    grade: Optional[int] = None
    video_path: Optional[str] = None
    student_result_path: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    class Config:
        orm_mode = True

class TaskResponse(BaseModel):
    id: int
    teacher_id: int
    student_id: int
    task_description: str
    grade: Optional[int]
    video_path: str
    student_result_path: Optional[str]
    start_time: Optional[time]
    end_time: Optional[time]

    class Config:
        orm_mode = True
        
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class HomeworkCreate(BaseModel):
    title: str
    description: str
    group_id: int

class VideoCreate(BaseModel):
    title: str
    video_path: str
    group_id: int

class Group(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class HomeworkBase(BaseModel):
    title: str
    description: str
    group_id: int

    class Config:
        orm_mode = True

class HomeworkResponse(HomeworkBase):
    id: int

    class Config:
        orm_mode = True

class VideoResponse(VideoCreate):
    id: int

    class Config:
        orm_mode = True