import json
import requests
import os
from dotenv import load_dotenv
from utils.query_cache import get_cached_response, save_response
from difflib import SequenceMatcher

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
        self.max_code_length = int(os.getenv("MAX_CODE_LENGTH", 3500))  # Используем значение из .env или значение по умолчанию
        self.max_tokens = int(os.getenv("MAX_TOKENS", 256))
        self.max_context_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", 4096))

        # Проверка обязательных параметров
        self.success = bool(self.server_url and self.model_name)

    def similarity(self, text1, text2):
        """
        Вычисляет схожесть двух текстов на основе количества совпадающих символов.

        :param text1: Первый текст.
        :param text2: Второй текст.
        :return: Коэффициент схожести (от 0 до 1).
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def split_into_chunks(self, file_code, system_prompt, user_prompt):
        """
        Разбивает исходный код файла на чанки, учитывая max_context_tokens.

        :param file_code: Исходный код файла.
        :param system_prompt: Системный промпт.
        :param user_prompt: Пользовательский промпт.
        :return: Список чанков исходного кода, которые укладываются в ограничение по токенам.
        """
        if not file_code.strip():
            raise ValueError("Исходный код файла пуст.")

        # Вычисляем максимальный размер чанка с учетом промптов и погрешности
        total_reserved_tokens = len(system_prompt) + len(user_prompt)  # Оценка токенов для промптов
        max_tokens_for_code = self.max_context_tokens - total_reserved_tokens

        # Учитываем погрешность ~10%
        max_tokens_for_code = int(max_tokens_for_code * 0.9)

        if max_tokens_for_code <= 0:
            raise ValueError("Размер контекста слишком мал для размещения кода с промптами.")

        # Преобразуем приблизительное ограничение токенов в количество символов
        # (предполагая, что 1 токен ≈ 0.5 символа)
        max_chunk_size = max_tokens_for_code * 2

        # Разбиваем код на чанки
        chunks = [file_code[i:i + max_chunk_size] for i in range(0, len(file_code), max_chunk_size)]

        return chunks

    def query(self, user_message, system_message=None, temperature=0.7, max_tokens=None):
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

        # Если max_tokens не задан, используем self.max_tokens
        if max_tokens is None:
            max_tokens = self.max_tokens

        # Формирование тела запроса
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Преобразование payload в строку для использования в кэшировании
        cache_key = json.dumps(payload, sort_keys=True)

        # Проверка необходимости использования кэша
        use_cache = os.getenv("USE_CACHE", "true").lower() == "true"
        if use_cache:
            cached_response = get_cached_response(cache_key)
            if cached_response:
                print("Ответ получен из кэша.")
                return cached_response

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
                content = response_data["choices"][0]["message"].get("content", "Нет текста в ответе.")

                # Сохраняем в кэш, если кэширование включено
                if use_cache:
                    save_response(cache_key, content)

                return content
            else:
                raise ValueError(f"Некорректный ответ модели: {response_data}")

        except Exception as e:
            raise RuntimeError(f"Ошибка при взаимодействии с LLM: {e}")

    def process_code_chunks(self, code, system_prompt, user_prompt):
        """
        Общая функция для обработки исходного кода, разделенного на чанки.

        :param code: Исходный код.
        :param system_prompt: Системный промпт.
        :param user_prompt: Пользовательский промпт.
        :return: Итоговое описание или консолидация результатов.
        """
        # Разбиваем код на чанки
        chunks = self.split_into_chunks(code, system_prompt, user_prompt)

        # Если только один чанк, возвращаем результат без консолидации
        if len(chunks) == 1:
            user_message = f"{user_prompt}\nСодержимое:\n\n{chunks[0]}"
            return self.query(user_message=user_message, system_message=system_prompt, temperature=0.4)

        results = []
        accumulated_context = ""  # Для хранения контекста ответов ассистента

        for idx, chunk in enumerate(chunks):
            # Формируем сообщение с учетом контекста предыдущих частей
            user_message = f"Часть {idx + 1}/{len(chunks)}. {user_prompt}\nСодержимое:\n\n{chunk}"
            if accumulated_context:
                user_message += f"\n\nКонтекст предыдущих частей:\n{accumulated_context}"

            try:
                result = self.query(user_message=user_message, system_message=system_prompt, temperature=0.4)
                results.append(result)

                # Проверяем схожесть последних двух ответов
                if idx > 0 and self.similarity(results[-1], results[-2]) > 0.9:
                    if len(results) < 3:
                        return results[0]  # Если менее трех ответов, возвращаем первый
                    break

                accumulated_context = result  # Обновляем контекст
            except Exception as e:
                raise RuntimeError(f"Ошибка при обработке чанка {idx + 1}: {e}")

        # Если менее трех результатов, возвращаем первый
        if len(results) < 3:
            return results[0]

        # Формируем запрос на консолидацию
        consolidated_prompt = (
            f"Вы ассистент для анализа исходного кода. "
            f"Объедините результаты анализа всех частей кода и предоставьте итоговое описание."
        )
        consolidated_user_message = "\n\n".join(
            [f"Ответ на часть {idx + 1}/{len(results)}:\n{result}" for idx, result in enumerate(results)]
        )

        try:
            consolidated_result = self.query(
                user_message=consolidated_user_message,
                system_message=consolidated_prompt,
                temperature=0.4
            )
            return consolidated_result
        except Exception as e:
            raise RuntimeError(f"Ошибка при консолидации результатов: {e}")

    def describe_file(self, file_name, file_code):
        """
        Описывает назначение файла на основе его имени и содержимого.

        :param file_name: Имя файла.
        :param file_code: Содержимое файла.
        :return: Описание назначения файла.
        """
        system_prompt = (
            f"Вы ассистент для анализа PHP-файлов проекта {self.project_type}. "
            f"Определяйте назначение файлов, классов и методов кратко и по существу."
        )
        user_prompt = f"Опишите назначение PHP-файла {file_name} в проекте {self.project_type}."
        return self.process_code_chunks(file_code, system_prompt, user_prompt)

    def describe_class(self, class_name, class_code):
        """
        Описывает назначение класса на основе его имени и содержимого.

        :param class_name: Имя класса.
        :param class_code: Содержимое кода класса.
        :return: Описание назначения класса.
        """
        system_prompt = (
            f"Вы ассистент для анализа PHP-классов проекта {self.project_type}. "
            f"Определяйте назначение классов, методов и их связей кратко и по существу."
        )
        user_prompt = f"Опишите назначение PHP-класса {class_name} в проекте {self.project_type}."
        return self.process_code_chunks(class_code, system_prompt, user_prompt)

    def describe_class_method(self, method_name, method_code, class_name, class_description):
        """
        Описывает назначение метода класса на основе его имени, содержимого и описания класса.

        :param method_name: Имя метода.
        :param method_code: Содержимое кода метода.
        :param class_name: Имя класса, к которому принадлежит метод.
        :param class_description: Описание назначения класса.
        :return: Описание назначения метода.
        """
        system_prompt = (
            f"Вы ассистент для анализа PHP-классов и их методов проекта {self.project_type}. "
            f"Определяйте назначение методов кратко и по существу, с учетом контекста класса."
        )
        user_prompt = (
            f"Опишите назначение метода {method_name} в классе {class_name} проекта {self.project_type}. "
            f"Описание класса: {class_description}."
        )
        return self.process_code_chunks(method_code, system_prompt, user_prompt)

    def describe_global_function(self, function_name, function_code, file_name):
        """
        Описывает назначение глобальной функции на основе её имени и содержимого.

        :param function_name: Имя функции.
        :param function_code: Содержимое кода функции.
        :param file_name: Имя файла, в котором определена функция.
        :return: Описание назначения функции.
        """
        system_prompt = (
            f"Вы ассистент для анализа PHP-файлов и их глобальных функций в проекте {self.project_type}. "
            f"Определяйте назначение функций кратко и по существу."
        )
        user_prompt = (
            f"Опишите назначение глобальной функции {function_name}, определённой в файле {file_name} проекта {self.project_type}."
        )
        return self.process_code_chunks(function_code, system_prompt, user_prompt)
