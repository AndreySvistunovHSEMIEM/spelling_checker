"""Репозиторий для работы с данными слов"""
import json
import logging
import os
import random
import time
from typing import List, Optional, Dict, Any

from .models import AppData, WordData, TrainingState, AppSettings, RepeatWordData
from .constants import Constants

logger = logging.getLogger(__name__)

# word_repository.py - полностью переписываем методы загрузки/сохранения

class WordRepository:
    """Репозиторий для работы с данными слов с поддержкой множественных категорий"""
    
    def __init__(self, base_dir: str, media_manager=None):
        # Используем get_data_directory() для определения пути к файлам
        data_dir = Constants.get_data_directory()
        self.base_dir = base_dir
        self.words_file = os.path.join(data_dir, Constants.WORDS_FILE)
        self.progress_file = os.path.join(data_dir, Constants.PROGRESS_FILE)
        self.settings_file = os.path.join(data_dir, Constants.SETTINGS_FILE)
        self.app_data = AppData()
        self.media_manager = media_manager  # Сразу устанавливаем связь
    
    def set_media_manager(self, media_manager):
        self.media_manager = media_manager
    
    def load_data(self) -> bool:
        """Загружает данные из файлов слов, прогресса и настроек"""
        logger.info("=== НАЧАЛО ЗАГРУЗКИ ДАННЫХ ===")
        
        try:
            # Инициализируем пустые данные
            self.app_data = AppData()
            logger.info("Создан новый AppData с состоянием по умолчанию")
            
            # Загружаем настройки
            try:
                self._load_settings_data()
                logger.info("Настройки загружены: cost=%.2f, penalty=%.2f", 
                        self.app_data.settings.cost_per_word, 
                        self.app_data.settings.penalty_per_word)
            except Exception as e:
                logger.warning("Не удалось загрузить настройки: %s", e)
            
            # Загружаем слова
            try:
                self._load_words_data()
                logger.info("Слова загружены: %d слов, %d категорий", 
                        len(self.app_data.words), len(self.app_data.categories))
            except Exception as e:
                logger.exception("Фатальная ошибка загрузки слов: %s", e)
                return False
            
            # Загружаем прогресс
            try:
                self._load_progress_data()
                logger.info("Прогресс загружен: points_score=%d, rubles_score=%.2f, used_words=%d, current_category=%s",
                        self.app_data.training_state.points_score,
                        self.app_data.training_state.rubles_score,
                        len(self.app_data.training_state.used_words),
                        self.app_data.training_state.current_category)
            except Exception as e:
                logger.warning("Не удалось загрузить прогресс: %s", e)
                
            # Мигрируем used_words если нужно
            self.migrate_used_words_to_uids()
            
            logger.info("=== ЗАВЕРШЕНИЕ ЗАГРУЗКИ ДАННЫХ ===")
            return True
            
        except Exception as e:
            logger.exception("Критическая ошибка загрузки данных: %s", e)
            return False
    
    def _load_words_data(self) -> None:
        """Загружает данные слов из words.json"""
        if not os.path.exists(self.words_file):
            return  # Файла нет - это нормально при первом запуске
        
        # Пробуем разные кодировки для надежности
        encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'latin-1']
        data = None
        last_error = None
        
        for encoding in encodings:
            try:
                with open(self.words_file, "r", encoding=encoding) as f:
                    data = json.load(f)
                logger.debug("Данные слов успешно загружены с кодировкой %s", encoding)
                break  # Если успешно, выходим из цикла
            except UnicodeDecodeError as e:
                last_error = e
                logger.debug("Не удалось декодировать файл слов с кодировкой %s: %s", encoding, e)
                continue
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning("Ошибка парсинга JSON слов с кодировкой %s: %s", encoding, e)
                continue
        
        if data is None:
            error_msg = f"Не удалось загрузить данные слов из файла {self.words_file}"
            if last_error:
                error_msg += f": {last_error}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Восстанавливаем слова с поддержкой старого и нового формата
        self.app_data.words = []
        
        # Получаем все существующие uid для проверки уникальности
        existing_uids = set()
        
        for idx, word_dict in enumerate(data.get("words", [])):
            try:
                # ОБРАБОТКА РАЗНЫХ ФОРМАТОВ КАТЕГОРИЙ
                categories = []
                
                # Старый формат: "category" как строка
                if "category" in word_dict and "categories" not in word_dict:
                    if word_dict["category"]:  # Если категория не пустая
                        categories = [word_dict["category"]]
                # Новый формат: "categories" как список
                elif "categories" in word_dict:
                    categories = word_dict.get("categories", [])
                
                # Валидация обязательного поля
                if "word" not in word_dict or not word_dict["word"]:
                    logger.warning("Пропущено слово без названия (индекс %d)", idx)
                    continue
                
                word_data = WordData(
                    word=word_dict["word"],
                    categories=categories,  # НОВЫЙ ФОРМАТ
                    audio=word_dict.get("audio", ""),
                    images=word_dict.get("images", []),
                    case_sensitive=word_dict.get("case_sensitive", False),
                    important_positions=word_dict.get("important_positions", "")
                )
                
                # ВОССТАНАВЛИВАЕМ uid если есть, иначе создаем новый 4-значный
                if "uid" in word_dict:
                    word_data.uid = word_dict["uid"]
                    existing_uids.add(word_data.uid)
                else:
                    # Генерируем новый 4-значный uid для старых данных
                    word_data.uid = self._generate_numeric_uid(existing_uids)
                    existing_uids.add(word_data.uid)
                
                # Проверяем и восстанавливаем медиафайлы если media_manager установлен
                if self.media_manager is not None:
                    word_data = self.media_manager.validate_media_files(word_data)
                self.app_data.words.append(word_data)
            except ValueError as e:
                logger.warning("Пропущено некорректное слово (индекс %d): %s", idx, e)
                continue
            except Exception as e:
                logger.warning("Ошибка при обработке слова (индекс %d): %s", idx, e)
                continue
        
        # Восстанавливаем категории (автоматически извлекаем из всех слов)
        self._rebuild_categories_from_words()
        
        # ОЧИЩАЕМ НЕКОРРЕКТНЫЕ КАТЕГОРИИ ПОСЛЕ ЗАГРУЗКИ
        # ИСПОЛЬЗУЕМ ВЕРСИЮ БЕЗ СОХРАНЕНИЯ, ЧТОБЫ НЕ ПЕРЕЗАПИСАТЬ ПРОГРЕСС
        self._cleanup_invalid_categories_only_no_save()

    def _load_progress_data(self) -> None:
        """Загружает данные прогресса из progress.json"""
        logger.info("Попытка загрузить прогресс из: %s", self.progress_file)
        
        if not os.path.exists(self.progress_file):
            logger.warning("Файл прогресса не существует: %s", self.progress_file)
            return

        # Пробуем разные кодировки для надежности
        encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'latin-1']
        data = None
        last_error = None
        
        for encoding in encodings:
            try:
                with open(self.progress_file, "r", encoding=encoding) as f:
                    data = json.load(f)
                logger.debug("Данные прогресса успешно загружены с кодировкой %s", encoding)
                break # Если успешно, выходим из цикла
            except UnicodeDecodeError as e:
                last_error = e
                logger.debug("Не удалось декодировать файл прогресса с кодировкой %s: %s", encoding, e)
                continue
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning("Ошибка парсинга JSON прогресса с кодировкой %s: %s", encoding, e)
                continue
            except Exception as e:
                last_error = e
                logger.warning("Неизвестная ошибка при загрузке прогресса с кодировкой %s: %s", encoding, e)
                continue
        
        if data is None:
            error_msg = f"Не удалось загрузить данные прогресса из файла {self.progress_file}"
            if last_error:
                error_msg += f": {last_error}"
            logger.error(error_msg)
            return  # Не создаем исключение, а просто выходим

        try:
            training_data = data.get("training_state", {})
            logger.info("Данные тренировки: %s", training_data.keys())
            
            # Загружаем отдельные счеты для баллов и рублей
            if "points_score" in training_data:
                self.app_data.training_state.points_score = training_data.get("points_score", 0)
            if "rubles_score" in training_data:
                self.app_data.training_state.rubles_score = training_data.get("rubles_score", 0.0)
            
            # Обработка устаревшего поля score для миграции данных
            if "score" in training_data:
                legacy_score = training_data.get("score", 0.0)
                # Если новые поля не были загружены или равны 0, а старое поле не равно 0,
                # то используем логику миграции из TrainingState.__post_init__
                if (legacy_score != 0.0 and
                    self.app_data.training_state.points_score == 0 and
                    self.app_data.training_state.rubles_score == 0.0):
                    # Предполагаем, что если score целое число, то это были баллы, иначе - рубли
                    if isinstance(legacy_score, (int, float)) and legacy_score.is_integer():
                        self.app_data.training_state.points_score = int(legacy_score)
                    else:
                        self.app_data.training_state.rubles_score = float(legacy_score)
                # В любом случае, не обновляем текущее значение legacy score,
                # так как оно устаревшее и используется только для миграции
            
            if "used_words" in training_data:
                used_words_data = training_data.get("used_words", [])
                if isinstance(used_words_data, list):
                    self.app_data.training_state.used_words = set(used_words_data)
            
            # ЗАГРУЖАЕМ использованные слова по категориям
            if "used_words_by_category" in training_data:
                used_words_by_category_data = training_data.get("used_words_by_category", {})
                for category, words in used_words_by_category_data.items():
                    if isinstance(words, list):
                        self.app_data.training_state.used_words_by_category[category] = set(words)
            
            if "current_category" in training_data:
                self.app_data.training_state.current_category = training_data.get("current_category", "")
            
            # ЗАГРУЖАЕМ СЧЕТЧИКИ ОШИБОК ДЛЯ КАТЕГОРИЙ
            if "mistakes_count" in training_data:
                mistakes_count_data = training_data.get("mistakes_count", {})
                for category, words in mistakes_count_data.items():
                    # Убедимся, что категория существует в словаре как defaultdict
                    if category not in self.app_data.training_state.mistakes_count:
                        self.app_data.training_state.mistakes_count[category] = {}
                    for word, count in words.items():
                        self.app_data.training_state.mistakes_count[category][word] = count
            
            # ЗАГРУЖАЕМ НЕПРАВИЛЬНЫЕ ОТВЕТЫ
            if "wrong_answers" in training_data:
                wrong_answers_data = training_data.get("wrong_answers", {})
                for category, words in wrong_answers_data.items():
                    # Убедимся, что категория существует в словаре как defaultdict
                    if category not in self.app_data.training_state.wrong_answers:
                        self.app_data.training_state.wrong_answers[category] = {}
                    for word, answers in words.items():
                        self.app_data.training_state.wrong_answers[category][word] = answers
            
            # ЗАГРУЖАЕМ СЧЕТЧИКИ ПРАВИЛЬНЫХ ОТВЕТОВ
            if "correct_answers_count" in training_data:
                correct_count_data = training_data.get("correct_answers_count", {})
                for category, count in correct_count_data.items():
                    self.app_data.training_state.correct_answers_count[category] = count
            
            # ЗАГРУЖАЕМ СЧЕТЧИКИ НЕПРАВИЛЬНЫХ ОТВЕТОВ
            if "incorrect_answers_count" in training_data:
                incorrect_count_data = training_data.get("incorrect_answers_count", {})
                for category, count in incorrect_count_data.items():
                    self.app_data.training_state.incorrect_answers_count[category] = count
            
            # ЗАГРУЖАЕМ СЛОВА НА ПОВТОРЕНИИ
            if "repeat_words" in training_data:
                repeat_words_data = training_data.get("repeat_words", [])
                for rw_data in repeat_words_data:
                    repeat_word = RepeatWordData(
                        word_uid=rw_data.get("word_uid", ""),
                        category=rw_data.get("category", ""),
                        next_show_after=rw_data.get("next_show_after", 0),
                        current_attempt=rw_data.get("current_attempt", 1),
                        total_attempts_needed=rw_data.get("total_attempts_needed", 3)
                    )
                    self.app_data.training_state.repeat_words.append(repeat_word)
                
            logger.info("Прогресс загружен: points_score=%d, rubles_score=%.2f, used_words=%d",
                    self.app_data.training_state.points_score,
                    self.app_data.training_state.rubles_score,
                    len(self.app_data.training_state.used_words))
                    
        except Exception as e:
            logger.error("Ошибка при обработке загруженных данных прогресса: %s", e)

    def _load_settings_data(self) -> None:
        """Загружает настройки из settings.json"""
        if not os.path.exists(self.settings_file):
            return # Файла нет - это нормально при первом запуске
        
        # Пробуем разные кодировки для надежности
        encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'latin-1']
        data = None
        last_error = None
        
        for encoding in encodings:
            try:
                with open(self.settings_file, "r", encoding=encoding) as f:
                    data = json.load(f)
                logger.debug("Данные настроек успешно загружены с кодировкой %s", encoding)
                break  # Если успешно, выходим из цикла
            except UnicodeDecodeError as e:
                last_error = e
                logger.debug("Не удалось декодировать файл настроек с кодировкой %s: %s", encoding, e)
                continue
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning("Ошибка парсинга JSON настроек с кодировкой %s: %s", encoding, e)
                continue
        
        if data is None:
            error_msg = f"Не удалось загрузить данные настроек из файла {self.settings_file}"
            if last_error:
                error_msg += f": {last_error}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Восстанавливаем настройки
        settings_data = data.get("settings", {})
        
        # Создаем AppSettings с учетом миграции старых данных
        # Сначала пытаемся получить новые поля, если их нет - используем старые с миграцией
        self.app_data.settings = AppSettings(
            # Старые поля для совместимости
            cost_per_word=settings_data.get("cost_per_word", Constants.DEFAULT_COST_PER_WORD),
            penalty_per_word=settings_data.get("penalty_per_word", Constants.DEFAULT_PENALTY_PER_WORD),
            # Новые поля - приоритетные
            points_cost_per_word=settings_data.get("points_cost_per_word", 1),
            points_penalty_per_word=settings_data.get("points_penalty_per_word", 1),
            rubles_cost_per_word=settings_data.get("rubles_cost_per_word", Constants.DEFAULT_COST_PER_WORD),
            rubles_penalty_per_word=settings_data.get("rubles_penalty_per_word", Constants.DEFAULT_PENALTY_PER_WORD),
            show_correct_answer=settings_data.get("show_correct_answer", Constants.DEFAULT_SHOW_CORRECT_ANSWER),
            auto_play_enabled=settings_data.get("auto_play_enabled", Constants.AUTO_PLAY_ENABLED),
            auto_play_delay=settings_data.get("auto_play_delay", Constants.AUTO_PLAY_DELAY),
            settings_password=settings_data.get("settings_password", Constants.SETTINGS_PASSWORD),
            music_enabled=settings_data.get("music_enabled", Constants.DEFAULT_MUSIC_ENABLED),
            require_password_for_settings=settings_data.get("require_password_for_settings", True),
            repeat_mistakes=settings_data.get("repeat_mistakes", True),
            repeat_mistakes_range=settings_data.get("repeat_mistakes_range", "7-10"),
            infinite_mode=settings_data.get("infinite_mode", False),
            reward_type=settings_data.get("reward_type", "rubles")
        )
        # УБРАЛИ ВЫЗОВ migrate_used_words_to_uids() из _load_settings_data
        # Т.к. на этом этапе прогресс еще не загружен
            
    def migrate_used_words_to_uids(self):
        """Мигрирует used_words с названий слов на uid для обратной совместимости"""
        training_state = self.app_data.training_state
        
        # Если used_words пустой или уже содержит uid (цифры), пропускаем
        if not training_state.used_words:
            # Также проверяем category-specific used words
            for category in list(training_state.used_words_by_category.keys()):
                used_words_in_category = training_state.used_words_by_category[category]
                if not used_words_in_category:
                    continue
                
                # Проверяем, есть ли строковые значения (старые названия слов)
                string_words = {word for word in used_words_in_category if isinstance(word, str) and not word.isdigit()}
                
                if string_words:
                    # Мигрируем старые названия на uid
                    new_used_words = set()
                    for word_name in used_words_in_category:
                        if isinstance(word_name, str) and not word_name.isdigit():
                            # Ищем слово по названию и берем первый uid
                            for word_data in self.app_data.words:
                                if word_data.word == word_name:
                                    new_used_words.add(word_data.uid)
                                    break
                        else:
                            # Уже uid, оставляем как есть
                            new_used_words.add(word_name)
                    
                    training_state.used_words_by_category[category] = new_used_words
            self.save_data()
            return
        
        # Проверяем, есть ли строковые значения (старые названия слов)
        string_words = {word for word in training_state.used_words if isinstance(word, str) and not word.isdigit()}
        
        if string_words:
            # Мигрируем старые названия на uid
            new_used_words = set()
            for word_name in training_state.used_words:
                if isinstance(word_name, str) and not word_name.isdigit():
                    # Ищем слово по названию и берем первый uid
                    for word_data in self.app_data.words:
                        if word_data.word == word_name:
                            new_used_words.add(word_data.uid)
                            break
                else:
                    # Уже uid, оставляем как есть
                    new_used_words.add(word_name)
            
            training_state.used_words = new_used_words
        
        # Также проверяем category-specific used words
        for category in list(training_state.used_words_by_category.keys()):
            used_words_in_category = training_state.used_words_by_category[category]
            if not used_words_in_category:
                continue
            
            # Проверяем, есть ли строковые значения (старые названия слов)
            string_words = {word for word in used_words_in_category if isinstance(word, str) and not word.isdigit()}
            
            if string_words:
                # Мигрируем старые названия на uid
                new_used_words = set()
                for word_name in used_words_in_category:
                    if isinstance(word_name, str) and not word_name.isdigit():
                        # Ищем слово по названию и берем первый uid
                        for word_data in self.app_data.words:
                            if word_data.word == word_name:
                                new_used_words.add(word_data.uid)
                                break
                    else:
                        # Уже uid, оставляем как есть
                        new_used_words.add(word_name)
                
                training_state.used_words_by_category[category] = new_used_words
        
        self.save_data()

    def _rebuild_categories_from_words(self):
        """Перестраивает список категорий из всех слов, фильтруя некорректные"""
        all_categories = set()
        for word_data in self.app_data.words:
            # Фильтруем категории: убираем пустые, пробелы и одиночные символы
            valid_categories = [
                category.strip() for category in word_data.categories 
                if category and category.strip() and len(category.strip()) > 1
            ]
            all_categories.update(valid_categories)
        
        self.app_data.categories = sorted(list(all_categories))

    def save_data(self) -> bool:
        """Сохраняет данные в отдельные файлы: words.json (только слова), progress.json, settings.json"""
        try:
            # Сохраняем только слова и категории в words.json
            words_data = {
                "words": [
                    {
                        "word": word.word,
                        "categories": word.categories,  # НОВЫЙ ФОРМАТ - список категорий
                        "audio": word.audio,
                        "images": word.images,
                        "case_sensitive": word.case_sensitive,
                        "important_positions": word.important_positions,
                        "uid": word.uid  # СОХРАНЯЕМ 4-значный uid
                    }
                    for word in self.app_data.words
                ],
                "categories": self.app_data.categories
            }
            
            with open(self.words_file, "w", encoding="utf-8") as f:
                json.dump(words_data, f, ensure_ascii=False, indent=2)
            
            # Сохраняем состояние тренировки в progress.json
            # Безопасное преобразование вложенных defaultdict
            mistakes_count_dict = {}
            for category, words in self.app_data.training_state.mistakes_count.items():
                mistakes_count_dict[category] = dict(words)
                
            wrong_answers_dict = {}
            for category, words in self.app_data.training_state.wrong_answers.items():
                wrong_answers_dict[category] = dict(words)
            
            # Преобразуем used_words_by_category для сохранения
            used_words_by_category_dict = {}
            for category, words in self.app_data.training_state.used_words_by_category.items():
                used_words_by_category_dict[category] = list(words)
            
            progress_data = {
                "training_state": {
                    "points_score": self.app_data.training_state.points_score,
                    "rubles_score": self.app_data.training_state.rubles_score,
                    "used_words": list(self.app_data.training_state.used_words),
                    "used_words_by_category": used_words_by_category_dict,
                    "current_category": self.app_data.training_state.current_category,
                    "mistakes_count": mistakes_count_dict,
                    "wrong_answers": wrong_answers_dict,
                    "correct_answers_count": dict(self.app_data.training_state.correct_answers_count),
                    "incorrect_answers_count": dict(self.app_data.training_state.incorrect_answers_count),
                    # ДОБАВЛЯЕМ СОХРАНЕНИЕ СЛОВ НА ПОВТОРЕНИИ ↓
                    "repeat_words": [
                        {
                            "word_uid": rw.word_uid,
                            "category": rw.category,
                            "next_show_after": rw.next_show_after,
                            "current_attempt": rw.current_attempt,
                            "total_attempts_needed": rw.total_attempts_needed
                        }
                        for rw in self.app_data.training_state.repeat_words
                    ]
                }
            }

            # Сохраняем состояние тренировки в progress.json

            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
            # Сохраняем настройки в settings.json
            # Сохраняем все поля для обратной совместимости с существующими файлами
            # В будущем можно будет упростить, сохранив только новые поля
            settings_data = {
                "settings": {
                    # УБРАНО: Сохранение старых полей cost_per_word и penalty_per_word при сохранении
                    # Эти поля должны использоваться ТОЛЬКО для миграции старых данных при загрузке
                    # При сохранении должны сохраняться только points_cost_per_word/points_penalty_per_word и rubles_cost_per_word/rubles_penalty_per_word
                    # Новые поля - основные
                    "points_cost_per_word": self.app_data.settings.points_cost_per_word,
                    "points_penalty_per_word": self.app_data.settings.points_penalty_per_word,
                    "rubles_cost_per_word": self.app_data.settings.rubles_cost_per_word,
                    "rubles_penalty_per_word": self.app_data.settings.rubles_penalty_per_word,
                    "show_correct_answer": self.app_data.settings.show_correct_answer,
                    "auto_play_enabled": self.app_data.settings.auto_play_enabled,
                    "auto_play_delay": self.app_data.settings.auto_play_delay,
                    "settings_password": self.app_data.settings.settings_password,
                    "music_enabled": self.app_data.settings.music_enabled,
                    "require_password_for_settings": self.app_data.settings.require_password_for_settings,
                    "repeat_mistakes": self.app_data.settings.repeat_mistakes,
                    "repeat_mistakes_range": self.app_data.settings.repeat_mistakes_range,
                    "infinite_mode": self.app_data.settings.infinite_mode,
                    "reward_type": self.app_data.settings.reward_type
                }
            }
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.exception("Ошибка сохранения данных: %s", e)
            return False
    
    def add_category_to_word(self, word_data: WordData, category: str):
        """Добавляет категорию к слову"""
        if category and category not in word_data.categories:
            word_data.categories.append(category)
            # Обновляем общий список категорий
            if category not in self.app_data.categories:
                self.app_data.categories.append(category)
                self.app_data.categories.sort()
    
    def remove_category_from_word(self, word_data: WordData, category: str):
        """Удаляет категорию из слова"""
        # Безопасное удаление: проверяем наличие перед удалением
        if category in word_data.categories:
            word_data.categories.remove(category)
            # Проверяем, нужно ли удалить категорию из общего списка
            self._cleanup_unused_categories()
    
    def update_word_categories(self, word_data: WordData, new_categories: List[str]):
        """Обновляет список категорий слова"""
        word_data.categories = new_categories
        # Обновляем общий список категорий
        for category in new_categories:
            if category not in self.app_data.categories:
                self.app_data.categories.append(category)
        self.app_data.categories.sort()
        # Очищаем неиспользуемые категории
        self._cleanup_unused_categories()
    
    def _cleanup_unused_categories(self):
        """
        Удаляет категории, которые не используются ни в одном слове.
        
        Оптимизация: использует set для O(1) проверки принадлежности.
        """
        # Собираем все используемые категории в set для быстрого поиска
        used_categories = set()
        for word_data in self.app_data.words:
            used_categories.update(word_data.categories)
        
        # Фильтруем категории, оставляя только используемые
        self.app_data.categories = [cat for cat in self.app_data.categories if cat in used_categories]
        self.app_data.categories.sort()
    
    def _cleanup_invalid_categories_only_no_save(self):
        """
        Очищает некорректные категории из всех слов и общего списка БЕЗ СОХРАНЕНИЯ
        """
        # Очищаем категории в словах
        for word_data in self.app_data.words:
            word_data.categories = [
                category for category in word_data.categories
                if category and category.strip() and len(category.strip()) > 1
            ]
            # Удаляем дубликаты категорий в одном слове
            word_data.categories = list(set(word_data.categories))
        
        # Перестраиваем общий список категорий
        self._rebuild_categories_from_words()
        
    def cleanup_invalid_categories(self):
        """Очищает некорректные категории из всех слов и общего списка"""
        # Очищаем категории в словах
        for word_data in self.app_data.words:
            word_data.categories = [
                category for category in word_data.categories 
                if category and category.strip() and len(category.strip()) > 1
            ]
            # Удаляем дубликаты категорий в одном слове
            word_data.categories = list(set(word_data.categories))
        
        # Перестраиваем общий список категорий
        self._rebuild_categories_from_words()
        self.save_data()
    
    def get_available_words(self, category: str) -> List[WordData]:
        """Возвращает доступные слова категории (ещё не использованные)"""
        training_state = self.app_data.training_state
        
        if category == "Все":
            # Для режима "Все" возвращаем все неиспользованные слова
            used_words = training_state.used_words
            return [word for word in self.app_data.words if word.uid not in used_words]
        
        words_in_category = self.get_words_by_category(category)
        # Для конкретной категории используем category-specific used_words
        used_words_in_category = training_state.used_words_by_category[category]
        # Оптимизация: used_words_in_category уже set, поэтому поиск O(1)
        return [word for word in words_in_category if word.uid not in used_words_in_category]
    
    def add_word(self, word_data: WordData):
        """
        Добавляет новое слово в репозиторий.
        
        Args:
            word_data: Данные слова для добавления
            
        Note:
            Автоматически генерирует uid если он отсутствует.
            Обновляет список категорий при необходимости.
        """
        # Гарантируем что у слова есть 4-значный uid
        existing_uids = {word.uid for word in self.app_data.words if getattr(word, 'uid', None)}
        if not word_data.uid:
            word_data.uid = self._generate_numeric_uid(existing_uids)
        
        self.app_data.words.append(word_data)
        # Оптимизация: используем set для быстрой проверки категорий
        categories_set = set(self.app_data.categories)
        for category in word_data.categories:
            if category not in categories_set:
                self.app_data.categories.append(category)
                categories_set.add(category)
        self.app_data.categories.sort()
    
    def update_word(self, index: int, word_data: WordData):
        """
        Обновляет существующее слово по индексу.
        
        Args:
            index: Индекс слова в списке
            word_data: Новые данные слова
            
        Note:
            Сохраняет оригинальный uid слова.
            Обновляет список категорий при необходимости.
        """
        if 0 <= index < len(self.app_data.words):
            # Сохраняем uid при обновлении
            original_uid = self.app_data.words[index].uid
            word_data.uid = original_uid
            
            self.app_data.words[index] = word_data
            # Оптимизация: используем set для быстрой проверки категорий
            categories_set = set(self.app_data.categories)
            for category in word_data.categories:
                if category not in categories_set:
                    self.app_data.categories.append(category)
                    categories_set.add(category)
            self.app_data.categories.sort()
            # Очищаем неиспользуемые категории
            self._cleanup_unused_categories()
            
    def delete_word(self, index: int):
        """Удаляет слово по индексу"""
        if 0 <= index < len(self.app_data.words):
            # Получаем данные слова для удаления медиафайлов
            word_data = self.app_data.words[index]
            
            # Удаляем медиафайлы через media_manager если он установлен
            if self.media_manager is not None:
                self.media_manager.delete_media_files(word_data)
            
            # Удаляем слово из списка
            del self.app_data.words[index]
            
            # Обновляем категории (удаляем неиспользуемые)
            self._cleanup_unused_categories()
            
            # Сохраняем изменения
            self.save_data()
    
    def add_category(self, category: str):
        """Добавляет новую категорию"""
        if category and category not in self.app_data.categories:
            self.app_data.categories.append(category)
            self.app_data.categories.sort()
    
    def delete_category(self, category: str, force: bool = False) -> Dict[str, Any]:
        """
        Удаляет категорию с проверкой условий
        
        Args:
            category: Название категории для удаления
            force: Принудительное удаление (игнорировать проверки)
            
        Returns:
            Словарь с результатом операции
        """
        if category not in self.app_data.categories:
            return {
                'success': False,
                'message': f"Категория '{category}' не существует",
                'words_affected': 0,
                'words_with_single_category': 0
            }
        
        # Получаем статистику
        words_in_category = self.get_words_in_category(category)
        words_with_single_category = self.get_words_with_single_category(category)
        
        if not force:
            # Проверяем, есть ли слова с этой единственной категорией
            if words_with_single_category:
                return {
                    'success': False,
                    'message': f"Невозможно удалить категорию '{category}'. "
                              f"Она является единственной для {len(words_with_single_category)} слов.",
                    'words_affected': len(words_in_category),
                    'words_with_single_category': len(words_with_single_category)
                }
        
        # Если проверки пройдены или force=True, удаляем категорию
        updated_count = self.remove_category_from_all_words(category)
        
        # ИСПРАВЛЕНИЕ: Очищаем состояние тренировки для удаляемой категории
        training_state = self.app_data.training_state
        
        # Если удаляемая категория была текущей, сбрасываем текущую категорию
        if training_state.current_category == category:
            training_state.current_category = ""
            if self.app_data.categories and category in self.app_data.categories:
                # Выбираем другую категорию (первую доступную, кроме удаляемой)
                other_categories = [cat for cat in self.app_data.categories if cat != category]
                if other_categories:
                    training_state.current_category = other_categories[0]
        
        # Очищаем статистику для удаляемой категории
        if category in training_state.mistakes_count:
            del training_state.mistakes_count[category]
        if category in training_state.wrong_answers:
            del training_state.wrong_answers[category]
        if category in training_state.correct_answers_count:
            del training_state.correct_answers_count[category]
        if category in training_state.incorrect_answers_count:
            del training_state.incorrect_answers_count[category]
        
        # Удаляем использованные слова, которые принадлежали только к удаляемой категории
        words_to_remove = set()
        for word_uid in training_state.used_words:
            # Находим слово по uid
            word_data = self.get_word_by_uid(word_uid)
            if word_data and category in word_data.categories and len(word_data.categories) == 1:
                words_to_remove.add(word_uid)
        training_state.used_words -= words_to_remove
        
        # Также удаляем использованные слова для удаляемой категории
        if category in training_state.used_words_by_category:
            del training_state.used_words_by_category[category]
        
        # Удаляем категорию из общего списка (безопасное удаление)
        if category in self.app_data.categories:
            self.app_data.categories.remove(category)
        
        # Очищаем неиспользуемые категории
        self._cleanup_unused_categories()
        
        self.save_data()
        
        return {
            'success': True,
            'message': f"Категория '{category}' удалена. Обновлено слов: {updated_count}",
            'words_affected': updated_count,
            'words_with_single_category': len(words_with_single_category)
        }
    
    def has_words_in_category(self, category: str) -> bool:
        """Проверяет есть ли слова в категории"""
        return any(category in word.categories for word in self.app_data.words)
        
    def get_words_by_category(self, category: str) -> List[WordData]:
        """Возвращает слова указанной категории"""
        if not category:
            return []
        return [word for word in self.app_data.words if category in word.categories]
        
    def get_words_in_category(self, category: str) -> List[WordData]:
        """Возвращает все слова в указанной категории"""
        return [word for word in self.app_data.words if category in word.categories]

    def get_words_with_single_category(self, category: str) -> List[WordData]:
        """Возвращает слова, у которых указанная категория является единственной"""
        words_in_category = self.get_words_in_category(category)
        return [word for word in words_in_category if len(word.categories) == 1]

    def remove_category_from_all_words(self, category: str) -> int:
        """Удаляет категорию из всех слов и возвращает количество обновленных слов"""
        updated_count = 0
        for word_data in self.app_data.words:
            # Безопасное удаление: проверяем наличие перед удалением
            if category in word_data.categories:
                word_data.categories.remove(category)
                updated_count += 1
        return updated_count
        
    def get_category_stats(self, category: str) -> Dict[str, Any]:
        """Возвращает статистику по категории"""
        words_in_category = self.get_words_in_category(category)
        words_with_single_category = self.get_words_with_single_category(category)
        words_with_multiple_categories = len(words_in_category) - len(words_with_single_category)
        
        return {
            'total_words': len(words_in_category),
            'words_with_single_category': len(words_with_single_category),
            'words_with_multiple_categories': words_with_multiple_categories,
            'can_be_deleted': len(words_with_single_category) == 0
        }
        
    def word_exists(self, word: str, exclude_uid: str = None) -> bool:
        """
        Проверяет существование слова (без учета регистра)
        
        Args:
            word: Слово для проверки
            exclude_uid: UID слова, которое исключаем из проверки (для редактирования)
        """
        word_lower = word.lower()
        for word_data in self.app_data.words:
            if exclude_uid and word_data.uid == exclude_uid:
                continue
            if word_data.word.lower() == word_lower:
                return True
        return False

    def get_word_by_uid(self, uid: str) -> Optional[WordData]:
        """Находит слово по уникальному идентификатору"""
        for word in self.app_data.words:
            if word.uid == uid:
                return word
        return None

    def find_duplicate_words(self, word: str, exclude_uid: str = None) -> List[WordData]:
        """
        Находит все слова с таким же написанием (без учета регистра)
        """
        word_lower = word.lower()
        duplicates = []
        for word_data in self.app_data.words:
            if exclude_uid and word_data.uid == exclude_uid:
                continue
            if word_data.word.lower() == word_lower:
                duplicates.append(word_data)
        return duplicates
        
    def _generate_numeric_uid(self, existing_uids: set) -> str:
        """
        Генерирует уникальный 4-значный числовой идентификатор
        
        Args:
            existing_uids: Множество существующих uid
            
        Returns:
            Уникальный 4-значный uid
        """
        import random
        
        # Пробуем сгенерировать случайный uid
        for _ in range(1000):  # Ограничим попытки
            new_uid = str(random.randint(1000, 9999))  # 4-значное число
            if new_uid not in existing_uids:
                return new_uid
        
        # Если случайная генерация не удалась, ищем первый доступный
        for i in range(1000, 10000):
            candidate = str(i)
            if candidate not in existing_uids:
                return candidate
        
        # В крайнем случае используем timestamp (маловероятно что будет 9000 слов)
        return str(int(time.time() * 1000))[-4:].zfill(4)