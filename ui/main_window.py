"""Главное окно приложения"""
import os
import random
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QLineEdit, QComboBox,
                               QMessageBox, QGroupBox, QInputDialog, QApplication, QSizePolicy, QFrame, QDialog)
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer, QSize

from core.constants import Constants
from core.models import WordData, RepeatWordData
from core.media_manager import MediaManager
from core.audio_service import AudioService
from core.music_service import MusicService
from core.word_repository import WordRepository
from utils.helpers import show_silent_message, create_scaled_pixmap
from ui.dialogs.word_management.word_dialogs import WordManagerDialog, WordEditorDialog, CategoryMoveDialog
from ui.dialogs.statistics.statistics_dialogs import ProblemWordsDialog
from ui.dialogs.settings.settings_dialogs import SettingsDialog
from ui.dialogs.auth.password_dialogs import ChangePasswordDialog
from ui.dialogs.import_export.data_dialogs import BulkImportDialog, ExportCategoriesDialog
from ui.menu_bar import MenuBar

class SpellingTrainer(QMainWindow):
    """Главное окно тренажёра орфографии"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orfocode")
        self.setGeometry(100, 100, *Constants.DEFAULT_WINDOW_SIZE)
        
        # Получаем абсолютный путь к папке с программой
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Инициализация компонентов
        self._init_components()
        
        # Создание интерфейса
        self.setFixedSize(630, 700)
        self.create_ui()
        
        # Центрируем главное окно
        self.center_window()
        
        # Добавляем флаг блокировки автоматической загрузки слов
        self.block_auto_load = False
        
        # ДОБАВЬТЕ ЭТУ СТРОКУ - инициализация флага подключения сигнала
        self.category_signal_connected = False
        
        # Вызываем validate_current_category ПОСЛЕ создания UI
        self._validate_current_category()
        
        # Загрузка первого слова
        self.load_next_word()
        
        # Обновляем UI с загруженными данными
        self.update_score()
        self._update_words_counter()
        
    def center_window(self):
        """Центрирование главного окна на экране"""
        # Получаем геометрию экрана
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        
        # Получаем геометрию окна
        window_geometry = self.frameGeometry()
        
        # Находим центр экрана
        center_point = screen_geometry.center()
        
        # Перемещаем центр окна в центр экрана
        window_geometry.moveCenter(center_point)
        
        # Перемещаем окно в новую позицию
        self.move(window_geometry.topLeft())
    
    def _init_components(self):
        """Инициализация всех компонентов приложения"""
        # Основные сервисы
        # Используем get_data_directory() для определения базовой директории для MediaManager и WordRepository
        data_dir = Constants.get_data_directory()
        self.media_manager = MediaManager(data_dir)
        self.audio_service = AudioService(self.base_dir)
        self.word_repository = WordRepository(data_dir)
        self.music_service = MusicService(self.base_dir)
        
        # Устанавливаем media_manager в word_repository
        self.word_repository.set_media_manager(self.media_manager)
        
        # Загружаем данные
        success = self.word_repository.load_data()
        
        # ИСПРАВЛЕНИЕ: Устанавливаем категорию по умолчанию если нет текущей
        training_state = self.word_repository.app_data.training_state
        if not training_state.current_category and self.word_repository.app_data.categories:
            training_state.current_category = self.word_repository.app_data.categories[0]
            # НЕ сохраняем изменения при загрузке - это перезапишет загруженные данные
        
        # Загружаем настройки из репозитория
        settings = self.word_repository.app_data.settings
        # Инициализируем reward_type до его использования
        self.reward_type = settings.reward_type
        # Используем новые поля в зависимости от типа награды
        if self.reward_type == "points":
            self.cost_per_word = settings.points_cost_per_word
            self.penalty_per_word = settings.points_penalty_per_word
        else:  # rubles
            self.cost_per_word = settings.rubles_cost_per_word
            self.penalty_per_word = settings.rubles_penalty_per_word
        self.show_correct_answer = settings.show_correct_answer
        self.auto_play_enabled = settings.auto_play_enabled
        self.auto_play_delay = settings.auto_play_delay
        self.require_password_for_settings = settings.require_password_for_settings
        self.repeat_mistakes = settings.repeat_mistakes
        self.repeat_mistakes_range = settings.repeat_mistakes_range
        self.infinite_mode = settings.infinite_mode
        self.music_enabled = settings.music_enabled
        self.answer_checked = False
        
        # Таймер для автоматического перехода
        self.auto_next_timer = QTimer()
        self.auto_next_timer.setSingleShot(True)
        self.auto_next_timer.timeout.connect(self.load_next_word)
        
        # Таймер для автоматического воспроизведения звука
        self.auto_play_timer = QTimer()
        self.auto_play_timer.setSingleShot(True)
        self.auto_play_timer.timeout.connect(self._auto_play_audio)
        
        # Текущее состояние
        self.current_word_data = None
        self.current_audio_file = ""
        
        # Добавляем флаг блокировки автоматической загрузки слов
        self.block_auto_load = False
        
        # Флаг первого запуска - чтобы звук не проигрывался при старте программы
        self.is_first_load = True
        
        # Запускаем музыку если включена
        if self.music_enabled:
            self.music_service.set_music_enabled(True)
    
    def _auto_play_audio(self):
        """Автоматическое воспроизведение звука через заданную задержку"""
        if (self.auto_play_enabled and
            self.current_word_data and
            self.current_audio_file and
            not self.answer_checked):  # Только если ответ еще не проверен
            self.audio_service.play_word_audio(self.current_audio_file, self.media_manager.audio_folder)
    
    def create_ui(self):
        """Создание пользовательского интерфейса"""
        # Создание меню бара
        self.menu_bar = MenuBar(self)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Верхняя панель с настройками и счетом
        self._create_top_panel(layout)
        
        # Область категории (по центру)
        self._create_category_area(layout)
        
        # ИСПРАВЛЕНИЕ: Обновляем категорию после создания UI
        self._validate_current_category()
        
        # Область для медиа
        self._create_media_area(layout)
        
        # Область для индикаторов результата
        self._create_result_area(layout)
        
        # Область ввода ответа (по центру)
        self._create_answer_area(layout)
        
        # Обновляем состояние кнопки музыки после создания UI
        if self.music_btn:
            self._update_music_button_state()
    
    def _create_top_panel(self, layout):
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        # ЛЕВАЯ ЧАСТЬ: управление счетом (единый счёт с переключением типа)
        score_layout = QHBoxLayout()
        score_layout.setContentsMargins(0, 0, 0, 0)

        # Рамка для счёта (баллы или рубли)
        score_frame = QFrame()
        score_frame_layout = QHBoxLayout()
        score_frame_layout.setContentsMargins(10, 1, 10, 1)
        score_frame_layout.setSpacing(8)

        score_frame.setLayout(score_frame_layout)
        score_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFEF7;
                border: 1px solid #FFCC00;
                border-radius: 8px;
            }
            QLabel {
                color: #303030;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)

        # Кнопка "обнулить счёт"
        self.reset_score_btn = QPushButton()
        reset_score_icon_path = os.path.join(self.base_dir, Constants.RESET_SCORE_ICON)
        if os.path.exists(reset_score_icon_path):
            icon = QIcon(reset_score_icon_path)
            self.reset_score_btn.setIcon(icon)
            self.reset_score_btn.setIconSize(QSize(20, 20))
            self.reset_score_btn.setToolTip("Обнулить счёт")
        else:
            self.reset_score_btn.setText("⟲")
        
        self.reset_score_btn.clicked.connect(self.reset_score)
        self.reset_score_btn.setFixedSize(24, 24)

        # Метка счёта (баллы или рубли в зависимости от настроек)
        training_state = self.word_repository.app_data.training_state
        current_score = training_state.get_current_score(self.reward_type)
        if self.reward_type == "points":
            score_text = f"{int(current_score)} балл"
        else:
            score_text = f"{current_score:.2f} руб."
        self.score_label = QLabel(score_text)
        score_font = QFont()
        score_font.setPointSize(12)
        score_font.setBold(True)
        self.score_label.setFont(score_font)
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setMinimumWidth(80)
        self.score_label.setMaximumWidth(120)

        # Добавляем кнопку и счёт в рамку
        score_frame_layout.addWidget(self.reset_score_btn)
        score_frame_layout.addWidget(self.score_label)

        score_layout.addWidget(score_frame)
        top_layout.addLayout(score_layout)
        
        # Разделитель между группами
        top_layout.addSpacing(10)
        
        # ЦЕНТРАЛЬНАЯ ЧАСТЬ: прогресс и статистика в две строки
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)  # Маленький отступ между строками
        
        # ВЕРХНЯЯ СТРОКА: прогресс
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.words_counter_label = QLabel("Пройдено: 0 из 0")
        counter_font = QFont()
        counter_font.setPointSize(10)
        counter_font.setBold(False)
        self.words_counter_label.setFont(counter_font)
        self.words_counter_label.setStyleSheet("""
            QLabel {
                color: #303030;
            }
        """)
        progress_layout.addWidget(self.words_counter_label)
        progress_layout.addStretch()  # Выравнивание по левому краю
        
        center_layout.addLayout(progress_layout)
        
        # НИЖНЯЯ СТРОКА: счётчики правильных/неправильных ответов
        answers_layout = QHBoxLayout()
        answers_layout.setContentsMargins(0, 0, 0, 0)
        answers_layout.setSpacing(10)  # Отступ между счетчиками
        
        # Верно с иконкой
        self.correct_counter_layout = QHBoxLayout()
        self.correct_counter_layout.setContentsMargins(0, 0, 0, 0)
        self.correct_icon_label = QLabel()
        correct_icon_path = os.path.join(self.base_dir, "icons/counter_correct.png")
        pixmap = create_scaled_pixmap(correct_icon_path, 16, 16)
        if pixmap:
            self.correct_icon_label.setPixmap(pixmap)
        self.correct_counter_label = QLabel("Верно: 0")
        self.correct_counter_label.setFont(counter_font)
        self.correct_counter_label.setTextFormat(Qt.RichText)
        self.correct_counter_layout.addWidget(self.correct_icon_label)
        self.correct_counter_layout.addWidget(self.correct_counter_label)
        answers_layout.addLayout(self.correct_counter_layout)
        
        # Ошибки с иконкой
        self.incorrect_counter_layout = QHBoxLayout()
        self.incorrect_counter_layout.setContentsMargins(0, 0, 0, 0)
        self.incorrect_icon_label = QLabel()
        incorrect_icon_path = os.path.join(self.base_dir, "icons/counter_incorrect.png")
        pixmap = create_scaled_pixmap(incorrect_icon_path, 16, 16)
        if pixmap:
            self.incorrect_icon_label.setPixmap(pixmap)
        self.incorrect_counter_label = QLabel("Ошибки: 0")
        self.incorrect_counter_label.setFont(counter_font)
        self.incorrect_counter_label.setTextFormat(Qt.RichText)
        self.incorrect_counter_layout.addWidget(self.incorrect_icon_label)
        self.incorrect_counter_layout.addWidget(self.incorrect_counter_label)
        answers_layout.addLayout(self.incorrect_counter_layout)
        
        answers_layout.addStretch()  # Выравнивание по левому краю
        center_layout.addLayout(answers_layout)
        
        top_layout.addLayout(center_layout)
        
        # Большой разделитель для отступа до правой части
        top_layout.addStretch()
        
        # ПРАВАЯ ЧАСТЬ: основные действия с иконками (оставляем как есть)
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        # Кнопка "сбросить прогресс" с иконкой
        self.reset_progress_btn = QPushButton()
        reset_progress_icon_path = os.path.join(self.base_dir, Constants.RESET_PROGRESS_ICON)
        if os.path.exists(reset_progress_icon_path):
            icon = QIcon(reset_progress_icon_path)
            self.reset_progress_btn.setIcon(icon)
            self.reset_progress_btn.setIconSize(QSize(28, 28))
            self.reset_progress_btn.setToolTip("Сбросить прогресс")
        else:
            self.reset_progress_btn.setText("Сбросить прогресс")
        self.reset_progress_btn.clicked.connect(self.reset_progress)
        self.reset_progress_btn.setFixedSize(45, 35)
        actions_layout.addWidget(self.reset_progress_btn)
        
        # Кнопка "проблемные слова" с иконкой
        self.problem_btn = QPushButton()
        mistake_icon_path = os.path.join(self.base_dir, Constants.MISTAKE_WORD_ICON)
        if os.path.exists(mistake_icon_path):
            icon = QIcon(mistake_icon_path)
            self.problem_btn.setIcon(icon)
            self.problem_btn.setIconSize(QSize(28, 28))
            self.problem_btn.setToolTip("Проблемные слова")
        else:
            self.problem_btn.setText("Проблемные слова")
        self.problem_btn.clicked.connect(self.show_problem_words)
        self.problem_btn.setFixedSize(45, 35)
        actions_layout.addWidget(self.problem_btn)
        
        # Кнопка "управление словами" с иконкой
        self.words_btn = QPushButton()
        manager_icon_path = os.path.join(self.base_dir, Constants.MANAGER_WORD_ICON)
        if os.path.exists(manager_icon_path):
            icon = QIcon(manager_icon_path)
            self.words_btn.setIcon(icon)
            self.words_btn.setIconSize(QSize(28, 28))
            self.words_btn.setToolTip("Управление словами")
        else:
            self.words_btn.setText("Управление словами")
        self.words_btn.clicked.connect(self.open_word_manager)
        self.words_btn.setFixedSize(45, 35)
        actions_layout.addWidget(self.words_btn)
        
        # Кнопка "настройки" с иконкой
        self.settings_btn = QPushButton()
        settings_icon_path = os.path.join(self.base_dir, Constants.SETTINGS_ICON)
        if os.path.exists(settings_icon_path):
            icon = QIcon(settings_icon_path)
            self.settings_btn.setIcon(icon)
            self.settings_btn.setIconSize(QSize(28, 28))
            self.settings_btn.setToolTip("Настройки")
        else:
            self.settings_btn.setText("Настройки")
        self.settings_btn.clicked.connect(self.open_settings)
        self.settings_btn.setFixedSize(45, 35)
        actions_layout.addWidget(self.settings_btn)
        
        # Кнопка управления музыкой
        self.music_btn = QPushButton()
        music_icon_path = os.path.join(self.base_dir, Constants.MUSIC_ICON)
        if os.path.exists(music_icon_path):
            icon = QIcon(music_icon_path)
            self.music_btn.setIcon(icon)
            self.music_btn.setIconSize(QSize(28, 28))
            self.music_btn.setToolTip("Включить/выключить музыку")
        else:
            self.music_btn.setText("🎵")
            self.music_btn.setToolTip("Включить/выключить музыку")

        self.music_btn.clicked.connect(self.toggle_music)
        self.music_btn.setFixedSize(45, 35)
        actions_layout.addWidget(self.music_btn)
        
        top_layout.addLayout(actions_layout)
        
        layout.addLayout(top_layout)
        
    def show_problem_words(self):
        """Показ проблемных слов с безопасным управлением ресурсами"""
        self.block_auto_load = True
        
        # СОХРАНЯЕМ ТЕКУЩУЮ КАТЕГОРИЮ ПЕРЕД ОТКЛЮЧЕНИЕМ СИГНАЛОВ
        current_category = self.category_combo.currentText()
        
        # БЕЗОПАСНО ОТКЛЮЧАЕМ обработчик изменения категории ↓
        self._safe_disconnect_category_signal()
        
        dialog = None
        try:
            dialog = ProblemWordsDialog(self, self.word_repository)
            result = dialog.exec()
            
            # ОБНОВЛЯЕМ КОМБОБОКС КАТЕГОРИЙ С СОХРАНЕНИЕМ "ВСЕ"
            self._refresh_category_combo()
            
            # БЕЗОПАСНО ВОССТАНАВЛИВАЕМ обработчик изменения категории ↓
            self._safe_connect_category_signal()
            
            # ПЕРЕЗАГРУЖАЕМ текущее слово чтобы обновить ВСЕ счетчики
            self.load_next_word()
            
            # СОХРАНЯЕМ ДАННЫЕ В ФАЙЛ
            self.word_repository.save_data()
            
            return result
        finally:
            self.block_auto_load = False
            if dialog:
                dialog.deleteLater()
        
    def toggle_music(self):
        """Включает/выключает фоновую музыку"""
        self.music_enabled = not self.music_enabled
        self.music_service.set_music_enabled(self.music_enabled)
        
        # Обновляем состояние в настройках
        self.word_repository.app_data.settings.music_enabled = self.music_enabled
        self.word_repository.save_data()
        
        # Обновляем внешний вид кнопки
        self._update_music_button_state()

    def _update_music_button_state(self):
        """Обновляет внешний вид кнопки музыки в зависимости от состояния"""
        if not self.music_btn:
            return
            
        if self.music_enabled:
            # Музыка включена - показываем иконку музыки
            music_icon_path = os.path.join(self.base_dir, Constants.MUSIC_ICON)
            if os.path.exists(music_icon_path):
                icon = QIcon(music_icon_path)
                self.music_btn.setIcon(icon)
                self.music_btn.setToolTip("Выключить музыку")
            else:
                self.music_btn.setText("🔊")
                self.music_btn.setToolTip("Выключить музыку")
            # Убираем цветной фон
            self.music_btn.setStyleSheet("")
        else:
            # Музыка выключена - показываем иконку выключенной музыки
            music_off_icon_path = os.path.join(self.base_dir, "icons/music_off_icon.png")
            if os.path.exists(music_off_icon_path):
                icon = QIcon(music_off_icon_path)
                self.music_btn.setIcon(icon)
                self.music_btn.setToolTip("Включить музыку")
            else:
                # Если нет специальной иконки, используем текстовый символ
                self.music_btn.setText("🔇")
                self.music_btn.setToolTip("Включить музыку")
            # Убираем цветной фон
            self.music_btn.setStyleSheet("")
    
    def _create_category_area(self, layout):
        """Создание области категории по центру"""
        category_layout = QHBoxLayout()
        
        # Добавляем растяжку слева
        category_layout.addStretch()
        
        # Категория по центру
        category_layout.addWidget(QLabel("Категория:"))
        self.category_combo = QComboBox()
        
        # ДОБАВЛЯЕМ ПУНКТ "ВСЕ" ПЕРВЫМ В СПИСКЕ ↓
        self.category_combo.addItem("Все")
        self.category_combo.addItems(self.word_repository.app_data.categories)
        
        # Устанавливаем ширину комбобокса
        self.category_combo.setMinimumWidth(120)  # или нужная вам ширина
        self.category_combo.setMaximumWidth(300)
        
        current_category = self.word_repository.app_data.training_state.current_category
        
        # УСТАНАВЛИВАЕМ "ВСЕ" ПО УМОЛЧАНИЮ ЕСЛИ ТЕКУЩАЯ КАТЕГОРИЯ ПУСТАЯ ИЛИ НЕ СУЩЕСТВУЕТ ↓
        if not current_category or current_category not in self.word_repository.app_data.categories:
            self.category_combo.setCurrentText("Все")
            # Обновляем текущую категорию в состоянии тренировки
            self.word_repository.app_data.training_state.current_category = "Все"
        else:
            self.category_combo.setCurrentText(current_category)
        
        # ВАЖНО: Подключаем сигнал ПОСЛЕ установки текущего значения
        self._safe_connect_category_signal()
        category_layout.addWidget(self.category_combo)
        
        # Добавляем растяжку справа
        category_layout.addStretch()
        
        layout.addLayout(category_layout)
    
    def _create_media_area(self, layout):
        """Создание области для отображения медиа"""
        media_group = QGroupBox("Задание")
        media_layout = QVBoxLayout(media_group)
        
        # Область для изображения (фиксированная высота)
        self.image_label = QLabel("Выберите категорию для начала")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(300)
        self.image_label.setMaximumHeight(300)
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: white;")
        media_layout.addWidget(self.image_label)
        
        # Кнопка аудио с иконкой
        self.audio_btn = QPushButton()
        listen_icon_path = os.path.join(self.base_dir, Constants.LISTEN_ICON)
        if os.path.exists(listen_icon_path):
            icon = QIcon(listen_icon_path)
            self.audio_btn.setIcon(icon)
            self.audio_btn.setIconSize(QSize(32, 32))  # Размер иконки
            self.audio_btn.setToolTip("Прослушать слово")
        else:
            # Фолбэк на текст если иконка не найдена
            self.audio_btn.setText("🔊")
        
        self.audio_btn.clicked.connect(self.play_audio)
        self.audio_btn.setEnabled(False)
        
        # Устанавливаем фиксированный размер для квадратной кнопки
        self.audio_btn.setFixedSize(80, 40)
        self.audio_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #8F8F8F;
                border-radius: 6px;
                background-color: #F0F0F0;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #707070;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
            QPushButton:disabled {
                background-color: #F8F8F8;
                border: 1px solid #CCCCCC;
            }
        """)
        
        # Центрируем кнопку
        audio_btn_layout = QHBoxLayout()
        audio_btn_layout.addStretch()
        audio_btn_layout.addWidget(self.audio_btn)
        audio_btn_layout.addStretch()
        
        media_layout.addLayout(audio_btn_layout)
        
        layout.addWidget(media_group)
    
    def _create_result_area(self, layout):
        """Создание фиксированной области для индикаторов результата"""
        result_group = QGroupBox("Результат")
        result_layout = QVBoxLayout(result_group)
        
        # ФИКСИРОВАННАЯ ВЫСОТА ДЛЯ ВСЕЙ ГРУППЫ
        result_group.setFixedHeight(120)
        
        # Область для иконки результата (фиксированная высота)
        self.result_icon_label = QLabel()
        self.result_icon_label.setAlignment(Qt.AlignCenter)
        self.result_icon_label.setFixedHeight(60)
        self.result_icon_label.setStyleSheet("border: none;")
        result_layout.addWidget(self.result_icon_label)
        
        # Метка для показа правильного ответа
        self.correct_answer_label = QLabel()
        self.correct_answer_label.setAlignment(Qt.AlignCenter)
        self.correct_answer_label.setStyleSheet("font-size: 16px; font-weight: bold;")  # Убрали color из стиля
        self.correct_answer_label.setFixedHeight(25)
        self.correct_answer_label.setTextFormat(Qt.RichText)  # Включаем поддержку HTML
        self.correct_answer_label.hide()
        result_layout.addWidget(self.correct_answer_label)
        
        # Пустой спейсер для сохранения места когда нет результата
        self.empty_space_label = QLabel()
        self.empty_space_label.setFixedHeight(35)
        result_layout.addWidget(self.empty_space_label)
        
        layout.addWidget(result_group)
    
    def _create_answer_area(self, layout):
        """Создание области для ввода ответа по центру"""
        # Основной контейнер для центрирования
        answer_container = QHBoxLayout()
        answer_container.addStretch()
        
        # Центральная область с элементами ввода
        center_answer_layout = QVBoxLayout()
        
        # Метка и поле ввода
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Введи слово:"))
        
        self.answer_entry = QLineEdit()
        self.answer_entry.setFont(QFont("Arial", 14))
        self.answer_entry.setMaximumWidth(200)  # Укороченное поле ввода
        self.answer_entry.returnPressed.connect(self.check_answer)
        input_layout.addWidget(self.answer_entry)
        
        center_answer_layout.addLayout(input_layout)
        
        # ОДНА кнопка проверки
        buttons_layout = QHBoxLayout()
        
        self.check_btn = QPushButton("Проверить")
        self.check_btn.clicked.connect(self.check_answer)
        self.check_btn.setEnabled(False)
        buttons_layout.addWidget(self.check_btn)
        
        center_answer_layout.addLayout(buttons_layout)
        
        answer_container.addLayout(center_answer_layout)
        answer_container.addStretch()
        
        layout.addLayout(answer_container)
    
    def _show_result_indicator(self, is_correct, correct_answer=""):
        """Показывает индикатор результата с иконками"""
        # Скрываем пустой спейсер
        self.empty_space_label.hide()

        if is_correct:
            # Правильный ответ - зеленая иконка
            correct_icon_path = os.path.join(self.base_dir, Constants.CORRECT_ICON)
            pixmap = create_scaled_pixmap(correct_icon_path, 50, 50)
            self.result_icon_label.setPixmap(pixmap)
            self.correct_answer_label.hide()
            
            # Автоматический переход через 2 секунды
            self.auto_next_timer.start(Constants.AUTO_NEXT_WORD_DELAY)
            
        else:
            # Неправильный ответ - красная иконка
            incorrect_icon_path = os.path.join(self.base_dir, Constants.INCORRECT_ICON)
            pixmap = create_scaled_pixmap(incorrect_icon_path, 50, 50)
            self.result_icon_label.setPixmap(pixmap)
            
            # Показываем правильный ответ только если включена настройка
            if self.show_correct_answer:
                # Создаем HTML-текст с цветовым оформлением
                if self.current_word_data and self.current_word_data.case_sensitive:
                    # Если включена чувствительность к регистру, подсвечиваем заглавные буквы
                    formatted_answer = self._format_case_sensitive_answer(correct_answer)
                else:
                    # Обычное отображение без подсветки регистра
                    formatted_answer = f'<span style="color: #404040;">Правильно:</span> <span style="color: #FF0000;">{correct_answer}</span>'
                
                self.correct_answer_label.setText(formatted_answer)
                self.correct_answer_label.show()
                # Меняем кнопку на "Следующее слово" для ручного перехода
                self.check_btn.setText("Следующее слово")
                self.check_btn.clicked.disconnect()
                self.check_btn.clicked.connect(self.load_next_word)
                
                # Делаем кнопку выделенной по умолчанию
                self.check_btn.setDefault(True)
                self.check_btn.setFocus()
            else:
                self.correct_answer_label.hide()
                # Автоматический переход через 2 секунды
                self.auto_next_timer.start(Constants.AUTO_NEXT_WORD_DELAY)
                
    def _format_case_sensitive_answer(self, correct_answer):
        """
        Форматирует правильный ответ с учетом позиций важных букв
        """
        html_parts = ['<span style="color: #404040;">Правильно:</span> ']
        
        important_positions = self.current_word_data.important_positions.strip()
        
        if not important_positions:
            # Если не указаны позиции - подсвечиваем все заглавные
            return self._highlight_all_uppercase(correct_answer)
        
        # Парсим позиции
        try:
            positions = [int(pos.strip()) - 1 for pos in important_positions.split(',') if pos.strip()]
            return self._highlight_by_positions(correct_answer, positions)
        except ValueError:
            # Если ошибка в формате - подсвечиваем все заглавные
            return self._highlight_all_uppercase(correct_answer)

    def _highlight_all_uppercase(self, correct_answer):
        """Подсвечивает все заглавные буквы"""
        html_parts = []
        for char in correct_answer:
            if char.isupper():
                html_parts.append(f'<span style="background-color: #54FF00; color: #000000;">{char}</span>')
            else:
                html_parts.append(f'<span style="color: #FF0000;">{char}</span>')
        return ''.join(html_parts)

    def _highlight_by_positions(self, correct_answer, positions):
        """Подсвечивает буквы по указанным позициям"""
        html_parts = []
        for i, char in enumerate(correct_answer):
            if i in positions:
                html_parts.append(f'<span style="background-color: #54FF00; color: #000000;">{char}</span>')
            else:
                html_parts.append(f'<span style="color: #FF0000;">{char}</span>')
        return ''.join(html_parts)
    
    def _hide_result_indicator(self):
        """Скрывает индикатор результата (оставляет область пустой)"""
        self.result_icon_label.clear()
        self.result_icon_label.setText("")
        self.result_icon_label.setStyleSheet("")
        self.correct_answer_label.hide()
        # Показываем пустой спейсер чтобы сохранить место
        self.empty_space_label.show()
        
        # Восстанавливаем кнопку "Проверить"
        self.check_btn.setText("Проверить")
        self.check_btn.clicked.disconnect()
        self.check_btn.clicked.connect(self.check_answer)
        
        # Сбрасываем выделение по умолчанию
        self.check_btn.setDefault(False)
        
        # СБРАСЫВАЕМ СТИЛЬ И ЗАГОЛОВОК ДЛЯ ПОВТОРЕНИЙ ↓
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: white;")
        self._set_group_title("Задание")
    
    def _update_words_counter(self):
        """Обновляет счетчик слов для текущей категории"""
        # Проверяем что элементы интерфейса уже созданы
        if not hasattr(self, 'words_counter_label') or not hasattr(self, 'correct_counter_label') or not hasattr(self, 'incorrect_counter_label'):
            return
        
        training_state = self.word_repository.app_data.training_state
        current_category = training_state.current_category
        
        # Определяем количество слов и статистику в зависимости от режима
        if not current_category or current_category == "Все":
            # В режиме "Все" считаем статистику по всем словам
            all_words = self.word_repository.app_data.words
            total_words = len(all_words)
            used_words_count = len(training_state.used_words)
            # Суммируем счетчики правильных/неправильных ответов по всем категориям
            correct = sum(training_state.correct_answers_count.values())
            incorrect = sum(training_state.incorrect_answers_count.values())
            # Считаем слова на повторении (всех категорий)
            repeat_words_count = len(training_state.repeat_words)
        else:
            # Для конкретной категории
            all_words_in_category = self.word_repository.get_words_by_category(current_category)
            total_words = len(all_words_in_category)
            # Считаем использованные слова этой категории по category-specific tracking
            used_words_set = training_state.used_words_by_category[current_category]
            used_words_count = len(used_words_set)
            # Получаем счетчики правильных/неправильных ответов для текущей категории
            correct = training_state.correct_answers_count.get(current_category, 0)
            incorrect = training_state.incorrect_answers_count.get(current_category, 0)
            # Считаем слова на повторении для текущей категории
            repeat_words_count = len([rw for rw in training_state.repeat_words if rw.category == current_category])
        
        # Формируем текст счетчика в зависимости от режима
        infinite_mode = self.word_repository.app_data.settings.infinite_mode
        if infinite_mode:
            # В бесконечном режиме показываем ∞
            counter_text = f"Пройдено: {used_words_count} из ∞"
        else:
            # В обычном режиме обычный счетчик
            counter_text = f"Пройдено: {used_words_count} из {total_words}"
        
        # Добавляем информацию о повторениях если есть слова на повторении
        if repeat_words_count > 0:
            counter_text += f" | Повтор: {repeat_words_count}"
        
        # Обновляем отображение счетчиков
        self.words_counter_label.setText(counter_text)
        self.correct_counter_label.setText(f'<span style="color: #303030;">Верно:</span> <span style="color: #00B524;">{correct}</span>')
        self.incorrect_counter_label.setText(f'<span style="color: #303030;">Ошибки:</span> <span style="color: #FF3B00;">{incorrect}</span>')
        
        # Сохраняем данные при каждом обновлении счетчиков для обеспечения сохранности
        self.word_repository.save_data()
    
    def on_category_changed(self, category):
        """Обработчик изменения категории"""
        if not category:  # Если категория пустая, выходим
            return
                
        training_state = self.word_repository.app_data.training_state
        
        # Сохраняем выбранную категорию, включая "Все"
        training_state.current_category = category
        
        # Сбрасываем текущее слово при смене категории
        self.current_word_data = None
        
        # Сбрасываем флаг первого запуска при смене категории
        self.is_first_load = False
        
        # Загружаем новое слово для новой категории
        self.load_next_word()
        
        # Обновляем счетчики для новой категории
        self._update_words_counter()
        
        # Сохраняем данные при необходимости
        self.word_repository.save_data()

    def reset_progress(self):
        """Сброс прогресса по словам ТОЛЬКО для текущей категории или всех"""
        self._validate_current_category()
        
        training_state = self.word_repository.app_data.training_state
        current_category = training_state.current_category
        
        # ОБРАБОТКА РЕЖИМА "ВСЕ" ↓
        if current_category == "Все":
            # Сброс прогресса по всем категориям, но СОХРАНЯЕМ статистику ошибок (problem words)
            # Проходим по всем категориям и сбрасываем прогресс для каждой, но не трогаем статистику ошибок
            categories_to_reset = self.word_repository.app_data.categories.copy()
            
            # Сбрасываем счетчики правильных/неправильных ответов, использованные слова и слова на повторении
            # для всех категорий, но сохраняем mistakes_count и wrong_answers
            training_state.correct_answers_count.clear()
            training_state.incorrect_answers_count.clear()
            training_state.used_words.clear()
            training_state.used_words_by_category.clear()  # Также очищаем category-specific used words
            training_state.repeat_words.clear()
            
            self.is_first_load = False
            self._update_words_counter()
            self.load_next_word()
            
            self.word_repository.save_data()
            show_silent_message(self, "Сброс", "Прогресс по ВСЕМ категориям сброшен!\n\nСохранены: статистика ошибок (проблемные слова)")
            
        elif current_category:
            # Сброс только для указанной категории
            # Получаем все слова текущей категории по uid
            all_words_in_category = self.word_repository.get_words_by_category(current_category)
            category_uids = {word_data.uid for word_data in all_words_in_category}
            
            # ВАЖНО: НЕ сбрасываем статистику ошибок (mistakes_count и wrong_answers) - это проблемные слова!
            # Они должны сохраняться даже после сброса прогресса
            
            # Сбрасываем только счетчики правильных/неправильных ответов для текущей категории
            if current_category in training_state.correct_answers_count:
                del training_state.correct_answers_count[current_category]
            if current_category in training_state.incorrect_answers_count:
                del training_state.incorrect_answers_count[current_category]
            
            # УДАЛЯЕМ СЛОВА НА ПОВТОРЕНИИ ДЛЯ ТЕКУЩЕЙ КАТЕГОРИИ
            training_state.repeat_words = [rw for rw in training_state.repeat_words if rw.category != current_category]
            
            # Удаляем слова только из списка использованных слов для текущей категории
            training_state.used_words_by_category[current_category] -= category_uids
            
            # Сбрасываем флаг первого запуска
            self.is_first_load = False
            
            # Обновляем счетчики
            self._update_words_counter()
            
            # Принудительно загружаем новое слово
            self.load_next_word()
            
            self.word_repository.save_data()
            show_silent_message(self, "Сброс", f"Прогресс по категории '{current_category}' сброшен!\n\nСброшено: использованные слова, счетчики правильных/неправильных ответов, слова на повторении\n\nСохранены: статистика ошибок (проблемные слова)")
        else:
            # Сбрасываем интерфейс если нет категории
            self._hide_result_indicator()
            self.answer_entry.clear()
            self.answer_entry.setEnabled(True)
            self.check_btn.setEnabled(False)
            self.image_label.setText("Выберите категорию для начала")
            self.audio_btn.setEnabled(False)

    def reset_score(self):
        """Обнуление общего счёта (для совместимости)"""
        # Вызываем сброс для текущего типа награды
        training_state = self.word_repository.app_data.training_state
        training_state.reset_score(self.reward_type)
        self.update_score()
        self._update_words_counter()
        self.word_repository.save_data()
        
        # Показываем сообщение о сбросе текущего счёта
        reward_unit = "балл" if self.reward_type == "points" else "руб."
        show_silent_message(self, "Сброс счёта", f"Счёт в {reward_unit} обнулён!")
        
    def _validate_current_category(self):
        """Проверяет и исправляет текущую категорию если она не существует"""
        # ИСПРАВЛЕНИЕ: Проверяем что category_combo уже создан
        if not hasattr(self, 'category_combo'):
            return
                
        training_state = self.word_repository.app_data.training_state
        current_category = training_state.current_category
        
        # ИСПРАВЛЯЕМ: Сохраняем пункт "Все" всегда
        # Если текущая категория не существует и не "Все", сбрасываем её на "Все"
        if (current_category and 
            current_category != "Все" and 
            current_category not in self.word_repository.app_data.categories):
            training_state.current_category = "Все"
        
        # БЕЗОПАСНОЕ ОБНОВЛЕНИЕ КОМБОБОКСА ↓
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("Все")  # Всегда добавляем "Все" первым
        
        # Добавляем остальные категории только если они есть
        if self.word_repository.app_data.categories:
            self.category_combo.addItems(self.word_repository.app_data.categories)
        
        # Восстанавливаем текущую категорию или "Все" если она пропала
        if current_category and (current_category == "Все" or current_category in self.word_repository.app_data.categories):
            self.category_combo.setCurrentText(current_category)
        else:
            self.category_combo.setCurrentText("Все")
            training_state.current_category = "Все"
        
        self.category_combo.blockSignals(False)
    
    def load_next_word(self):
        """
        Загрузка следующего слова для обучения.
        
        Метод выбирает следующее слово в зависимости от текущей категории и настроек.
        Сначала проверяется наличие слов для повторения, затем обычные слова.
        """
        # Останавливаем таймеры если они активны
        if self.auto_next_timer.isActive():
            self.auto_next_timer.stop()
        if self.auto_play_timer.isActive():
            self.auto_play_timer.stop()
            
        # Проверяем блокировку - если True, выходим из метода
        if self.block_auto_load:
            return
            
        # Проверяем что UI полностью инициализирован
        if not hasattr(self, 'answer_entry'):
            return
            
        # Сбрасываем состояние проверки ответа
        self.answer_checked = False
        self.answer_entry.clear()
        self.answer_entry.setEnabled(True)
        
        # Восстанавливаем фокус на поле ввода
        self.answer_entry.setFocus()
        
        # Скрываем индикатор результата при загрузке нового слова (оставляем область пустой)
        self._hide_result_indicator()
        
        training_state = self.word_repository.app_data.training_state
        current_category = training_state.current_category
        
        # Проверяем категорию для загрузки слова
        if not current_category or current_category == "Все":
            # В режиме "Все" просто продолжаем без дополнительных проверок
            pass
        else:
            # Для конкретной категории проверяем что она существует
            if current_category not in self.word_repository.app_data.categories:
                self.image_label.setText("Категория не найдена")
                self.audio_btn.setEnabled(False)
                self.check_btn.setEnabled(False)
                self._update_words_counter()
                return
        
        # Проверяем наличие слов для повторения
        if self.repeat_mistakes:
            # НЕ УМЕНЬШАЕМ счетчики для всех слов на повторении при загрузке слова
            # Счетчики уменьшаются только когда пользователь отвечает на слово
            
            # Проверяем есть ли слова готовые для повторения
            ready_words = training_state.get_words_ready_for_repetition()
            if ready_words:
                # Выбираем случайное слово из готовых к повторению
                repeat_word_data = random.choice(ready_words)
                
                # Находим полные данные слова по uid
                word_data = self.word_repository.get_word_by_uid(repeat_word_data.word_uid)
                if word_data and word_data.categories:
                    # Проверяем соответствие категории (в "Все" режиме подходит любая категория)
                    if current_category == "Все" or current_category in word_data.categories:
                        self.current_word_data = word_data
                        
                        # Загружаем медиа
                        self._load_word_media()
                        
                        # Запускаем таймер автоматического воспроизведения звука
                        if (self.auto_play_enabled and
                            self.current_audio_file and
                            not self.is_first_load):
                            self.auto_play_timer.start(self.auto_play_delay)
                        
                        # Обновляем UI
                        self.audio_btn.setEnabled(bool(self.current_word_data.audio))
                        self.check_btn.setEnabled(True)
                        self.answer_entry.setFocus()
                        
                        # Обновляем счетчик слов с пометкой о повторении
                        self._update_words_counter()
                        
                        # Показываем пометку что это повторение
                        self._show_repetition_indicator(repeat_word_data.current_attempt)
                        
                        self.word_repository.save_data()
                        return
        
        # Определяем доступные слова в зависимости от режима
        available_words = []
        if current_category == "Все":
            # В режиме "Все" используем слова из всех категорий
            all_words = self.word_repository.app_data.words
            
            if self.infinite_mode:
                # В бесконечном режиме используем все слова
                if all_words:
                    # Исключаем только что использованное слово чтобы не повторяться сразу
                    if self.current_word_data:
                        available_words = [word for word in all_words if word.uid != self.current_word_data.uid]
                    else:
                        available_words = all_words
                    
                    # Если после исключения текущего слова не осталось вариантов, используем все слова
                    if not available_words:
                        available_words = all_words
            else:
                # В обычном режиме - только неиспользованные слова
                available_words = [word for word in all_words if word.uid not in training_state.used_words]
        else:
            # Для конкретной категории
            if self.infinite_mode:
                # В бесконечном режиме используем все слова категории
                all_words = self.word_repository.get_words_by_category(current_category)
                if all_words:
                    # Исключаем только что использованное слово чтобы не повторяться сразу
                    if self.current_word_data:
                        available_words = [word for word in all_words if word.uid != self.current_word_data.uid]
                    else:
                        available_words = all_words
                    
                    # Если после исключения текущего слова не осталось вариантов, используем все слова
                    if not available_words:
                        available_words = all_words
            else:
                # Обычный режим - только неиспользованные слова
                available_words = self.word_repository.get_available_words(current_category)
        
        if not available_words:
            # Обновляем сообщение в зависимости от режима
            if current_category == "Все":
                self.image_label.setText("Все слова пройдены!\nСбросьте прогресс для повторения")
            else:
                self.image_label.setText(f"Все слова в категории '{current_category}' пройдены!\nСбросьте прогресс для повторения")
                
            self.audio_btn.setEnabled(False)
            self.check_btn.setEnabled(False)
            self._update_words_counter()
            # Сбрасываем флаг первого запуска
            self.is_first_load = False
            return
        
        # Выбираем случайное слово
        self.current_word_data = random.choice(available_words)
        
        # Загружаем медиа
        self._load_word_media()
        
        # Запускаем таймер автоматического воспроизведения звука
        # НЕ проигрываем звук при самом первом запуске программы
        if (self.auto_play_enabled and
            self.current_audio_file and
            not self.is_first_load):
            self.auto_play_timer.start(self.auto_play_delay)
        
        # Сбрасываем флаг первого запуска после первой загрузки слова
        self.is_first_load = False
        
        # Обновляем UI
        self.audio_btn.setEnabled(bool(self.current_word_data.audio))
        self.check_btn.setEnabled(True)
        self.answer_entry.setFocus()
        
        # Обновляем счетчик слов
        self._update_words_counter()
        
        self.word_repository.save_data()
        
    def _show_repetition_indicator(self, attempt_number: int):
        """Показывает индикатор что это повторение слова"""
        # Меняем стиль рамки в зависимости от номера попытки
        if attempt_number == 1:
            self.image_label.setStyleSheet("border: 3px solid #FF6B00; background-color: #FFF3E0;")
            # Можно также добавить текст в заголовок
            self._set_group_title("Задание (Повторение 1)")
        elif attempt_number == 2:
            self.image_label.setStyleSheet("border: 3px solid #2196F3; background-color: #E3F2FD;")
            self._set_group_title("Задание (Повторение 2)")
        else:
            self.image_label.setStyleSheet("border: 3px solid #4CAF50; background-color: #E8F5E8;")
            self._set_group_title("Задание (Повторение 3)")

    def _set_group_title(self, title: str):
        """Устанавливает заголовок для группы задания"""
        # Находим QGroupBox с заданием (предполагаем что он первый в layout)
        central_widget = self.centralWidget()
        if central_widget:
            layout = central_widget.layout()
            if layout and layout.count() > 2:  # Пропускаем top_panel и category_area
                media_group = layout.itemAt(2).widget()
                if isinstance(media_group, QGroupBox):
                    media_group.setTitle(title)
    
    def _load_word_media(self):
        """Загружает медиафайлы для текущего слова"""
        if not self.current_word_data:
            return
        
        try:
            # Загружаем изображение
            available_images = self.media_manager.get_available_images(self.current_word_data.images)
            
            if available_images:
                random_image = random.choice(available_images)
                image_path = os.path.join(self.media_manager.images_folder, random_image)
                
                pixmap = create_scaled_pixmap(image_path, Constants.IMAGE_WIDTH, Constants.IMAGE_HEIGHT)
                
                if pixmap:
                    self.image_label.setPixmap(pixmap)
                    self.image_label.setText("")
                else:
                    self._show_default_image()
            else:
                self._show_default_image()
        except Exception as e:
            logging.error(f"Ошибка при загрузке изображения: {e}")
            self._show_default_image()
        
        # Сохраняем информацию об аудио
        self.current_audio_file = self.current_word_data.audio
    
    def _show_default_image(self):
        """Показывает изображение-заглушку"""
        try:
            # Сначала пробуем загрузить изображение из медиа-менеджера (data directory)
            if os.path.exists(self.media_manager.default_image):
                pixmap = create_scaled_pixmap(
                    self.media_manager.default_image,
                    Constants.IMAGE_WIDTH,
                    Constants.IMAGE_HEIGHT
                )
                if pixmap:
                    self.image_label.setPixmap(pixmap)
                    self.image_label.setText("")
                    return
            else:
                # Если в data directory нет, пробуем загрузить из ui/icons (base directory)
                default_image_path = os.path.join(self.base_dir, Constants.DEFAULT_IMAGE)
                if os.path.exists(default_image_path):
                    pixmap = create_scaled_pixmap(
                        default_image_path,
                        Constants.IMAGE_WIDTH,
                        Constants.IMAGE_HEIGHT
                    )
                    if pixmap:
                        self.image_label.setPixmap(pixmap)
                        self.image_label.setText("")
                        return
            
            # Если ни один из путей не сработал, показываем текст
            self.image_label.setText("Изображение не доступно")
        except Exception as e:
            logging.error(f"Ошибка при отображении заглушки изображения: {e}")
            self.image_label.setText("Ошибка загрузки изображения")
    
    def play_audio(self):
        """Воспроизведение аудио слова"""
        if self.current_audio_file:
            self.audio_service.play_word_audio(self.current_audio_file, self.media_manager.audio_folder)
        else:
            QMessageBox.warning(self, "Предупреждение", "Аудио не доступно для этого слова")
        
        # Восстанавливаем фокус на поле ввода после нажатия кнопки
        self.answer_entry.setFocus()
    
    def check_answer(self):
        """Проверка ответа пользователя"""
        try:
            if not self.current_word_data:
                show_silent_message(self, "Ошибка", "Нет текущего слова!")
                return
            
            if self.answer_checked:
                show_silent_message(self, "Информация", "Ответ уже проверен!")
                return
            
            user_answer = self.answer_entry.text().strip()
            if not user_answer:
                show_silent_message(self, "Ошибка", "Введи слово!")
                return
            
            training_state = self.word_repository.app_data.training_state
            current_category = training_state.current_category
            correct_answer = self.current_word_data.word
            
            # ОПРЕДЕЛЯЕМ ЯВЛЯЕТСЯ ЛИ ТЕКУЩЕЕ СЛОВО ПОВТОРЕНИЕМ ↓
            is_repetition = False
            current_repeat_word = None
            if self.repeat_mistakes and current_category:
                for repeat_word in training_state.repeat_words:
                    if (repeat_word.word_uid == self.current_word_data.uid and
                        repeat_word.category == current_category and
                        repeat_word.next_show_after <= 0):
                        is_repetition = True
                        current_repeat_word = repeat_word
                        break
            # ДОБАВЛЯЕМ ЛОГИКУ: если слово не найдено в текущей категории, ищем его в других категориях
            # Это решает проблему, когда слово было добавлено в повтор из категории "Все"
            if not is_repetition and self.repeat_mistakes:
                for repeat_word in training_state.repeat_words:
                    if (repeat_word.word_uid == self.current_word_data.uid and
                        repeat_word.next_show_after <= 0):
                        is_repetition = True
                        current_repeat_word = repeat_word
                        break  # Используем первое найденное совпадение
            
            # ОБНОВЛЕННАЯ ЛОГИКА ПРОВЕРКИ С УЧЕТОМ ПОЗИЦИЙ ВАЖНЫХ БУКВ
            if self.current_word_data.case_sensitive:
                important_positions = self.current_word_data.important_positions.strip()
                
                if not important_positions:
                    # Если позиции не указаны - проверяем все буквы на точное совпадение
                    is_correct = user_answer == correct_answer
                else:
                    # Если указаны позиции - проверяем только важные позиции
                    is_correct = self._check_important_positions(user_answer, correct_answer, important_positions)
            else:
                # Игнорируем регистр для этого слова (поведение по умолчанию)
                is_correct = user_answer.lower() == correct_answer.lower()
            
            # ОБНОВЛЯЕМ ЛОГИКУ ДОБАВЛЕНИЯ В USED_WORDS ↓
            if not is_repetition:
                # Добавляем слово в used_words только если это не повторение
                # Добавляем в глобальный список для совместимости
                training_state.used_words.add(self.current_word_data.uid)
                # Также добавляем в список использованных слов для текущей категории
                if current_category:
                    training_state.used_words_by_category[current_category].add(self.current_word_data.uid)
            
            if is_correct:
                # Правильный ответ - ОБНОВЛЯЕМ ТОЛЬКО ТЕКУЩИЙ СЧЁТ
                # Обновляем счёт в зависимости от текущего типа награды
                current_score = training_state.get_current_score(self.reward_type)
                if self.reward_type == "points":
                    new_score = current_score + self.word_repository.app_data.settings.points_cost_per_word
                    training_state.set_current_score(new_score, self.reward_type)
                else:
                    new_score = current_score + self.word_repository.app_data.settings.rubles_cost_per_word
                    training_state.set_current_score(new_score, self.reward_type)
                
                if current_category:
                    training_state.increment_correct(current_category)
                    
                # ОБРАБАТЫВАЕМ ПОВТОРЕНИЕ ЕСЛИ ЭТО ПОВТОРЕНИЕ ↓
                if is_repetition and current_repeat_word:
                    # Используем оригинальную категорию повтора, а не текущую
                    training_state.update_repeat_word_after_attempt(
                        self.current_word_data.uid,
                        current_repeat_word.category,
                        self.repeat_mistakes_range,
                        True  # is_correct
                    )
                    
                self.audio_service.play_correct_sound()
                
                # Показываем индикатор правильного ответа
                self._show_result_indicator(True)
                
                self._handle_correct_answer()
            else:
                # Неправильный ответ - ОБНОВЛЯЕМ ТОЛЬКО ТЕКУЩИЙ СЧЁТ
                current_score = training_state.get_current_score(self.reward_type)
                if self.reward_type == "points":
                    new_score = current_score - self.word_repository.app_data.settings.points_penalty_per_word
                    training_state.set_current_score(new_score, self.reward_type)
                else:
                    new_score = current_score - self.word_repository.app_data.settings.rubles_penalty_per_word
                    training_state.set_current_score(new_score, self.reward_type)
                
                if current_category:
                    training_state.increment_incorrect(current_category)
                    training_state.increment_mistake(current_category, self.current_word_data.word)
                    training_state.add_wrong_answer(current_category, self.current_word_data.word, user_answer)
                    
                # ДОБАВЛЯЕМ/ОБНОВЛЯЕМ СЛОВО НА ПОВТОРЕНИЕ ↓
                if self.repeat_mistakes and current_category:
                    if is_repetition and current_repeat_word:
                        # Если это уже повторение - обновляем его
                        # Используем оригинальную категорию повтора, а не текущую
                        training_state.update_repeat_word_after_attempt(
                            self.current_word_data.uid,
                            current_repeat_word.category,
                            self.repeat_mistakes_range,
                            False  # is_correct
                        )
                    else:
                        # Если это новое слово с ошибкой - добавляем его
                        training_state.add_word_for_repetition(
                            self.current_word_data.uid,
                            current_category,
                            self.repeat_mistakes_range
                        )
                    
                self.audio_service.play_incorrect_sound()
                
                # Показываем индикатор неправильного ответа с правильным ответом
                self._show_result_indicator(False, correct_answer)
                
                self._handle_incorrect_answer()
            
            # УМЕНЬШАЕМ счетчики для всех слов на повторении ТОЛЬКО после ответа пользователя
            training_state.decrement_repeat_counters()
            self.update_score()
            self._update_words_counter() # Обновляем счетчик слов
            self.word_repository.save_data()
            
        except Exception as e:
            logging.error(f"Ошибка при проверке ответа: {e}")
            show_silent_message(self, "Ошибка", f"Произошла ошибка при проверке ответа: {str(e)}")
        
    def _check_important_positions(self, user_answer, correct_answer, important_positions):
        """
        Проверяет только важные позиции в ответе
        """
        try:
            # Парсим позиции (преобразуем в индексы с 0)
            positions = [int(pos.strip()) - 1 for pos in important_positions.split(',') if pos.strip()]
            
            # Проверяем длину ответа
            if len(user_answer) != len(correct_answer):
                return False
            
            # Проверяем каждую важную позицию
            for pos in positions:
                # Проверяем границы для обеих строк
                if pos < 0 or pos >= len(correct_answer) or pos >= len(user_answer):
                    # Если позиция выходит за границы, считаем это ошибкой
                    return False
                
                # Проверяем, что в важной позиции символы совпадают (с учетом регистра)
                if user_answer[pos] != correct_answer[pos]:
                    return False
            
            # Все важные позиции совпали
            return True
            
        except ValueError:
            # Если ошибка в формате позиций - проверяем все буквы
            return user_answer == correct_answer
    
    def _handle_correct_answer(self):
        """Обработка правильного ответа"""
        self.check_btn.setEnabled(False)
        self.answer_entry.setEnabled(False)
        self.answer_checked = True
        
        # Сохраняем данные при обработке ответа для обеспечения сохранности
        self.word_repository.save_data()
    
    def _handle_incorrect_answer(self):
        """Обработка неправильного ответа"""
        self.answer_entry.setEnabled(False)
        if self.show_correct_answer:
            # Для ручного перехода кнопка остается активной (но теперь это "Следующее слово")
            pass
        else:
            # Для автоматического перехода кнопка отключается
            self.check_btn.setEnabled(False)
        self.answer_checked = True
        
        # Сохраняем данные при обработке ответа для обеспечения сохранности
        self.word_repository.save_data()
    
    def update_score(self):
        """Обновление отображения общего счёта"""
        training_state = self.word_repository.app_data.training_state
        
        # Обновляем отображение счёта в зависимости от текущего типа награды
        current_score = training_state.get_current_score(self.reward_type)
        if self.reward_type == "points":
            score_text = f"{int(current_score)} балл"
        else:
            score_text = f"{current_score:.2f} руб."
        self.score_label.setText(score_text)
        
        # Сохраняем данные при обновлении счёта для обеспечения сохранности
        self.word_repository.save_data()
    
    def open_settings(self):
        """Открытие настроек с безопасным управлением ресурсами"""
        # ПРОВЕРЯЕМ НУЖЕН ЛИ ПАРОЛЬ ДЛЯ ВХОДА В НАСТРОЙКИ ↓
        if self.require_password_for_settings:
            # Если требуется пароль - показываем диалог ввода пароля
            password_dialog = QDialog(self)
            password_dialog.setWindowTitle("Введите пароль")
            password_dialog.setModal(True)
            password_dialog.resize(260, 120)
            
            # Устанавливаем иконку окна
            settings_icon_path = os.path.join(self.base_dir, Constants.SETTINGS_ICON)
            if os.path.exists(settings_icon_path):
                password_dialog.setWindowIcon(QIcon(settings_icon_path))
            
            # Создаем layout
            layout = QVBoxLayout(password_dialog)
            
            # Создаем горизонтальный layout для поля ввода и кнопки
            input_layout = QHBoxLayout()
            
            # Поле ввода пароля
            input_layout.addWidget(QLabel("Введите пароль:"))
            password_edit = QLineEdit()
            password_edit.setEchoMode(QLineEdit.Password)
            password_edit.returnPressed.connect(password_dialog.accept)
            input_layout.addWidget(password_edit)
            
            # Кнопка смены пароля
            change_password_btn = QPushButton()
            change_password_icon_path = os.path.join(self.base_dir, Constants.CHANGE_PASSWORD_ICON)
            if os.path.exists(change_password_icon_path):
                icon = QIcon(change_password_icon_path)
                change_password_btn.setIcon(icon)
                change_password_btn.setIconSize(QSize(20, 20))
                change_password_btn.setToolTip("Сменить пароль")
            else:
                change_password_btn.setText("Сменить")
            
            change_password_btn.setFixedSize(30, 30)
            change_password_btn.clicked.connect(lambda: self._change_password(password_dialog))
            input_layout.addWidget(change_password_btn)
            
            layout.addLayout(input_layout)
            
            # Кнопки OK/Отмена
            button_layout = QHBoxLayout()
            
            ok_btn = QPushButton("ОК")
            ok_btn.clicked.connect(password_dialog.accept)
            button_layout.addWidget(ok_btn)
            
            cancel_btn = QPushButton("Отмена")
            cancel_btn.clicked.connect(password_dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # Показываем диалог и получаем результат
            result = password_dialog.exec()
            password = password_edit.text()
            
            # Используем пароль из настроек вместо константы
            current_password = self.word_repository.app_data.settings.settings_password
            
            if result and password == current_password:
                # Пароль верный - открываем настройки
                self._open_settings_dialog()
            elif result:
                QMessageBox.critical(self, "Ошибка", "Неверный пароль!")
            
            # Освобождаем ресурсы
            password_dialog.deleteLater()
        else:
            # Если пароль не требуется - открываем настройки сразу
            self._open_settings_dialog()
            
    def _open_settings_dialog(self):
        """Открывает диалог настроек (внутренний метод)"""
        dialog = None
        try:
            settings = self.word_repository.app_data.settings
            dialog = SettingsDialog(self,
                                  settings.cost_per_word,
                                  settings.penalty_per_word,
                                  self.show_correct_answer,
                                  self.auto_play_enabled,
                                  self.auto_play_delay,
                                  self.require_password_for_settings,
                                  self.repeat_mistakes,
                                  self.repeat_mistakes_range,
                                  self.infinite_mode,
                                  settings.reward_type,
                                  settings.points_cost_per_word,
                                  settings.points_penalty_per_word,
                                  settings.rubles_cost_per_word,
                                  settings.rubles_penalty_per_word)
            if dialog.exec():
                # Сохраняем настройки в репозиторий
                self.cost_per_word = dialog.get_cost_per_word()
                self.penalty_per_word = dialog.get_penalty_per_word()
                self.show_correct_answer = dialog.get_show_correct_answer()
                # Автовоспроизведение всегда включено с задержкой 500 мс
                self.auto_play_enabled = True
                self.auto_play_delay = 500
                
                # СОХРАНЯЕМ НОВЫЕ НАСТРОЙКИ
                self.require_password_for_settings = dialog.get_require_password_for_settings()
                self.repeat_mistakes = dialog.get_repeat_mistakes()
                self.repeat_mistakes_range = dialog.get_repeat_mistakes_range()
                self.infinite_mode = dialog.get_infinite_mode()
                reward_type = dialog.get_reward_type()
                
                # Обновляем настройки в репозитории
                # Синхронизируем старые и новые поля для обеспечения совместимости
                # Получаем новые значения из диалога
                points_cost = dialog.points_cost_per_word
                points_penalty = dialog.points_penalty_per_word
                rubles_cost = dialog.rubles_cost_per_word
                rubles_penalty = dialog.rubles_penalty_per_word
                
                # УБРАНО: Обновление старых полей cost_per_word и penalty_per_word при сохранении
                # Эти поля должны использоваться ТОЛЬКО для миграции старых данных при загрузке
                # При сохранении должны обновляться только points_cost_per_word/points_penalty_per_word и rubles_cost_per_word/rubles_penalty_per_word
                
                # Обновляем новые отдельные настройки (важно: сохраняем оба набора значений независимо)
                self.word_repository.app_data.settings.points_cost_per_word = points_cost
                self.word_repository.app_data.settings.points_penalty_per_word = points_penalty
                self.word_repository.app_data.settings.rubles_cost_per_word = rubles_cost
                self.word_repository.app_data.settings.rubles_penalty_per_word = rubles_penalty
                
                self.word_repository.app_data.settings.show_correct_answer = self.show_correct_answer
                self.word_repository.app_data.settings.auto_play_enabled = True
                self.word_repository.app_data.settings.auto_play_delay = 500
                
                # ОБНОВЛЯЕМ НОВЫЕ НАСТРОЙКИ В РЕПОЗИТОРИИ
                self.word_repository.app_data.settings.require_password_for_settings = self.require_password_for_settings
                self.word_repository.app_data.settings.repeat_mistakes = self.repeat_mistakes
                self.word_repository.app_data.settings.repeat_mistakes_range = self.repeat_mistakes_range
                self.word_repository.app_data.settings.infinite_mode = self.infinite_mode
                self.word_repository.app_data.settings.reward_type = reward_type
                
                # ОБНОВЛЯЕМ ТИП НАГРАДЫ В ОСНОВНОМ ОКНЕ
                self.reward_type = reward_type
                
                # ОБНОВЛЯЕМ ОСНОВНЫЕ ЗНАЧЕНИЯ НАГРАДЫ И ШТРАФА В ЗАВИСИМОСТИ ОТ ТИПА НАГРАДЫ
                if reward_type == "points":
                    self.cost_per_word = points_cost
                    self.penalty_per_word = points_penalty
                else:  # rubles
                    self.cost_per_word = rubles_cost
                    self.penalty_per_word = rubles_penalty
                
                # ОБНОВЛЯЕМ СЧЕТЧИК СЛОВ ДЛЯ ОТОБРАЖЕНИЯ ∞
                self._update_words_counter()
                
                # ОБНОВЛЯЕМ КОМБОБОКС КАТЕГОРИЙ ЕСЛИ НУЖНО ↓
                self._validate_current_category()
                
                # ОБНОВЛЯЕМ ОТОБРАЖЕНИЕ СЧЁТА ПРИ СМЕНЕ ТИПА НАГРАДЫ
                self.update_score()
                
                # Сохраняем данные один раз в конце
                self.word_repository.save_data()
        finally:
            if dialog:
                dialog.deleteLater()
                
    def _refresh_category_combo(self):
        """Обновляет комбобокс категорий с сохранением текущего выбора и пункта 'Все'"""
        # СОХРАНЯЕМ ТЕКУЩУЮ КАТЕГОРИЮ ↓
        current_category = self.category_combo.currentText()
        
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("Все")  # Всегда добавляем "Все" первым
        
        # Добавляем остальные категории только если они есть
        if self.word_repository.app_data.categories:
            self.category_combo.addItems(self.word_repository.app_data.categories)
        
        # Восстанавливаем текущую категорию или "Все" если она пропала
        if current_category and (current_category == "Все" or current_category in self.word_repository.app_data.categories):
            self.category_combo.setCurrentText(current_category)
        else:
            self.category_combo.setCurrentText("Все")
            self.word_repository.app_data.training_state.current_category = "Все"
        
        self.category_combo.blockSignals(False)
    
    def _change_password(self, parent_dialog):
        """Смена пароля"""
        # Закрываем родительский диалог ввода пароля
        parent_dialog.close()
        
        dialog = None
        try:
            # Используем пароль из настроек вместо константы
            current_password = self.word_repository.app_data.settings.settings_password
            dialog = ChangePasswordDialog(self, current_password)
            if dialog.exec():
                new_password = dialog.get_new_password()
                if new_password:
                    # Обновляем пароль в настройках приложения
                    self.word_repository.app_data.settings.settings_password = new_password
                    self.word_repository.save_data()
                    QMessageBox.information(self, "Успех", "Пароль успешно изменен!")
        finally:
            if dialog:
                dialog.deleteLater()
    
    def open_word_manager(self):
        """Открытие менеджера слов с безопасным управлением ресурсами"""
        # Блокируем автоматическую загрузку слов
        self.block_auto_load = True
        
        # СОХРАНЯЕМ ТЕКУЩУЮ КАТЕГОРИЮ ПЕРЕД ОТКЛЮЧЕНИЕМ СИГНАЛОВ
        current_category = self.category_combo.currentText()
        
        # БЕЗОПАСНО ОТКЛЮЧАЕМ обработчик изменения категории ↓
        self._safe_disconnect_category_signal()
        
        dialog = None
        try:
            dialog = WordManagerDialog(self, self.word_repository, self.media_manager)
            result = dialog.exec()
            
            # После закрытия диалога обновляем состояние
            self._validate_current_category()
            self.load_next_word()
            
            # ОБНОВЛЯЕМ КОМБОБОКС КАТЕГОРИЙ С СОХРАНЕНИЕМ "ВСЕ"
            self._refresh_category_combo()
            
            # Обновляем счетчик слов
            self._update_words_counter()
            
            return result
        finally:
            # БЕЗОПАСНО ВОССТАНАВЛИВАЕМ обработчик изменения категории ↓
            self._safe_connect_category_signal()
            
            # Снимаем блокировку в любом случае
            self.block_auto_load = False
            # Явное освобождение ресурсов диалога
            if dialog:
                dialog.deleteLater()
    
    def add_new_word(self):
        """Открытие диалога добавления нового слова"""
        dialog = None
        try:
            dialog = WordEditorDialog(self, self.word_repository, self.media_manager)
            if dialog.exec():
                # После добавления слова обновляем комбобокс категорий
                self._validate_current_category()
                self._update_words_counter()
                # Если текущая категория не изменилась, можно перезагрузить слово
                self.load_next_word()
        finally:
            if dialog:
                dialog.deleteLater()

    def closeEvent(self, event):
        """Вызывается при закрытии окна"""
        # Останавливаем все таймеры
        if hasattr(self, 'auto_next_timer'):
            self.auto_next_timer.stop()
        if hasattr(self, 'auto_play_timer'):
            self.auto_play_timer.stop()
        # Останавливаем аудио
        if hasattr(self, 'audio_service'):
            self.audio_service.stop_all()
        # Останавливаем музыку и очищаем ресурсы
        if hasattr(self, 'music_service'):
            self.music_service.cleanup()
        # Сохраняем все данные перед закрытием
        if hasattr(self, 'word_repository'):
            self.word_repository.save_data()
        event.accept()
        
    def _safe_disconnect_category_signal(self):
        """Безопасно отключает сигнал изменения категории"""
        try:
            if hasattr(self, 'category_signal_connected') and self.category_signal_connected:
                self.category_combo.currentTextChanged.disconnect(self.on_category_changed)
                self.category_signal_connected = False
        except (TypeError, RuntimeError):
            # Если сигнал не был подключен, игнорируем ошибку
            self.category_signal_connected = False

    def _safe_connect_category_signal(self):
        """Безопасно подключает сигнал изменения категории"""
        try:
            # Сначала отключаем, если был подключен
            if hasattr(self, 'category_signal_connected') and self.category_signal_connected:
                try:
                    self.category_combo.currentTextChanged.disconnect(self.on_category_changed)
                except (TypeError, RuntimeError):
                    pass
            
            # Подключаем сигнал
            self.category_combo.currentTextChanged.connect(self.on_category_changed)
            self.category_signal_connected = True
        except (TypeError, RuntimeError):
            self.category_signal_connected = False