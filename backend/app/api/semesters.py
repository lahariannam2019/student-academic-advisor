from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models import Semester, StudentProfile
from app.schemas.academic import SemesterCreate, SemesterUpdate, SemesterResponse
from app.api.deps import get_current_student

router = APIRouter()

@router.get("/", response_model=List[SemesterResponse])
def get_semesters(db: Session = Depends(get_db), student: StudentProfile = Depends(get_current_student)):
    semesters = db.query(Semester).filter(Semester.student_id == student.id).order_by(Semester.semester_number.asc()).all()
    return semesters

@router.post("/", response_model=SemesterResponse)
def create_semester(semester_in: SemesterCreate, db: Session = Depends(get_db), student: StudentProfile = Depends(get_current_student)):
    
    # Check for duplicate semester_number
    existing = db.query(Semester).filter(
        Semester.student_id == student.id, 
        Semester.semester_number == semester_in.semester_number
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Semester number already exists")
        
    if semester_in.sgpa is not None and (semester_in.sgpa < 0 or semester_in.sgpa > 10.0):
        raise HTTPException(status_code=400, detail="Invalid SGPA range")
        
    if semester_in.cgpa is not None and (semester_in.cgpa < 0 or semester_in.cgpa > 10.0):
        raise HTTPException(status_code=400, detail="Invalid CGPA range")
        
    db_semester = Semester(
        student_id=student.id,
        semester_number=semester_in.semester_number,
        academic_year=semester_in.academic_year,
        sgpa=semester_in.sgpa,
        cgpa=semester_in.cgpa,
        total_credits=semester_in.total_credits,
        is_current=False
    )
    db.add(db_semester)
    db.commit()
    db.refresh(db_semester)
    return db_semester

@router.put("/{semester_id}", response_model=SemesterResponse)
def update_semester(semester_id: str, semester_in: SemesterUpdate, db: Session = Depends(get_db), student: StudentProfile = Depends(get_current_student)):
    db_semester = db.query(Semester).filter(Semester.id == semester_id, Semester.student_id == student.id).first()
    
    if not db_semester:
        raise HTTPException(status_code=404, detail="Semester not found")
        
    if semester_in.semester_number is not None and semester_in.semester_number != db_semester.semester_number:
        existing = db.query(Semester).filter(
            Semester.student_id == student.id, 
            Semester.semester_number == semester_in.semester_number
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Semester number already exists")

    if semester_in.sgpa is not None and (semester_in.sgpa < 0 or semester_in.sgpa > 10.0):
        raise HTTPException(status_code=400, detail="Invalid SGPA range")
        
    if semester_in.cgpa is not None and (semester_in.cgpa < 0 or semester_in.cgpa > 10.0):
        raise HTTPException(status_code=400, detail="Invalid CGPA range")

    update_data = semester_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_semester, field, value)
        
    db.commit()
    db.refresh(db_semester)
    return db_semester

@router.delete("/{semester_id}")
def delete_semester(semester_id: str, db: Session = Depends(get_db), student: StudentProfile = Depends(get_current_student)):
    db_semester = db.query(Semester).filter(Semester.id == semester_id, Semester.student_id == student.id).first()
    
    if not db_semester:
        raise HTTPException(status_code=404, detail="Semester not found")
        
    db.delete(db_semester)
    db.commit()
    return {"status": "success"}
