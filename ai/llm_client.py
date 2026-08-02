# * ==============================================================================
# *                          LLMClient (Interface)
# * ==============================================================================
# ? این Interface تنها نقطه‌ای است که Grading Layer با "یک مدل زبانی" ارتباط
# ? دارد. هیچ Grader ای نباید مستقیماً از Ollama یا هر Provider دیگری نام ببرد.
#
# ! طبق قانون پروژه: "Ollama فقط یکی از اجزای احتمالی پروژه است و نباید تمام
# ! معماری به آن وابسته باشد." اگر فردا خواستیم OpenAI/Claude/مدل محلی دیگری
# ! جایگزین شود، فقط یک پیاده‌سازی جدید از همین Interface لازم است - نه تغییر
# ! در EssayGrader یا ShortAnswerGrader.

from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        """
        ? یک prompt متنی می‌گیرد و پاسخ خام مدل را به‌صورت رشته برمی‌گرداند.

        ! این متد نباید JSON را parse کند - مسئولیت parse کردن پاسخ به عهده
        ! کد صداکننده (Grader) است، نه این لایه انتزاعی.
        """
        raise NotImplementedError
