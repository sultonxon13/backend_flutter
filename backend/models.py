from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Time

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(128))
    role = Column(String(20))
    fullname = Column(String(100))
    phone_number = Column(String(15))
    passport_image = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=False)
    verification_code = Column(String(6), nullable=True)

    teacher = relationship("Teacher", back_populates="user")
    student = relationship("Student", back_populates="user")

class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(50))  # Teacher'ning ismi
    subject = Column(String(100))  # O'qitiladigan fan
    rating = Column(Float, default=0.0)  # Reyting

    user = relationship("User", back_populates="teacher")
    students = relationship("Student", back_populates="teacher")
    tasks = relationship("Task", back_populates="teacher")
    groups = relationship("Group", back_populates="creator", primaryjoin="Teacher.id==Group.created_by")

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    attendance = Column(Float, default=0.0)
    rating = Column(Float, default=0.0)

    user = relationship("User", back_populates="student")
    teacher = relationship("Teacher", back_populates="students")
    tasks = relationship("Task", back_populates="student")
    group_memberships = relationship("GroupMembership", back_populates="student")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    student_id = Column(Integer, ForeignKey('students.id'))
    task_description = Column(String(1000))
    grade = Column(Integer)  # 1-5 ballar
    video_path = Column(String(255))
    student_result_path = Column(String(255))  # O‘quvchining natija fayli
    start_time = Column(Time)  # Dars boshlanish vaqti
    end_time = Column(Time)    # Dars tugash vaqti

    teacher = relationship("Teacher", back_populates="tasks")
    student = relationship("Student", back_populates="tasks")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("teachers.id"))
     
    creator = relationship("Teacher", back_populates="groups")
    memberships = relationship("GroupMembership", back_populates="group")
    homeworks = relationship("Homework", back_populates="group")
    videos = relationship("Video", back_populates="group")

class GroupMembership(Base):
    __tablename__ = "group_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    status = Column(String(20), default="pending")  # So'rov holati: pending, accepted, rejected
    
    group = relationship("Group", back_populates="memberships")
    student = relationship("Student", back_populates="group_memberships")

class Homework(Base):
    __tablename__ = "homeworks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    group_id = Column(Integer, ForeignKey("groups.id"))
    
    group = relationship("Group", back_populates="homeworks")

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)  # VARCHAR uzunligi qo‘shildi
    video_path = Column(String(255))
    group_id = Column(Integer, ForeignKey("groups.id"))
    
    group = relationship("Group", back_populates="videos")
