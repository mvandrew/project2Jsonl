import json
import os
from dotenv import load_dotenv

class QAManager:
    """
    Синглетный класс для управления глобальным массивом вопросов и ответов.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QAManager, cls).__new__(cls)
            cls._instance._qa_global = []  # Инициализация глобального массива QA
            cls._instance._load_env()  # Загрузка параметров из .env
        return cls._instance

    @classmethod
    def _load_env(cls):
        """
        Загружает параметры из .env файла и инициализирует необходимые переменные.
        """
        load_dotenv()
        cls.OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
        cls.PROJECT_PREFIX = os.getenv("PROJECT_PREFIX", "project")

    def add_qa(self, question, answer, context=None):
        """
        Добавляет пару вопрос-ответ (и опциональный контекст) в глобальный массив.

        :param question: Текст вопроса.
        :param answer: Текст ответа.
        :param context: Дополнительный контекст для вопроса.
        """
        qa_entry = {"question": question, "answer": answer}
        if context:
            qa_entry["context"] = context
        self._qa_global.append(qa_entry)

    def get_qa(self):
        """
        Возвращает глобальный массив QA.

        :return: Список вопросов и ответов.
        """
        return self._qa_global

    def save_to_jsonl(self):
        """
        Сохраняет глобальный массив QA в JSONL-файл. Параметры берутся из .env:
        - OUTPUT_DIR: Каталог для сохранения файла.
        - PROJECT_PREFIX: Префикс для имени файла.
        """
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        file_name = f"{self.PROJECT_PREFIX}_qa_global.jsonl"
        output_file = os.path.join(self.OUTPUT_DIR, file_name)

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for item in self._qa_global:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            print(f"Глобальный QA файл сохранён в: {output_file}")
        except Exception as e:
            raise RuntimeError(f"Ошибка при сохранении глобального QA файла: {e}")

    def clear_qa(self):
        """
        Очищает глобальный массив QA.
        """
        self._qa_global = []
