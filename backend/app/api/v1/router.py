from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.interview import router as interview_router
from app.api.v1.resume import router as resume_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(resume_router, prefix="/resume", tags=["Resume"])
api_router.include_router(interview_router, prefix="/interview", tags=["Interview"])
