"""Менеджер для работы с медиафайлами"""
import logging
import os
import shutil
from typing import List, Optional
from .constants import Constants
from .models import WordData

logger = logging.getLogger(__name__)

class MediaManager:
    """
    Класс для управления медиафайлами (изображения и аудио)
    Отвечает за сохранение, удаление и проверку файлов
    """
    
    def __init__(self, base_dir: str):
        """
        Инициализация менеджера
        
        Args:
            base_dir: Основная папка приложения
        """
        self.base_dir = base_dir
        # Используем get_data_directory() для определения путей к папкам
        data_dir = Constants.get_data_directory()
        self.images_folder = os.path.join(data_dir, Constants.IMAGES_FOLDER)
        self.audio_folder = os.path.join(data_dir, Constants.AUDIO_FOLDER)
        self.default_image = os.path.join(data_dir, Constants.DEFAULT_IMAGE)
        
        # Создаём папки, если они не существуют
        self._create_folders()
    
    def _create_folders(self):
        """Создаёт необходимые папки для медиафайлов"""
        try:
            os.makedirs(self.images_folder, exist_ok=True)
            os.makedirs(self.audio_folder, exist_ok=True)
        except OSError as e:
            logger.error("Не удалось создать папки для медиафайлов: %s", e)
            raise
    
    def transliterate(self, text: str) -> str:
        """
        Преобразует русский текст в латиницу для имён файлов
        
        Args:
            text: Текст для преобразования
            
        Returns:
            Текст в латинице
        """
        translit_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            ' ': '_'
        }
        
        text = text.lower().strip()
        result = []
        for char in text:
            if char in translit_dict:
                result.append(translit_dict[char])
            elif char.isalnum():
                result.append(char)
            else:
                result.append('_')
        
        return ''.join(result)
    
    def get_unique_filename(self, base_name: str, extension: str, folder: str, 
                          existing_files: Optional[List[str]] = None) -> str:
        """
        Генерирует уникальное имя файла
        
        Args:
            base_name: Базовое имя файла
            extension: Расширение файла
            folder: Папка для проверки
            existing_files: Список существующих файлов
            
        Returns:
            Уникальное имя файла
        """
        if not os.path.exists(folder):
            return f"{base_name}.{extension}"
            
        if existing_files is None:
            existing_files = os.listdir(folder)
        
        counter = 1
        test_name = f"{base_name}.{extension}"
        
        if test_name not in existing_files:
            return test_name
        
        while True:
            test_name = f"{base_name}_{counter}.{extension}"
            if test_name not in existing_files:
                return test_name
            counter += 1
    
    def save_audio_file(self, source_path: str, word: str) -> str:
        """
        Сохраняет аудиофайл для слова
        
        Args:
            source_path: Путь к исходному файлу
            word: Слово для которого сохраняем
            
        Returns:
            Имя сохранённого файла
        """
        base_name = self.transliterate(word or "audio")
        extension = source_path.split('.')[-1].lower()
        
        if not os.path.exists(source_path):
            logger.error("Исходный аудиофайл не найден: %s", source_path)
            raise FileNotFoundError(f"Аудиофайл не найден: {source_path}")
        
        existing_files = os.listdir(self.audio_folder) if os.path.exists(self.audio_folder) else []
        new_filename = self.get_unique_filename(base_name, extension, self.audio_folder, existing_files)
        destination_path = os.path.join(self.audio_folder, new_filename)
        
        try:
            shutil.copy(source_path, destination_path)
            logger.debug("Аудиофайл сохранен: %s -> %s", source_path, destination_path)
        except (OSError, IOError) as e:
            logger.error("Ошибка при копировании аудиофайла %s: %s", source_path, e)
            raise
        return new_filename
    
    def save_image_file(self, source_path: str, word: str, existing_images: List[str]) -> str:
        """
        Сохраняет изображение для слова
        
        Args:
            source_path: Путь к исходному файлу
            word: Слово для которого сохраняем
            existing_images: Существующие изображения слова
            
        Returns:
            Имя сохранённого файла
        """
        base_name = self.transliterate(word or "image")
        extension = source_path.split('.')[-1].lower()
        
        all_images = os.listdir(self.images_folder) if os.path.exists(self.images_folder) else []
        # Исключаем существующие изображения этого слова из проверки
        other_images = [img for img in all_images if img not in existing_images]
        
        if not os.path.exists(source_path):
            logger.error("Исходный файл изображения не найден: %s", source_path)
            raise FileNotFoundError(f"Файл изображения не найден: {source_path}")
        
        new_filename = self.get_unique_filename(base_name, extension, self.images_folder, other_images + existing_images)
        destination_path = os.path.join(self.images_folder, new_filename)
        
        try:
            shutil.copy(source_path, destination_path)
            logger.debug("Изображение сохранено: %s -> %s", source_path, destination_path)
        except (OSError, IOError) as e:
            logger.error("Ошибка при копировании изображения %s: %s", source_path, e)
            raise
        return new_filename
    
    def delete_media_files(self, word_data: 'WordData'):
        """
        Удаляет медиафайлы слова
        
        Args:
            word_data: Данные слова
        """
        # Удаляем аудио
        if word_data.audio:
            audio_path = os.path.join(self.audio_folder, word_data.audio)
            self._safe_delete(audio_path)
        
        # Удаляем изображения
        for image_name in word_data.images:
            image_path = os.path.join(self.images_folder, image_name)
            self._safe_delete(image_path)
    
    def _safe_delete(self, file_path: str):
        """
        Безопасное удаление файла (не вызывает ошибку если файла нет)
        
        Args:
            file_path: Путь к файлу
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("Файл удален: %s", file_path)
        except OSError as e:
            logger.warning("Не удалось удалить файл %s: %s", file_path, e)
        except Exception as e:
            logger.warning("Неожиданная ошибка при удалении файла %s: %s", file_path, e)
    
    def get_available_images(self, image_names: List[str]) -> List[str]:
        """
        Возвращает список доступных изображений
        
        Args:
            image_names: Список имён изображений
            
        Returns:
            Список существующих изображений
        """
        if not image_names:
            return []
        
        return [img for img in image_names if img and os.path.exists(os.path.join(self.images_folder, img))]
    
    def audio_exists(self, audio_name: str) -> bool:
        """
        Проверяет существование аудиофайла
        
        Args:
            audio_name: Имя аудиофайла
            
        Returns:
            True если файл существует
        """
        if not audio_name:
            return False
        return os.path.exists(os.path.join(self.audio_folder, audio_name))
        
    def validate_media_files(self, word_data: WordData) -> WordData:
        """
        Проверяет и восстанавливает медиафайлы слова
        
        Args:
            word_data: Данные слова для проверки
            
        Returns:
            Исправленные данные слова
        """
        # Проверяем и исправляем аудио
        if word_data.audio:
            audio_path = os.path.join(self.audio_folder, word_data.audio)
            if not os.path.exists(audio_path):
                # Ищем в папке images
                audio_in_images = os.path.join(self.images_folder, word_data.audio)
                if os.path.exists(audio_in_images):
                    # Копируем в правильную папку
                    try:
                        shutil.copy2(audio_in_images, audio_path)
                        logger.info("Восстановлен аудиофайл из папки images: %s", word_data.audio)
                    except (OSError, IOError) as e:
                        logger.warning("Не удалось восстановить аудиофайл %s: %s", word_data.audio, e)
                        word_data.audio = ""  # Удаляем ссылку если не удалось восстановить
                else:
                    logger.debug("Аудиофайл не найден: %s", word_data.audio)
                    word_data.audio = ""  # Удаляем ссылку если файл не существует
        
        # Проверяем и исправляем изображения
        valid_images = []
        for image_name in word_data.images:
            image_path = os.path.join(self.images_folder, image_name)
            if os.path.exists(image_path):
                valid_images.append(image_name)
        
        word_data.images = valid_images
        return word_data