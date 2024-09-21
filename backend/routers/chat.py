from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user, get_db
from models import User

router = APIRouter()

# Misol uchun chat holatini saqlash uchun oddiy bir flag
chat_status_flag = True  # True - chat ochiq, False - chat yopiq

@router.get("/chat/status/")
def get_chat_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Chat holatini olish uchun endpoint. Chat ochiq yoki yopiq ekanligini qaytaradi.
    """
    # Chat holatini tekshirish
    if chat_status_flag:
        return {"chat_status": "open"}
    else:
        return {"chat_status": "closed"}

@router.post("/chat/status/{status}")
def set_chat_status(status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Chat holatini o'zgartirish uchun endpoint. "open" yoki "closed" statuslarini qabul qiladi.
    """
    global chat_status_flag
    
    if status not in ["open", "closed"]:
        raise HTTPException(status_code=400, detail="Invalid status value. Use 'open' or 'closed'.")
    
    chat_status_flag = (status == "open")
    return {"chat_status": status}
