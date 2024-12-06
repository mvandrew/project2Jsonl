import requests
import os
from dotenv import load_dotenv

class LLMAssist:
    """
    Класс для взаимодействия с LM Studio через эндпоинт /v1/chat/completions.
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

    def query(self, user_message, system_message=None, temperature=0.7, max_tokens=256):
        """
        Отправляет запрос на LM Studio сервер через /v1/chat/completions.

        :param user_message: Сообщение пользователя.
        :param system_message: Сообщение системы (контекст, необязательно).
        :param temperature: Уровень случайности генерации ответа.
        :param max_tokens: Максимальное количество токенов в ответе.
        :return: Ответ модели в виде строки.
        """
        if not self.success:
            raise RuntimeError("Не удалось инициализировать LLMAssist.")

        # Формирование сообщений для модели
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})

        # Формирование тела запроса
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            # Логируем запрос
            print(f"Отправка запроса: {payload}")

            # Отправляем запрос на /v1/chat/completions
            response = requests.post(self.server_url, json=payload)

            # Логируем ответ
            print(f"Ответ сервера: {response.text}")

            # Проверка кода ответа
            if response.status_code != 200:
                raise RuntimeError(f"Ошибка запроса к LLM: {response.status_code} - {response.text}")

            # Парсинг JSON-ответа
            response_data = response.json()

            # Извлечение текста из choices[0]["message"]["content"]
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"].get("content", "Нет текста в ответе.")
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

        # Максимальная длина сообщения
        max_length = 4096

        # Если содержимое файла пустое
        if not file_code.strip():
            user_message = f"Определи назначение PHP-файла {file_name} в проекте {self.project_type}. Файл пуст."
            user_messages = [user_message]
        else:
            max_code_length = 3500  # Ограничение на длину содержимого файла для сокращения
            if len(file_code) > max_code_length:
                file_code = file_code[:max_code_length] + "\n\n[Содержимое файла сокращено...]"

            user_message = (
                f"Опиши на русском языке назначение PHP-файла {file_name} в проекте {self.project_type}.\n"
                f"Не цитируй код файла или промпт пользователя.\n"
                f"Содержимое:\n\n{file_code}"
            )

            # Разделяем сообщение, если оно длиннее max_length
            user_messages = [user_message[i:i + max_length] for i in range(0, len(user_message), max_length)]

        # Формируем системное сообщение
        system_message = (
            "Вы ассистент для анализа PHP-файлов Yii2. Определяйте назначение файлов, классов и методов кратко и по существу."
        )

        # Обработка сообщений по частям
        result = ""
        for part in user_messages:
            response = self.query(user_message=part, system_message=system_message, max_tokens=256, temperature=0.4)
            result += response.strip() + "\n"

        return result.strip()
