from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.subjects import router as subjects_router
from app.api.attendance import router as attendance_router
from app.api.marks import router as marks_router
from app.api.assignments import router as assignments_router
from app.api.exams import router as exams_router
from app.api.planner import router as planner_router
from app.api.analytics import router as analytics_router
from app.api.advisor import router as advisor_router
from app.api.semesters import router as semesters_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(subjects_router)
api_router.include_router(attendance_router)
api_router.include_router(marks_router)
api_router.include_router(assignments_router)
api_router.include_router(exams_router)
api_router.include_router(planner_router)
api_router.include_router(analytics_router)
api_router.include_router(advisor_router)
api_router.include_router(semesters_router, prefix="/semesters", tags=["semesters"])
