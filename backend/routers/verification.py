from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from crud import create_verification_code, verify_code, generate_verification_code
from schemas import VerificationCode
from auth import get_db

router = APIRouter()

@router.post("/send_code/")
def send_code(verification_data: VerificationCode, db: Session = Depends(get_db)):
    # Tasdiqlash kodi avtomatik tarzda yaratiladi
    verification_code = generate_verification_code()  # Avtomatik kodi yaratiladi
    user = create_verification_code(db, verification_data.phone_number, verification_code)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Bu yerda siz kodni yuborishingiz kerak bo'ladi
    # SMS yuborishning o'rniga test kodini qaytaramiz
    return {"msg": "Verification code sent", "code": verification_code}

@router.post("/verify_code/")
def verify_code_endpoint(verification_data: VerificationCode, db: Session = Depends(get_db)):
    if verify_code(db, verification_data.phone_number, verification_data.verification_code):
        return {"msg": "Code verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification code")
