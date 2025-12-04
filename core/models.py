"""Модели данных приложения"""
import uuid
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass
class WordData:
    """Данные одного слова"""
    word: str
    categories: List[str] = field(default_factory=list)
    audio: str = ""
    images: List[str] = field(default_factory=list)
    case_sensitive: bool = False
    important_positions: str = ""
    uid: str = ""
    
    def __post_init__(self):
        """Валидация данных после инициализации"""
        # Проверяем, что слово не пустое
        if not self.word or not self.word.strip():
            raise ValueError("Word cannot be empty or whitespace")
        
        # Нормализуем слово (убираем лишние пробелы)
        self.word = self.word.strip()
        
        # Проверяем категории (убираем пустые и дубликаты)
        self.categories = [cat.strip() for cat in self.categories if cat and cat.strip()]
        self.categories = list(dict.fromkeys(self.categories))  # Убираем дубликаты с сохранением порядка
        
        # Нормализуем important_positions
        if self.important_positions:
            self.important_positions = self.important_positions.strip()

@dataclass
class AppSettings:
    """Настройки приложения"""
    # Старые поля для совместимости (временно сохраняем для миграции)
    cost_per_word: float = 0.5
    penalty_per_word: float = 0.25
    # Новые отдельные поля для баллов и рублей
    points_cost_per_word: int = 1      # Награда в баллах за слово
    points_penalty_per_word: int = 1   # Штраф в баллах за ошибку
    rubles_cost_per_word: float = 0.5  # Награда в рублях за слово
    rubles_penalty_per_word: float = 0.25  # Штраф в рублях за ошибку
    show_correct_answer: bool = True
    auto_play_enabled: bool = True
    auto_play_delay: int = 500
    settings_password: str = "1234"
    music_enabled: bool = True
    require_password_for_settings: bool = True  # Новое: требовать пароль для настроек
    repeat_mistakes: bool = True               # Новое: повторять ошибки
    repeat_mistakes_range: str = "7-10"        # Новое: диапазон повторения
    infinite_mode: bool = False                # Новое: бесконечный режим
    reward_type: str = "rubles"                # Новое: тип награды ("rubles" или "points")
    
    def __post_init__(self):
        """Валидация настроек после инициализации"""
        # Выполняем миграцию старых значений к новым, если новые не заданы явно
        self._migrate_old_values()
        
        # Проверяем, что награда и штраф неотрицательные
        # Эти поля используются ТОЛЬКО для миграции старых данных при загрузке
        # и не должны обновляться при сохранении настроек
        if self.cost_per_word < 0:
            self.cost_per_word = 0.5  # Возвращаем к значению по умолчанию
        if self.penalty_per_word < 0:
            self.penalty_per_word = 0.25  # Возвращаем к значению по умолчанию
        
        # Валидация новых полей для баллов
        if self.points_cost_per_word < 0:
            self.points_cost_per_word = 1  # Возвращаем к значению по умолчанию
        if self.points_penalty_per_word < 0:
            self.points_penalty_per_word = 1  # Возвращаем к значению по умолчанию
            
        # Валидация новых полей для рублей
        if self.rubles_cost_per_word < 0:
            self.rubles_cost_per_word = 0.5  # Возвращаем к значению по умолчанию
        if self.rubles_penalty_per_word < 0:
            self.rubles_penalty_per_word = 0.25  # Возвращаем к значению по умолчанию
        
        # Проверяем задержку автовоспроизведения
        if self.auto_play_delay < 0:
            self.auto_play_delay = 500  # Возвращаем к значению по умолчанию
        if self.auto_play_delay > 10000:  # Максимум 10 секунд
            self.auto_play_delay = 500  # Возвращаем к значению по умолчанию
        
        # Нормализуем пароль (убираем пробелы)
        if self.settings_password:
            self.settings_password = self.settings_password.strip()
        else:
            self.settings_password = "1234"  # Возвращаем к значению по умолчанию
            
        # Проверяем формат диапазона повторения
        if self.repeat_mistakes_range:
            try:
                min_val, max_val = map(int, self.repeat_mistakes_range.split('-'))
                if min_val < 1 or max_val < min_val:
                    # Если диапазон неверный, используем значение по умолчанию
                    self.repeat_mistakes_range = "7-10"
            except (ValueError, AttributeError):
                # Если формат неверный, используем значение по умолчанию
                self.repeat_mistakes_range = "7-10"
                
    def _migrate_old_values(self):
        """Миграция старых значений к новым полям"""
        # Если новые значения не были установлены (остались по умолчанию),
        # но есть старые значения, мигрируем старые в новые
        # Проверяем, были ли новые значения изменены от значений по умолчанию
        default_points_cost = 1
        default_points_penalty = 1
        default_rubles_cost = 0.5
        default_rubles_penalty = 0.25
        
        # Если все новые поля имеют значения по умолчанию, а старые отличаются от своих значений по умолчанию,
        # то выполняем миграцию
        if (self.points_cost_per_word == default_points_cost and
            self.points_penalty_per_word == default_points_penalty and
            self.rubles_cost_per_word == default_rubles_cost and
            self.rubles_penalty_per_word == default_rubles_penalty and
            (self.cost_per_word != 0.5 or self.penalty_per_word != 0.25)):
            
            # Мигрируем старые значения в новые поля
            # Для баллов - округляем до целых
            self.points_cost_per_word = int(self.cost_per_word) if self.cost_per_word.is_integer() else round(self.cost_per_word)
            self.points_penalty_per_word = int(self.penalty_per_word) if self.penalty_per_word.is_integer() else round(self.penalty_per_word)
            # Для рублей - сохраняем как дробные
            self.rubles_cost_per_word = self.cost_per_word
            self.rubles_penalty_per_word = self.penalty_per_word
                
                
@dataclass
class RepeatWordData:
    """Данные слова для повторения"""
    word_uid: str
    category: str
    next_show_after: int  # через сколько слов показать
    current_attempt: int = 1  # текущая попытка (1, 2, 3)
    total_attempts_needed: int = 3  # всего нужно попыток
    
    def __post_init__(self):
        """Валидация данных"""
        # ИСПРАВЛЯЕМ: разрешаем 0 и отрицательные значения для next_show_after ↓
        # Эти значения означают что слово готово к показу
        if self.current_attempt < 1 or self.current_attempt > self.total_attempts_needed:
            raise ValueError("current_attempt должен быть от 1 до total_attempts_needed")
                

@dataclass
class TrainingState:
    """Состояние тренировки"""
    score: float = 0.0  # Legacy field for backward compatibility
    points_score: int = 0  # Separate points account
    rubles_score: float = 0.0  # Separate rubles account
    # ГЛОБАЛЬНЫЙ список использованных слов для совместимости
    used_words: Set[str] = field(default_factory=set)
    # ОТДЕЛЬНЫЙ список использованных слов для каждой категории
    used_words_by_category: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    current_word: WordData = None
    current_category: str = ""
    # ОТДЕЛЬНЫЕ счетчики ошибок для каждой категории
    mistakes_count: Dict[str, Dict[str, int]] = field(default_factory=dict)
    wrong_answers: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    # ОТДЕЛЬНЫЕ счетчики правильных/неправильных ответов для каждой категории
    correct_answers_count: Dict[str, int] = field(default_factory=dict)
    incorrect_answers_count: Dict[str, int] = field(default_factory=dict)
    # ДОБАВЛЯЕМ ПОЛЕ ДЛЯ СЛОВ НА ПОВТОРЕНИИ ↓
    repeat_words: List[RepeatWordData] = field(default_factory=list)
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        # Если score не равен 0, а другие счеты равны 0, переносим значение из старого поля
        if self.score != 0.0 and self.points_score == 0 and self.rubles_score == 0.0:
            # Предполагаем, что если score целое число, то это были баллы, иначе - рубли
            if isinstance(self.score, float) and self.score.is_integer():
                self.points_score = int(self.score)
            else:
                self.rubles_score = float(self.score)
            # Обнуляем старое поле
            self.score = 0.0
        
        # Инициализируем used_words_by_category как defaultdict если пустой
        # Это будет работать корректно благодаря field(default_factory=lambda: defaultdict(set))
    
    def increment_correct(self, category: str):
        """Увеличивает счётчик правильных ответов категории"""
        if not category:
            return
        self.correct_answers_count[category] = self.correct_answers_count.get(category, 0) + 1

    def increment_incorrect(self, category: str):
        """Увеличивает счётчик неправильных ответов категории"""
        if not category:
            return
        self.incorrect_answers_count[category] = self.incorrect_answers_count.get(category, 0) + 1

    def increment_mistake(self, category: str, word: str):
        """Увеличивает количество ошибок для слова в категории"""
        if not category or not word:
            return
        category_mistakes = self.mistakes_count.setdefault(category, {})
        category_mistakes[word] = category_mistakes.get(word, 0) + 1

    def add_wrong_answer(self, category: str, word: str, answer: str):
        """Добавляет неправильный ответ для слова"""
        if not category or not word or not answer:
            return
        words_wrong_answers = self.wrong_answers.setdefault(category, {})
        answers = words_wrong_answers.setdefault(word, [])
        if answer not in answers:
            answers.append(answer)
    
    def reset_progress(self, category: str = None):
        """Сброс прогресса по словам для конкретной категории или всех"""
        if category:
            # Сброс только для указанной категории
            if category in self.mistakes_count:
                del self.mistakes_count[category]
            if category in self.wrong_answers:
                del self.wrong_answers[category]
            if category in self.correct_answers_count:
                del self.correct_answers_count[category]
            if category in self.incorrect_answers_count:
                del self.incorrect_answers_count[category]
            # Удаляем слова на повторении этой категории
            self.repeat_words = [rw for rw in self.repeat_words if rw.category != category]
            # Удаляем использованные слова только этой категории
            if category in self.used_words_by_category:
                del self.used_words_by_category[category]
        else:
            # Сброс для всех категорий
            self.used_words.clear()
            self.used_words_by_category.clear()
            self.mistakes_count.clear()
            self.wrong_answers.clear()
            self.correct_answers_count.clear()
            self.incorrect_answers_count.clear()
            self.repeat_words.clear()  # Очищаем слова на повторении
            
    def add_word_for_repetition(self, word_uid: str, category: str, repeat_range: str):
        """Добавляет слово для повторения"""
        try:
            min_val, max_val = map(int, repeat_range.split('-'))
            next_show_after = random.randint(min_val, max_val)
            
            repeat_word = RepeatWordData(
                word_uid=word_uid,
                category=category,
                next_show_after=next_show_after,
                current_attempt=1
            )
            
            self.repeat_words.append(repeat_word)
        except (ValueError, AttributeError):
            # Если ошибка в формате диапазона, используем значения по умолчанию
            next_show_after = random.randint(7, 10)
            repeat_word = RepeatWordData(
                word_uid=word_uid,
                category=category,
                next_show_after=next_show_after,
                current_attempt=1
            )
            self.repeat_words.append(repeat_word)
    
    def get_words_ready_for_repetition(self) -> List[RepeatWordData]:
        """Возвращает слова, готовые для повторения (next_show_after <= 0)"""
        ready_words = [rw for rw in self.repeat_words if rw.next_show_after <= 0]
        return ready_words
    
    def decrement_repeat_counters(self):
        """Уменьшает счетчики для всех слов на повторении"""
        for repeat_word in self.repeat_words:
            if repeat_word.next_show_after > 0:
                repeat_word.next_show_after -= 1
    
    def update_repeat_word_after_attempt(self, word_uid: str, category: str,
                                       repeat_range: str, is_correct: bool):
        """Обновляет слово после попытки повторения"""
        # Сначала ищем слово для повторения в той же категории
        for repeat_word in self.repeat_words:
            if (repeat_word.word_uid == word_uid and
                repeat_word.category == category):
                
                if repeat_word.current_attempt >= repeat_word.total_attempts_needed:
                    # Достигли максимального количества попыток - удаляем слово
                    self.repeat_words.remove(repeat_word)
                else:
                    # Увеличиваем счетчик попыток и устанавливаем новый интервал
                    repeat_word.current_attempt += 1
                    try:
                        min_val, max_val = map(int, repeat_range.split('-'))
                        repeat_word.next_show_after = random.randint(min_val, max_val)
                    except (ValueError, AttributeError):
                        repeat_word.next_show_after = random.randint(7, 10)
                return  # Завершаем после обновления найденного слова
        
        # Если слово не найдено в той же категории, ищем его в других категориях
        # Это решает проблему, когда слово было добавлено в повтор из одной категории,
        # но пользователь отвечает на него в другой категории
        for repeat_word in self.repeat_words:
            if repeat_word.word_uid == word_uid:
                
                if repeat_word.current_attempt >= repeat_word.total_attempts_needed:
                    # Достигли максимального количества попыток - удаляем слово
                    self.repeat_words.remove(repeat_word)
                else:
                    # Увеличиваем счетчик попыток и устанавливаем новый интервал
                    repeat_word.current_attempt += 1
                    try:
                        min_val, max_val = map(int, repeat_range.split('-'))
                        repeat_word.next_show_after = random.randint(min_val, max_val)
                    except (ValueError, AttributeError):
                        repeat_word.next_show_after = random.randint(7, 10)
                break
    
    def reset_score(self, reward_type: str = "rubles"):
        """Сброс общего счёта"""
        if reward_type == "points":
            self.points_score = 0
        else:  # rubles or default
            self.rubles_score = 0.0
        # НЕ сбрасываем счетчики правильных/неправильных ответов при обнулении счета

    def get_current_score(self, reward_type: str = "rubles") -> float:
        """Получение текущего счёта в зависимости от типа награды"""
        if reward_type == "points":
            return float(self.points_score)
        else:  # rubles or default
            return self.rubles_score

    def set_current_score(self, value: float, reward_type: str = "rubles"):
        """Установка текущего счёта в зависимости от типа награды"""
        if reward_type == "points":
            self.points_score = int(value)
        else:  # rubles or default
            self.rubles_score = value


@dataclass
class AppData:
    """Все данные приложения"""
    words: List[WordData] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    training_state: TrainingState = field(default_factory=TrainingState)
    settings: AppSettings = field(default_factory=AppSettings)