"""Константы приложения"""
import os
import sys
import logging
import shutil
from pathlib import Path

class Constants:
    # Размеры окон
    DEFAULT_WINDOW_SIZE = (900, 700)
    DIALOG_SIZE = (600, 500)
    SETTINGS_DIALOG_SIZE = (300, 150)
    PROBLEM_WORDS_DIALOG_SIZE = (500, 400)
    CHANGE_PASSWORD_DIALOG_SIZE = (300, 150)
    
    # Размеры изображений
    IMAGE_WIDTH = 640
    IMAGE_HEIGHT = 290
    
    # Награды и штрафы
    DEFAULT_COST_PER_WORD = 0.5
    DEFAULT_PENALTY_PER_WORD = 0.25
    
    # Тайминг автоматического перехода (в миллисекундах)
    AUTO_NEXT_WORD_DELAY = 1300
    
    # Пароль для настроек
    SETTINGS_PASSWORD = "1234"
    
    # Музыка
    MUSIC_VOLUME = 0.05  # Громкость музыки (0.0 - 1.0)
    DEFAULT_MUSIC_ENABLED = True  # Музыка включена по умолчанию
    
    # Имена файлов и папок (теперь это только имена, не пути)
    WORDS_FILE = "words.json"
    PROGRESS_FILE = "progress.json"
    SETTINGS_FILE = "settings.json"
    IMAGES_FOLDER = "images"
    AUDIO_FOLDER = "audio"
    MUSIC_FOLDER = "music"
    DEFAULT_IMAGE = "icons/sound_no_image.png"
    APP_ICON = "app_icon.ico"
    CORRECT_SOUND = "correct.mp3"
    INCORRECT_SOUND = "incorrect.mp3"
    
    # Настройки по умолчанию
    DEFAULT_SHOW_CORRECT_ANSWER = True
    
    # Автовоспроизведение звука при переходе на следующее слово
    AUTO_PLAY_DELAY = 500  # 0.5 секунды в миллисекундах
    AUTO_PLAY_ENABLED = True  # Включено по умолчанию
    
    # Иконки
    CORRECT_ICON = "icons/correct_icon.png"
    INCORRECT_ICON = "icons/incorrect_icon.png"
    ADD_WORD_ICON = "icons/add_word_icon.png"
    BULK_WORD_ICON = "icons/bulk_word_icon.png"
    EDIT_WORD_ICON = "icons/edit_word_icon.png"
    TRANS_CATEGORY_ICON = "icons/trans_category_icon.png"
    DELETE_WORD_ICON = "icons/delete_word_icon.png"
    IMPORT_WORD_ICON = "icons/import_word_icon.png"
    EXPORT_WORD_ICON = "icons/export_word_icon.png"
    RESET_SCORE_ICON = "icons/reset_score_icon.png"
    MANAGER_WORD_ICON = "icons/manager_word_icon.png"
    MISTAKE_WORD_ICON = "icons/mistake_word_icon.png"
    RESET_PROGRESS_ICON = "icons/reset_progress_icon.png"
    SETTINGS_ICON = "icons/settings_icon.png"
    LISTEN_ICON = "icons/listen_icon.png"
    CHANGE_PASSWORD_ICON = "icons/change_password_icon.png"
    MUSIC_ICON = "icons/music_icon.png"
    MUSIC_OFF_ICON = "icons/music_off_icon.png"
    
    @staticmethod
    def _migrate_data_if_needed(new_data_dir: str):
        """
        Мигрирует данные из старой директории в новую, если новая директория пуста
        """
        import shutil
        import logging
        logger = logging.getLogger(__name__)
        
        # Проверяем, есть ли уже данные в новой директории
        new_words_file = os.path.join(new_data_dir, Constants.WORDS_FILE)
        new_progress_file = os.path.join(new_data_dir, Constants.PROGRESS_FILE)
        new_settings_file = os.path.join(new_data_dir, Constants.SETTINGS_FILE)
        new_images_dir = os.path.join(new_data_dir, Constants.IMAGES_FOLDER)
        new_audio_dir = os.path.join(new_data_dir, Constants.AUDIO_FOLDER)
        
        # Если в новой директории уже есть хотя бы один из основных файлов, считаем что миграция уже выполнена
        has_existing_data = (os.path.exists(new_words_file) or
                            os.path.exists(new_progress_file) or
                            os.path.exists(new_settings_file))
                            
        if has_existing_data:
            logger.info("Данные уже существуют в новой директории, миграция не требуется")
            return
        
        # Определяем возможные старые директории для поиска данных
        # В оригинальной версии приложения main_window.py находится в ui/, и данные также могли быть там
        possible_old_dirs = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui'),  # ../ui
            os.path.dirname(os.path.abspath(__file__)),  # ./core (где находится Constants.py)
        ]
        
        # Ищем файлы данных в возможных старых директориях
        old_data_dir = None
        for possible_dir in possible_old_dirs:
            words_path = os.path.join(possible_dir, Constants.WORDS_FILE)
            if os.path.exists(words_path):
                old_data_dir = possible_dir
                logger.info(f"Найдены данные в старой директории: {old_data_dir}")
                break
        
        if old_data_dir is None:
            logger.info("Старые данные не найдены, миграция не требуется")
            return
        
        logger.info(f"Попытка миграции данных из {old_data_dir} в {new_data_dir}")
        
        # Пути к старым файлам
        old_words_file = os.path.join(old_data_dir, Constants.WORDS_FILE)
        old_progress_file = os.path.join(old_data_dir, Constants.PROGRESS_FILE)
        old_settings_file = os.path.join(old_data_dir, Constants.SETTINGS_FILE)
        old_images_dir = os.path.join(old_data_dir, Constants.IMAGES_FOLDER)
        old_audio_dir = os.path.join(old_data_dir, Constants.AUDIO_FOLDER)
        
        # Копируем файлы, если они существуют
        files_to_migrate = [
            (old_words_file, new_words_file),
            (old_progress_file, new_progress_file),
            (old_settings_file, new_settings_file)
        ]
        
        for old_path, new_path in files_to_migrate:
            if os.path.exists(old_path):
                try:
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    shutil.copy2(old_path, new_path)
                    logger.info(f"Скопирован файл: {old_path} -> {new_path}")
                except Exception as e:
                    logger.error(f"Ошибка копирования файла {old_path}: {e}")
            else:
                logger.info(f"Файл не существует, пропущен: {old_path}")
        
        # Копируем папки, если они существуют
        dirs_to_migrate = [
            (old_images_dir, new_images_dir),
            (old_audio_dir, new_audio_dir)
        ]
        
        for old_path, new_path in dirs_to_migrate:
            if os.path.exists(old_path):
                try:
                    if os.path.exists(new_path):
                        shutil.rmtree(new_path)  # Удаляем старую папку, если существует
                    shutil.copytree(old_path, new_path)
                    logger.info(f"Скопирована папка: {old_path} -> {new_path}")
                except Exception as e:
                    logger.error(f"Ошибка копирования папки {old_path}: {e}")
            else:
                logger.info(f"Папка не существует, пропущена: {old_path}")
        
        logger.info("Миграция данных завершена")

    @staticmethod
    def get_data_directory():
        """
        Умное определение папки для данных:
        - Если программа собрана в exe: используем AppData
        - Если запущена из исходников: используем папку рядом
        """
        if getattr(sys, 'frozen', False):
            # Режим exe: сохраняем в AppData
            appdata = Path(os.environ.get('APPDATA', Path.home()))
            data_dir = appdata / "Orfocode"
            data_dir.mkdir(exist_ok=True)
            # Выполняем миграцию, если нужно
            Constants._migrate_data_if_needed(str(data_dir))
            return str(data_dir)
        else:
            # Режим разработки: сохраняем рядом с программой
            dev_dir = os.path.dirname(os.path.abspath(__file__))
            # Выполняем миграцию, если нужно
            Constants._migrate_data_if_needed(dev_dir)
            return dev_dir