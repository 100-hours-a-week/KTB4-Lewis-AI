"""
FastAPI 커뮤니티 서비스 - 메인 진입점
- 라우터 등록
- DB 테이블 자동 생성
- 서버 실행 설정
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from api.posts import router as posts_router
from api.comments import router as comments_router
from api.llm import router as llm_router

# ORM 모델을 import하여 Base에 등록 (테이블 생성에 필요)
from models.post import Post, PostLike
from models.comment import Comment, CommentLike


# ─── 앱 생성 ───
app = FastAPI(
    title="커뮤니티 서비스 API",
    description="FastAPI 기반 커뮤니티 백엔드 (게시글, 댓글, LLM 연동)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── DB 테이블 자동 생성 ───
Base.metadata.create_all(bind=engine)


# ─── 라우터 등록 ───
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(llm_router)
app.mount("/client", StaticFiles(directory="client", html=True), name="client")


# ─── 루트 엔드포인트 ───
@app.get("/", tags=["상태 확인"])
def root():
    """서버 상태 확인용 엔드포인트"""
    return {
        "message": "커뮤니티 서비스 API가 정상 작동 중입니다.",
        "docs": "/docs (Swagger UI)",
    }


# ─── 서버 직접 실행 시 ───
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
