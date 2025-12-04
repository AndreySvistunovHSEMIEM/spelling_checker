"""Диалоги импорта и экспорта данных"""
import json
import logging
import os
import re
from typing import Dict, Any

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                              QLineEdit, QComboBox, QListWidget, QTreeWidgetItem,
                              QGroupBox, QFileDialog, QInputDialog, QMessageBox, QGridLayout, QCheckBox, QListWidgetItem, QFormLayout)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

from core.constants import Constants
from core.models import WordData
from utils.helpers import show_silent_message


logger = logging.getLogger(__name__)


class BulkImportDialog(QDialog):
    """Диалог массового импорта слов"""
    
    def __init__(self, parent, word_repository, media_manager):
        super().__init__(parent)
        self.word_repository = word_repository
        self.media_manager = media_manager
        self.selected_files = []
        
        self.setWindowTitle("Массовый импорт слов")
        self.setModal(True)
        self.resize(500, 400)
        self._create_ui()
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Выбор категории
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Категория:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.word_repository.app_data.categories)
        
        # Если категорий нет, создаем стандартную
        if not self.word_repository.app_data.categories:
            self.word_repository.add_category("Слова")
            self.word_repository.save_data()
            self.category_combo.addItems(["Слова"])
        
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        
        layout.addLayout(category_layout)
        
        # Область выбора файлов
        files_group = QGroupBox("Выбор файлов")
        files_layout = QVBoxLayout(files_group)
        
        # Кнопка выбора файлов
        select_files_btn = QPushButton("📁 Выбрать файлы")
        select_files_btn.clicked.connect(self._select_files)
        files_layout.addWidget(select_files_btn)
        
        # Список найденных пар файлов
        self.files_list = QListWidget()
        files_layout.addWidget(self.files_list)
        
        layout.addWidget(files_group)
        
        # Статистика
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Найдено пар файлов: 0")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Инструкция
        instruction = QLabel(
            "Формат файлов:\n"
            "• Для каждого слова должны быть файлы с одинаковым названием:\n"
            "  слово.mp3 (обязательно) + слово.jpg (опционально)\n"
            "• Пример: морковь.mp3 и морковь.jpg\n"
            "• Файлы без пары (только картинки) игнорируются"
        )
        instruction.setStyleSheet("color: gray; font-size: 10px;")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        import_btn = QPushButton("Импортировать")
        import_btn.clicked.connect(self._import_files)
        button_layout.addWidget(import_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _select_files(self):
        """Выбор файлов"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Выберите файлы", 
            "", 
            "Медиа файлы (*.mp3 *.wav *.ogg *.jpg *.jpeg *.png *.gif *.bmp)"
        )
        
        if files:
            self._process_selected_files(files)
    
    def _process_selected_files(self, file_paths):
        """Обрабатывает выбранные файлы и находит пары"""
        self.selected_files = []
        self.files_list.clear()
        
        # Группируем файлы по имени (без расширения)
        audio_files = {}
        image_files = {}
        
        supported_audio = {'.mp3', '.wav', '.ogg'}
        supported_images = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            ext_lower = ext.lower()
            
            if ext_lower in supported_audio:
                audio_files[name.lower()] = file_path
            elif ext_lower in supported_images:
                image_files[name.lower()] = file_path
        
        # Находим пары: файлы с одинаковыми именами
        for audio_name, audio_path in audio_files.items():
            image_path = image_files.get(audio_name)
            
            # Извлекаем слово из имени файла
            word = self._filename_to_word(audio_name)
            
            if word:
                self.selected_files.append({
                    'word': word,
                    'audio_path': audio_path,
                    'image_path': image_path,
                    'audio_filename': os.path.basename(audio_path)
                })
                
                # Добавляем в список
                item_text = f"{word}"
                if image_path:
                    item_text += f" 🔊+🖼️ ({os.path.basename(audio_path)}, {os.path.basename(image_path)})"
                else:
                    item_text += f" 🔊 ({os.path.basename(audio_path)})"
                
                item = QListWidgetItem(item_text)
                self.files_list.addItem(item)
        
        # Обновляем статистику
        self.stats_label.setText(f"Найдено пар файлов: {len(self.selected_files)}")
    
    def _filename_to_word(self, filename):
        """Преобразует имя файла в слово"""
        # Убираем цифры и специальные символы в начале/конце
        import re
        clean_name = re.sub(r'^[\d_\-\s]+|[\d_\-\s]+$', '', filename)
        clean_name = clean_name.replace('_', ' ').strip()
        
        # Делаем первую букву заглавной если нужно
        if clean_name and not clean_name[0].isupper():
            clean_name = clean_name.capitalize()
            
        return clean_name if clean_name else None
    
    def _import_files(self):
        """Импортирует выбранные файлы с учетом дубликатов"""
        if not self.selected_files:
            QMessageBox.warning(self, "Ошибка", "Нет файлов для импорта!")
            return
        
        category = self.category_combo.currentText()
        if not category:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию!")
            return
        
        # Статистика
        words_created = 0
        audio_imported = 0
        images_imported = 0
        duplicates_skipped = 0
        duplicate_words = []  # Список пропущенных дубликатов
        
        # Импортируем каждую пару файлов
        for file_data in self.selected_files:
            try:
                word = file_data['word']
                audio_path = file_data['audio_path']
                image_path = file_data['image_path']
                
                # ПРОВЕРКА НА ДУБЛИКАТЫ через новый метод
                if self.word_repository.word_exists(word):
                    duplicates_skipped += 1
                    duplicate_words.append(word)
                    continue  # Пропускаем дубликаты
                
                # Копируем аудио файл
                audio_filename = self.media_manager.save_audio_file(audio_path, word)
                audio_imported += 1
                
                # Копируем изображение если есть
                image_filenames = []
                if image_path and os.path.exists(image_path):
                    image_filename = self.media_manager.save_image_file(image_path, word, [])
                    image_filenames.append(image_filename)
                    images_imported += 1
                
                # Создаем слово
                word_data = WordData(
                    word=word,
                    categories=[category],
                    audio=audio_filename,
                    images=image_filenames,
                    case_sensitive=False,
                    important_positions=""
                )
                
                self.word_repository.add_word(word_data)
                words_created += 1
                
            except Exception as e:
                logger.exception("Ошибка при импорте слова %s: %s", file_data.get('word', 'unknown'), e)
                continue
        
        # Сохраняем данные
        self.word_repository.save_data()
        
        # Показываем результат с информацией о дубликатах
        result_message = (
            f"Импорт завершен!\n\n"
            f"Создано слов: {words_created}\n"
            f"Импортировано аудио: {audio_imported}\n"
            f"Импортировано изображений: {images_imported}"
        )
        
        if duplicates_skipped > 0:
            result_message += f"\n\nПропущено дубликатов: {duplicates_skipped}"
            if duplicate_words:
                # Показываем первые 10 дубликатов чтобы не перегружать сообщение
                shown_duplicates = duplicate_words[:10]
                duplicates_text = ", ".join(shown_duplicates)
                if len(duplicate_words) > 10:
                    duplicates_text += f" ... (ещё {len(duplicate_words) - 10})"
                result_message += f"\nДубликаты: {duplicates_text}"
        
        QMessageBox.information(self, "Результат импорта", result_message)
        self.accept()


class ExportCategoriesDialog(QDialog):
    """Диалог выбора категорий для экспорта"""
    
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.categories = categories
        self.selected_categories = []
        
        self.setWindowTitle("Выбор категорий для экспорта")
        self.setModal(True)
        self.resize(300, 400)
        self._create_ui()
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        layout.addWidget(QLabel("Выберите категории для экспорта:"))
        
        # Список категорий с чекбоксами
        self.categories_list = QListWidget()
        
        for category in self.categories:
            item = QListWidgetItem(category)
            item.setCheckState(Qt.Unchecked)
            self.categories_list.addItem(item)
        
        layout.addWidget(self.categories_list)
        
        # Кнопки выбора всех/очистки
        selection_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Выбрать все")
        select_all_btn.clicked.connect(self._select_all)
        selection_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("Очистить")
        clear_all_btn.clicked.connect(self._clear_all)
        selection_layout.addWidget(clear_all_btn)
        
        layout.addLayout(selection_layout)
        
        # Кнопки OK/Отмена
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("Экспорт")
        ok_btn.clicked.connect(self._export)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _select_all(self):
        """Выбирает все категории"""
        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            item.setCheckState(Qt.Checked)
    
    def _clear_all(self):
        """Очищает все выборы"""
        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def _export(self):
        """Экспортирует выбранные категории"""
        self.selected_categories = []
        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_categories.append(item.text())
        
        if not self.selected_categories:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну категорию!")
            return
        
        self.accept()
    
    def get_selected_categories(self):
        """Возвращает выбранные категории"""
        return self.selected_categories
        

__all__ = ['BulkImportDialog', 'ExportCategoriesDialog']