# * ==============================================================================
# *                              FastAPI App
# * ==============================================================================

from fastapi import FastAPI

from app.routers import analytics, classes, exams, grading, review, sheets, students
from infrastructure.database.session import init_db

app = FastAPI(title="Exam Grader API", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    # ? در فاز ۱ از create_all استفاده می‌کنیم؛ کافی است چون schema هنوز ساده است.
    init_db()


app.include_router(classes.router)
app.include_router(exams.router)
app.include_router(students.router)
app.include_router(sheets.router)
app.include_router(sheets.sheet_status_router)
app.include_router(grading.router)
app.include_router(review.router)
app.include_router(analytics.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
