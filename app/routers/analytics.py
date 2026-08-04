# * ==============================================================================
# *                          Router: Analytics
# * ==============================================================================
# ? این روتر همان چیزی است که کاربر در بررسی معماری خواسته بود: نام/کد/کلاس،
# ? نمره هر آزمون، میانگین، روند، نقاط قوت/ضعف، مقایسه با کلاس، تاریخچه -
# ? همه از روی ClassAnalyticsService/StudentAnalyticsService (فقط محاسبه،
# ? بدون ذخیره‌سازی اضافه).

from fastapi import APIRouter, HTTPException

from app.dependencies import ClassAnalyticsServiceDep, StudentAnalyticsServiceDep
from analytics.class_analytics import ExamClassAnalytics
from analytics.student_analytics import ClassComparison, StudentAnalytics

router = APIRouter(tags=["analytics"])


@router.get("/exams/{exam_id}/analytics", response_model=ExamClassAnalytics)
def get_exam_analytics(
    exam_id: str, class_analytics_service: ClassAnalyticsServiceDep
) -> ExamClassAnalytics:
    return class_analytics_service.analyze_exam(exam_id)


@router.get("/students/{student_id}/analytics", response_model=StudentAnalytics)
def get_student_analytics(
    student_id: str, student_analytics_service: StudentAnalyticsServiceDep
) -> StudentAnalytics:
    return student_analytics_service.analyze_student(student_id)


@router.get(
    "/students/{student_id}/analytics/compare/{exam_id}",
    response_model=ClassComparison,
)
def compare_student_to_class(
    student_id: str,
    exam_id: str,
    student_analytics_service: StudentAnalyticsServiceDep,
    class_analytics_service: ClassAnalyticsServiceDep,
) -> ClassComparison:
    class_analytics = class_analytics_service.analyze_exam(exam_id)
    if class_analytics.participant_count == 0:
        raise HTTPException(
            status_code=404, detail="No graded results found for this exam"
        )

    return student_analytics_service.compare_to_class(
        student_id, exam_id, class_analytics.average_percentage
    )
