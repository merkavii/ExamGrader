# * ==============================================================================
# *                          BaseGrader (Contract)
# * ==============================================================================
# ? هر Grader باید این کلاس را پیاده‌سازی کند. این همان قرارداد Strategy Pattern
# ? است که GradingOrchestrator بر اساس آن، Grader مناسب را انتخاب و صدا می‌زند.
#
# ! هیچ Grader ای اجازه ندارد:
# !   - مستقیماً به تصویر/فایل دسترسی داشته باشد (وظیفه لایه Extraction است)
# !   - به Repository یا دیتابیس متصل شود (ورودی/خروجی فقط از طریق پارامترهای grade)
# !   - بداند StudentAnswer از کجا آمده (source) - این فقط برای audit استفاده می‌شود

from abc import ABC, abstractmethod

from domain.models.exam import Question
from domain.models.grading_result import GradeResult
from domain.models.student import StudentAnswer


class BaseGrader(ABC):
    @abstractmethod
    def grade(self, question: Question, student_answer: StudentAnswer) -> GradeResult:
        """
        ? یک (Question, StudentAnswer) را می‌گیرد و GradeResult استاندارد برمی‌گرداند.

        ! پیاده‌سازی‌ها موظف‌اند حتی برای نمره صفر هم `reasoning` معنادار بنویسند -
        ! نه رشته خالی یا جمله کلی‌ای مثل "نمره محاسبه شد".
        """
        raise NotImplementedError
