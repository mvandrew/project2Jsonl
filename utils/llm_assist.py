import requests
import os
from dotenv import load_dotenv

class LLMAssist:
    """
    Класс для взаимодействия с LM Studio и выполнения запросов к заданной модели.
    """

    def __init__(self, project_type):
        """
        Инициализация LLMAssist с загрузкой параметров из .env файла.

        :param project_type: Тип проекта (например, "php", "python").
        """
        # Загрузка переменных из .env файла
        load_dotenv()

        self.server_url = os.getenv("LLM_SERVER_URL")
        self.model_name = os.getenv("LLM_MODEL_NAME")
        self.project_type = project_type

        # Проверка обязательных параметров
        self.success = bool(self.server_url and self.model_name)

    def query(self, prompt, temperature=0.7, max_tokens=256):
        """
        Отправляет запрос на LM Studio сервер через /v1/completions.

        :param prompt: Текстовый запрос для модели.
        :param temperature: Уровень случайности генерации ответа (0.0 - детерминированный, 1.0 - максимальная случайность).
        :param max_tokens: Максимальное количество токенов в ответе.
        :return: Ответ модели в виде строки.
        """
        if not self.success:
            raise RuntimeError("Не удалось инициализировать LLMAssist.")

        # Формирование тела запроса
        payload = {
            "prompt": prompt,
            "model": self.model_name,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            # Логируем запрос
            print(f"Отправка запроса: {payload}")

            # Отправляем запрос на /v1/completions
            response = requests.post(self.server_url, json=payload)

            # Логируем ответ
            print(f"Ответ сервера: {response.text}")

            # Проверка кода ответа
            if response.status_code != 200:
                raise RuntimeError(f"Ошибка запроса к LLM: {response.status_code} - {response.text}")

            # Парсинг JSON-ответа
            response_data = response.json()

            # Извлечение текста из choices[0]["text"]
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0].get("text", "Нет текста в ответе.")
            else:
                raise ValueError(f"Некорректный ответ модели: {response_data}")

        except Exception as e:
            raise RuntimeError(f"Ошибка при взаимодействии с LLM: {e}")

    def describe_file(self, file_name, file_code):
        """
        Описывает назначение файла на основе его имени и содержимого.

        :param file_name: Имя файла.
        :param file_code: Содержимое файла.
        :return: Описание назначения файла.
        """
        if not self.success:
            raise RuntimeError("Не удалось инициализировать LLMAssist.")

        # Если содержимое файла пустое
        if not file_code.strip():
            prompt = (
                f"Тип проекта: {self.project_type}\n"
                f"Опиши назначение файла с именем {file_name}. Файл пуст или недоступен."
            )
        else:
            max_code_length = 3500  # Ограничение на длину содержимого файла
            if len(file_code) > max_code_length:
                file_code = file_code[:max_code_length] + "\n\n[Содержимое файла сокращено...]"

            prompt = (
                f"Тип проекта: {self.project_type}\n"
                f"Опиши назначение файла с именем {file_name}. Вот содержимое файла:\n\n{file_code}"
            )

        # Увеличиваем max_tokens для получения более полного ответа
        return self.query(prompt, max_tokens=512)
