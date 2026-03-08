"""Диалоги управления словами"""
import json
import logging
import os
import re
from typing import Dict, Any

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QLineEdit, QComboBox, QListWidget, QTreeWidget, QTreeWidgetItem,
                              QGroupBox, QFileDialog, QInputDialog, QMessageBox, QGridLayout, QCheckBox, QListWidgetItem, QFormLayout)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

from core.constants import Constants
from core.models import WordData
from utils.helpers import show_silent_message
from ui.dialogs.import_export.data_dialogs import BulkImportDialog, ExportCategoriesDialog
from ui.dialogs.word_management.category_management_dialog import CategoryManagementDialog


logger = logging.getLogger(__name__)


class WordManagerDialog(QDialog):
    def __init__(self, parent, word_repository, media_manager):
        super().__init__(parent)
        self.word_repository = word_repository
        self.media_manager = media_manager
        self.current_category_filter = "Все"  # текущий фильтр
        
        self.setWindowTitle("Управление словами")
        self.setModal(True)
        self.resize(500, 400)
        self.setMinimumSize(500, 400)
        self.setMaximumSize(500, 1000)
        self._create_ui()
        
        # Устанавливаем иконку окна
        manager_icon_path = os.path.join(parent.base_dir, Constants.MANAGER_WORD_ICON)
        if os.path.exists(manager_icon_path):
            self.setWindowIcon(QIcon(manager_icon_path))
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Панель поиска и фильтра
        filter_layout = QHBoxLayout()  # ИЗМЕНИЛ НАЗВАНИЕ НА filter_layout
        
        # Поиск
        #filter_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск")
        self.search_edit.textChanged.connect(self._filter_words)
        filter_layout.addWidget(self.search_edit)
        
        # Кнопка сброса поиска
        clear_search_btn = QPushButton("❌")
        clear_search_btn.setToolTip("Очистить поиск")
        clear_search_btn.setFixedWidth(30)
        clear_search_btn.clicked.connect(self._clear_search)
        filter_layout.addWidget(clear_search_btn)
        
        # Фильтр по категориям
        filter_layout.addWidget(QLabel("Категория:"))
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("Все")
        self.category_filter_combo.addItems(self.word_repository.app_data.categories)
        self.category_filter_combo.currentTextChanged.connect(self._on_category_filter_changed)
        filter_layout.addWidget(self.category_filter_combo)
        
        manage_categories_btn = QPushButton("⚙️")
        manage_categories_btn.setToolTip("Управление категориями")
        manage_categories_btn.setFixedSize(24, 24) 
        manage_categories_btn.clicked.connect(self._manage_categories)
        filter_layout.addWidget(manage_categories_btn)
        
        layout.addLayout(filter_layout)  # ТЕПЕРЬ ИСПОЛЬЗУЕМ filter_layout
        
        # ТАБЛИЦА слов вместо списка
        self.words_tree = QTreeWidget()
        self.words_tree.setHeaderLabels(["Слово", "Картинка", "Звук", "Регистр", "Категории"])
        self.words_tree.setColumnWidth(0, 110)
        self.words_tree.setColumnWidth(1, 70)
        self.words_tree.setColumnWidth(2, 40)
        self.words_tree.setColumnWidth(3, 60)
        self.words_tree.setColumnWidth(4, 100)
        self.words_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self._refresh_words_tree()
        layout.addWidget(self.words_tree)
        
        # Кнопки управления
        button_layout = QHBoxLayout()

        # Кнопка "Добавить слово" с иконкой
        add_btn = QPushButton()
        add_btn_icon_path = os.path.join(self.parent().base_dir, Constants.ADD_WORD_ICON)
        icon = QIcon(add_btn_icon_path)
        add_btn.setIcon(icon)
        add_btn.setIconSize(QSize(28, 28))
        add_btn.setToolTip("Добавить слово")
        add_btn.clicked.connect(self._add_word)
        add_btn.setFixedSize(40, 30)
        button_layout.addWidget(add_btn)

        # Кнопка "Массовый импорт слов" с иконкой
        bulk_import_btn = QPushButton()
        bulk_import_icon_path = os.path.join(self.parent().base_dir, Constants.BULK_WORD_ICON)
        icon = QIcon(bulk_import_icon_path)
        bulk_import_btn.setIcon(icon)
        bulk_import_btn.setIconSize(QSize(28, 28))
        bulk_import_btn.setToolTip("Массовый импорт слов")
        bulk_import_btn.clicked.connect(self._bulk_import_words)
        bulk_import_btn.setFixedSize(40, 30)
        button_layout.addWidget(bulk_import_btn)

        # Кнопка "Редактировать слово" с иконкой
        edit_btn = QPushButton()
        edit_icon_path = os.path.join(self.parent().base_dir, Constants.EDIT_WORD_ICON)
        icon = QIcon(edit_icon_path)
        edit_btn.setIcon(icon)
        edit_btn.setIconSize(QSize(28, 28))
        edit_btn.setToolTip("Редактировать слово")
        edit_btn.clicked.connect(self._edit_word)
        edit_btn.setFixedSize(40, 30)
        button_layout.addWidget(edit_btn)

        # Кнопка "Удалить слово" с иконкой
        delete_btn = QPushButton()
        delete_icon_path = os.path.join(self.parent().base_dir, Constants.DELETE_WORD_ICON)
        icon = QIcon(delete_icon_path)
        delete_btn.setIcon(icon)
        delete_btn.setIconSize(QSize(28, 28))
        delete_btn.setToolTip("Удалить слово")
        delete_btn.clicked.connect(self._delete_word)
        delete_btn.setFixedSize(40, 30)
        button_layout.addWidget(delete_btn)

        # Кнопка "Перемещение в категориях" с иконкой
        move_categories_btn = QPushButton()
        move_icon_path = os.path.join(self.parent().base_dir, Constants.TRANS_CATEGORY_ICON)
        icon = QIcon(move_icon_path)
        move_categories_btn.setIcon(icon)
        move_categories_btn.setIconSize(QSize(28, 28))
        move_categories_btn.setToolTip("Переместить/скопировать в категорию")
        move_categories_btn.clicked.connect(self._move_categories)
        move_categories_btn.setFixedSize(40, 30)
        button_layout.addWidget(move_categories_btn)

        button_layout.addStretch()

        # Кнопка "Импорт" с иконкой
        import_btn = QPushButton()
        import_icon_path = os.path.join(self.parent().base_dir, Constants.IMPORT_WORD_ICON)
        icon = QIcon(import_icon_path)
        import_btn.setIcon(icon)
        import_btn.setIconSize(QSize(28, 28))
        import_btn.setToolTip("Импорт слов из архива")
        import_btn.clicked.connect(self._import_data)
        import_btn.setFixedSize(40, 30)
        button_layout.addWidget(import_btn)

        # Кнопка "Экспорт" с иконкой
        export_btn = QPushButton()
        export_icon_path = os.path.join(self.parent().base_dir, Constants.EXPORT_WORD_ICON)
        icon = QIcon(export_icon_path)
        export_btn.setIcon(icon)
        export_btn.setIconSize(QSize(28, 28))
        export_btn.setToolTip("Экспорт слов в архив")
        export_btn.clicked.connect(self._export_data)
        export_btn.setFixedSize(40, 30)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _on_category_filter_changed(self, category_filter):
        """Обработчик изменения фильтра категорий"""
        self.current_category_filter = category_filter
        self._refresh_words_tree()
    
    def _refresh_words_tree(self):
        """Обновляет таблицу слов с учетом фильтров - показываем все слова без группировки"""
        self.words_tree.clear()
        
        # Фильтруем слова по категории
        filtered_words = []
        if self.current_category_filter == "Все":
            filtered_words = self.word_repository.app_data.words
        else:
            filtered_words = self.word_repository.get_words_by_category(self.current_category_filter)
        
        # Фильтруем по поисковому запросу
        search_text = self.search_edit.text().lower().strip()
        if search_text:
            filtered_words = [word for word in filtered_words if search_text in word.word.lower()]
        
        # Показываем КАЖДОЕ слово отдельно без какой-либо группировки
        for word_data in filtered_words:
            image_icon = "✅" if word_data.images else ""
            audio_icon = "✅" if word_data.audio else ""
            case_icon = "✅" if word_data.case_sensitive else ""
            
            # Категории через запятую
            categories_text = ", ".join(sorted(word_data.categories))
            
            item = QTreeWidgetItem([
                word_data.word,  # Просто слово, без uid и пометок
                image_icon,
                audio_icon,
                case_icon,
                categories_text
            ])
            
            # Сохраняем оригинальные данные слова
            item.setData(0, Qt.UserRole, word_data)
            self.words_tree.addTopLevelItem(item)
    
    def _filter_words(self, search_text):
        """Фильтрует слова по поисковому запросу"""
        search_text = search_text.lower().strip()
        
        if not search_text:
            # Если поиск пустой, показываем все слова
            self._refresh_words_tree()
            return
        
        # Скрываем/показываем элементы
        for i in range(self.words_tree.topLevelItemCount()):
            item = self.words_tree.topLevelItem(i)
            word_name = item.text(0).lower()
            if search_text in word_name:
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _clear_search(self):
        """Очищает поле поиска"""
        self.search_edit.clear()
        self._refresh_words_tree()
    
    def _move_categories(self):
        """Открывает диалог перемещения/копирования слов между категориями"""
        selected_items = self.words_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите слова для перемещения/копирования!")
            return
        
        # Получаем оригинальные данные слов
        words_to_process = []
        for item in selected_items:
            word_data = item.data(0, Qt.UserRole)
            words_to_process.append(word_data)
        
        dialog = CategoryMoveDialog(self, self.word_repository, words_to_process)
        if dialog.exec():
            self._refresh_words_tree()
            # Сообщение теперь показывается внутри диалога
        
    def _bulk_import_words(self):
        """Массовый импорт слов из папки"""
        dialog = BulkImportDialog(self, self.word_repository, self.media_manager)
        if dialog.exec():
            self._refresh_words_tree()
    
    def _add_word(self):
        """Добавляет новое слово"""
        dialog = WordEditorDialog(self, self.word_repository, self.media_manager)
        if dialog.exec():
            self._refresh_words_tree()
    
    def _edit_word(self):
        """Редактирует выбранное слово"""
        selected_items = self.words_tree.selectedItems()
        if len(selected_items) != 1:
            QMessageBox.warning(self, "Ошибка", "Выберите одно слово для редактирования!")
            return
        
        # Получаем оригинальные данные слова из UserRole
        word_data = selected_items[0].data(0, Qt.UserRole)
        
        # Находим индекс в основном списке
        try:
            index = self.word_repository.app_data.words.index(word_data)
            dialog = WordEditorDialog(self, self.word_repository, self.media_manager, index)
            if dialog.exec():
                self._refresh_words_tree()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти слово в списке!")
    
    def _delete_word(self):
        """Удаляет выбранные слова"""
        selected_items = self.words_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите слова для удаления!")
            return
        
        # Получаем оригинальные данные слов из UserRole
        words_to_delete = []
        for item in selected_items:
            word_data = item.data(0, Qt.UserRole)
            words_to_delete.append(word_data)
        
        if len(words_to_delete) == 1:
            reply = QMessageBox.question(self, "Подтверждение", 
                                       f"Удалить слово '{words_to_delete[0].word}'?")
        else:
            reply = QMessageBox.question(self, "Подтверждение", 
                                       f"Удалить выбранные {len(words_to_delete)} слов?")
        
        if reply == QMessageBox.Yes:
            # Удаляем слова по оригинальным данным
            for word_data in words_to_delete:
                try:
                    index = self.word_repository.app_data.words.index(word_data)
                    
                    # Удаляем слово через репозиторий (метод всегда существует)
                    self.word_repository.delete_word(index)
                    
                except ValueError as e:
                    logger.exception("Ошибка при удалении слова: %s", e)
                    continue
            
            self._refresh_words_tree()
            
    def _manage_categories(self):
        """Открывает диалог управления категориями"""
        dialog = CategoryManagementDialog(self, self.word_repository)
        if dialog.exec():
            # Обновляем интерфейс после закрытия диалога
            self.category_filter_combo.clear()
            self.category_filter_combo.addItem("Все")
            self.category_filter_combo.addItems(self.word_repository.app_data.categories)
            self._refresh_words_tree()
        
    def _export_data(self):
        """Экспорт данных в архивный файл"""
        if not self.word_repository.app_data.words:
            QMessageBox.warning(self, "Ошибка", "Нет слов для экспорта!")
            return
        
        # Показываем диалог выбора категорий
        categories = self.word_repository.app_data.categories
        if not categories:
            QMessageBox.warning(self, "Ошибка", "Нет категорий для экспорта!")
            return
        
        dialog = ExportCategoriesDialog(self, categories)
        if not dialog.exec():
            return  # Пользователь отменил
        
        selected_categories = dialog.get_selected_categories()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт данных", "Слова_тренажёр.zip", "ZIP Archives (*.zip)"
        )
        
        if not filename:
            return
        
        try:
            import zipfile
            import tempfile
            import shutil
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Фильтруем слова по выбранным категориям
                words_to_export = [
                    word for word in self.word_repository.app_data.words 
                    if any(category in word.categories for category in selected_categories)
                ]
                
                if not words_to_export:
                    QMessageBox.warning(self, "Ошибка", "В выбранных категориях нет слов!")
                    return
                
                # Сохраняем данные только выбранных категорий
                data_file = os.path.join(temp_dir, "words.json")
                self._save_filtered_data(data_file, words_to_export, selected_categories)
                
                # Создаем папки для медиафайлов
                images_dir = os.path.join(temp_dir, "images")
                audio_dir = os.path.join(temp_dir, "audio")
                os.makedirs(images_dir, exist_ok=True)
                os.makedirs(audio_dir, exist_ok=True)
                
                # Собираем все используемые медиафайлы из выбранных слов
                all_images = set()
                all_audio = set()
                
                for word_data in words_to_export:
                    all_images.update(word_data.images)
                    if word_data.audio:
                        all_audio.add(word_data.audio)
                
                # Копируем изображения
                copied_images = 0
                for image_name in all_images:
                    src_path = os.path.join(self.media_manager.images_folder, image_name)
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, os.path.join(images_dir, image_name))
                        copied_images += 1
                
                # Копируем аудиофайлы
                copied_audio = 0
                for audio_name in all_audio:
                    src_path = os.path.join(self.media_manager.audio_folder, audio_name)
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, os.path.join(audio_dir, audio_name))
                        copied_audio += 1
                    else:
                        src_path = os.path.join(self.media_manager.images_folder, audio_name)
                        if os.path.exists(src_path):
                            shutil.copy2(src_path, os.path.join(audio_dir, audio_name))
                            copied_audio += 1
                
                # Создаем архив
                with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Добавляем файл данных
                    zipf.write(data_file, "words.json")
                    
                    # Добавляем изображения
                    images_files = os.listdir(images_dir)
                    for file in images_files:
                        file_path = os.path.join(images_dir, file)
                        arcname = os.path.join("images", file)
                        zipf.write(file_path, arcname)
                    
                    # Добавляем аудио
                    audio_files = os.listdir(audio_dir)
                    for file in audio_files:
                        file_path = os.path.join(audio_dir, file)
                        arcname = os.path.join("audio", file)
                        zipf.write(file_path, arcname)
                
                QMessageBox.information(
                    self, 
                    "Успех", 
                    f"Данные экспортированы в:\n{filename}\n\n"
                    f"Категории: {', '.join(selected_categories)}\n"
                    f"Слов: {len(words_to_export)}\n"
                    f"Изображений: {copied_images}\n"
                    f"Аудиофайлов: {copied_audio}"
                )
            
        except Exception as e:
            logger.exception("Ошибка при экспорте данных: %s", e)
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте: {str(e)}")

    def _save_filtered_data(self, filepath, words, categories):
        """Сохраняет отфильтрованные данные в файл (для экспорта)"""
        try:
            data = {
                "words": [
                    {
                        "word": word.word,
                        "categories": word.categories,
                        "audio": word.audio,
                        "images": word.images,
                        "case_sensitive": word.case_sensitive,
                        "important_positions": word.important_positions,
                        "uid": word.uid
                    }
                    for word in words
                ],
                "categories": categories
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception:
            return False

    def _import_data(self):
        """Импорт данных из архивного файла"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Импорт данных", "", "ZIP Archives (*.zip)"
        )
        
        if not filename:
            return
        
        try:
            import zipfile
            import tempfile
            import shutil
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Распаковываем архив
                with zipfile.ZipFile(filename, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Загружаем данные из JSON
                data_file = os.path.join(temp_dir, "words.json")
                if not os.path.exists(data_file):
                    raise Exception("Файл words.json не найден в архиве")
                
                # Загружаем импортируемые данные
                with open(data_file, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                # Получаем категории из архива
                import_categories = import_data.get("categories", [])
                import_words = import_data.get("words", [])
                
                if not import_categories or not import_words:
                    raise Exception("В архиве нет данных для импорта")
                
                # Обрабатываем конфликты категорий
                existing_categories = set(self.word_repository.app_data.categories)
                category_mapping = {}  # Сопоставление оригинальных категорий с финальными
                
                for category in import_categories:
                    final_category = category
                    counter = 1
                    
                    # Если категория уже существует, добавляем суффикс
                    while final_category in existing_categories:
                        final_category = f"{category}_new{counter}"
                        counter += 1
                    
                    category_mapping[category] = final_category
                    
                    # Добавляем категорию если её нет
                    if final_category not in self.word_repository.app_data.categories:
                        self.word_repository.add_category(final_category)
                        existing_categories.add(final_category)
                
                # Подсчет статистики для отчета
                imported_count = 0
                duplicate_word_uid_count = 0 # Слова с одинаковым word и uid (уже существуют)
                different_word_same_uid_count = 0  # Разные слова с одинаковым uid (нужно менять uid)
                same_word_different_uid_count = 0  # Одинаковые слова с разными uid (разрешено)
                
                # Словарь для отслеживания слов и их uid из импортируемых данных
                import_word_uid_map = {}
                for word_dict in import_words:
                    word_lower = word_dict["word"].lower()
                    uid = word_dict.get("uid", "")
                    if (word_lower, uid) in import_word_uid_map:
                        # Это дубль в импортируемых данных - пропускаем
                        continue
                    import_word_uid_map[(word_lower, uid)] = word_dict
                
                # Словари для отслеживания уже существующих слов и uid
                existing_word_uid_map = {}
                for word_data in self.word_repository.app_data.words:
                    existing_word_uid_map[(word_data.word.lower(), word_data.uid)] = word_data
                
                # Словари для отслеживания слов и их uid из импортируемых данных
                import_word_uid_map = {}
                for word_dict in import_words:
                    word_lower = word_dict["word"].lower()
                    uid = word_dict.get("uid", "")
                    if (word_lower, uid) in import_word_uid_map:
                        # Это дубль в импортируемых данных - пропускаем
                        continue
                    import_word_uid_map[(word_lower, uid)] = word_dict
                
                # Словари для отслеживания уже существующих слов и uid
                existing_word_uid_map = {}
                for word_data in self.word_repository.app_data.words:
                    existing_word_uid_map[(word_data.word.lower(), word_data.uid)] = word_data
                
                
                # Обработка импортируемых слов
                for word_dict in import_words:
                    original_word = word_dict["word"]
                    original_word_lower = original_word.lower()
                    original_uid = word_dict.get("uid", "")
                    
                    # Проверяем, есть ли уже слово с таким же word и uid в существующих данных
                    if (original_word_lower, original_uid) in existing_word_uid_map:
                        duplicate_word_uid_count += 1
                        continue
                    
                    # Проверяем, есть ли уже существующее слово с таким же uid, но другим word
                    uid_exists_with_different_word = any(
                        word_data.uid == original_uid and word_data.word.lower() != original_word_lower
                        for word_data in self.word_repository.app_data.words
                    )
                    
                    # Проверяем, есть ли слово с тем же word, но другим uid (разрешено)
                    word_exists_with_different_uid = any(
                        word_data.word.lower() == original_word_lower and word_data.uid != original_uid
                        for word_data in self.word_repository.app_data.words
                    )
                    
                    # Если uid уже существует с другим словом, меняем uid на новый
                    final_uid = original_uid
                    if uid_exists_with_different_word:
                        different_word_same_uid_count += 1
                        # Генерируем новый уникальный uid
                        existing_uids = {w.uid for w in self.word_repository.app_data.words}
                        final_uid = self.word_repository._generate_numeric_uid(existing_uids)
                    elif word_exists_with_different_uid:
                        # Если слово уже существует с другим uid, это нормально
                        same_word_different_uid_count += 1
                    
                    # Преобразуем категории с учетом конфликтов
                    final_categories = []
                    original_categories = word_dict.get("categories", [])
                    for category in original_categories:
                        final_category = category_mapping.get(category, category)
                        final_categories.append(final_category)
                    
                    # Создаем новое слово
                    word_data = WordData(
                        word=original_word,
                        categories=final_categories,
                        audio=word_dict.get("audio", ""),
                        images=word_dict.get("images", []),
                        case_sensitive=word_dict.get("case_sensitive", False),
                        important_positions=word_dict.get("important_positions", "")
                    )
                    
                    # Устанавливаем финальный uid
                    word_data.uid = final_uid
                    
                    # Добавляем слово в репозиторий
                    self.word_repository.app_data.words.append(word_data)
                    imported_count += 1
                
                # Копируем изображения из папки images
                images_src_dir = os.path.join(temp_dir, "images")
                if os.path.exists(images_src_dir):
                    for image_file in os.listdir(images_src_dir):
                        src_path = os.path.join(images_src_dir, image_file)
                        dest_path = os.path.join(self.media_manager.images_folder, image_file)
                        # Проверяем, не существует ли уже файл
                        if not os.path.exists(dest_path):
                            shutil.copy2(src_path, dest_path)
                
                # Копируем аудио из папки audio
                audio_src_dir = os.path.join(temp_dir, "audio")
                if os.path.exists(audio_src_dir):
                    for audio_file in os.listdir(audio_src_dir):
                        src_path = os.path.join(audio_src_dir, audio_file)
                        dest_path = os.path.join(self.media_manager.audio_folder, audio_file)
                        # Проверяем, не существует ли уже файл
                        if not os.path.exists(dest_path):
                            shutil.copy2(src_path, dest_path)
                
                # Сохраняем данные
                self.word_repository.save_data()
                
            # ОБНОВЛЯЕМ ТЕКУЩУЮ КАТЕГОРИЮ В СОСТОЯНИИ ТРЕНИРОВКИ
            training_state = self.word_repository.app_data.training_state
            if not training_state.current_category and self.word_repository.app_data.categories:
                # Если нет текущей категории, устанавливаем первую доступную
                training_state.current_category = self.word_repository.app_data.categories[0]
                
            # Сохраняем снова с обновленной категорией
            self.word_repository.save_data()

            # Обновляем интерфейс
            self._refresh_words_tree()

            # УВЕДОМЛЯЕМ ГЛАВНОЕ ОКНО ОБ ИЗМЕНЕНИИ ДАННЫХ
            parent = self.parent()
            if parent and hasattr(parent, 'on_category_changed'):
                parent.on_category_changed(training_state.current_category)
            
            # Обновляем интерфейс
            self._refresh_words_tree()
            
            # Показываем результат импорта
            message = f"Импорт завершен!\n\nИмпортировано слов: {imported_count}"
            
            # Добавляем информацию о пропущенных/обработанных словах
            if duplicate_word_uid_count > 0:
                message += f"\n\nПропущено слов (одинаковые слово и uid): {duplicate_word_uid_count}"
            
            if different_word_same_uid_count > 0:
                message += f"\n\nСлов с изменённым uid (разные слова, одинаковый uid): {different_word_same_uid_count}"
            
            if same_word_different_uid_count > 0:
                message += f"\n\nСовпадений по слову с разными uid: {same_word_different_uid_count}"
            
            # Показываем информацию о категориях
            if len(import_categories) == 1:
                original_category = import_categories[0]
                final_category = category_mapping[original_category]
                if original_category == final_category:
                    message += f"\n\nКатегория: '{original_category}'"
                else:
                    message += f"\n\nКатегория: '{original_category}' → '{final_category}' (переименована)"
            else:
                message += f"\n\nКатегории: {len(import_categories)}"
                # Показываем переименованные категории
                renamed_categories = [f"'{orig}' → '{final}'" for orig, final in category_mapping.items() if orig != final]
                if renamed_categories:
                    message += f"\nПереименованные категории:\n" + "\n".join(renamed_categories)
            
            QMessageBox.information(self, "Успех", message)
            
        except Exception as e:
            logger.exception("Ошибка при импорте данных: %s", e)
            QMessageBox.critical(self, "Ошибка", f"Ошибка при импорте: {str(e)}")


class CategoryMoveDialog(QDialog):
    """Диалог перемещения или копирования слов между категориями"""
    
    def __init__(self, parent, word_repository, selected_words):
        super().__init__(parent)
        self.word_repository = word_repository
        self.selected_words = selected_words
        self.operation_type = None  # 'copy' или 'move'
        
        self.setWindowTitle("Копирование/перемещение слов в категории")
        self.setModal(True)
        self.resize(400, 500)
        self._create_ui()
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Информационная надпись
        info_label = QLabel("Отметьте категории для выбранных слов:")
        layout.addWidget(info_label)
        
        # Список выбранных слов
        selected_group = QGroupBox("Выбранные слова")
        selected_layout = QVBoxLayout(selected_group)
        
        selected_list = QListWidget()
        for word_data in self.selected_words:
            # Показываем слово и его текущие категории
            current_categories = ", ".join(word_data.categories)
            selected_list.addItem(f"{word_data.word} ({current_categories})")
        selected_layout.addWidget(selected_list)
        
        layout.addWidget(selected_group)
        
        # Список категорий с чекбоксами
        categories_group = QGroupBox("Категории назначения")
        categories_layout = QVBoxLayout(categories_group)
        
        self.categories_list = QListWidget()
        
        for category in self.word_repository.app_data.categories:
            item = QListWidgetItem(category)
            item.setCheckState(Qt.Unchecked)
            self.categories_list.addItem(item)
        
        categories_layout.addWidget(self.categories_list)
        
        # Кнопки выбора всех/очистки
        selection_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Выбрать все")
        select_all_btn.clicked.connect(self._select_all_categories)
        selection_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("Очистить")
        clear_all_btn.clicked.connect(self._clear_all_categories)
        selection_layout.addWidget(clear_all_btn)
        
        categories_layout.addLayout(selection_layout)
        layout.addWidget(categories_group)
        
        # Кнопки операций
        button_layout = QHBoxLayout()
        
        # Кнопка "Копировать"
        copy_btn = QPushButton("Копировать")
        copy_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        copy_btn.clicked.connect(lambda: self._process_words('copy'))
        button_layout.addWidget(copy_btn)
        
        # Кнопка "Переместить"
        move_btn = QPushButton("Переместить")
        move_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        move_btn.clicked.connect(lambda: self._process_words('move'))
        button_layout.addWidget(move_btn)
        
        # Кнопка "Отмена"
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _select_all_categories(self):
        """Выбирает все категории"""
        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            item.setCheckState(Qt.Checked)
    
    def _clear_all_categories(self):
        """Очищает все выборы категорий"""
        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def _process_words(self, operation):
        """Обрабатывает выбранные слова в зависимости от операции"""
        selected_categories = []
        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_categories.append(item.text())
        
        if not selected_categories:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну категорию!")
            return
        
        # Сохраняем тип операции
        self.operation_type = operation
        
        # Обрабатываем слова в зависимости от операции
        if operation == 'copy':
            self._copy_words(selected_categories)
        else:  # move
            self._move_words(selected_categories)
        
        self.accept()
    
    def _copy_words(self, selected_categories):
        """Копирует слова в выбранные категории (добавляет категории)"""
        for word_data in self.selected_words:
            # Добавляем новые категории к существующим
            for category in selected_categories:
                if category not in word_data.categories:
                    word_data.categories.append(category)
        
        # Сохраняем изменения
        self.word_repository.save_data()
        
        # Показываем сообщение о результате
        QMessageBox.information(
            self, 
            "Копирование завершено", 
            f"Слова скопированы в {len(selected_categories)} категорий:\n" +
            f"{', '.join(selected_categories)}"
        )
    
    def _move_words(self, selected_categories):
        """Перемещает слова в выбранные категории (заменяет категории)"""
        for word_data in self.selected_words:
            # Заменяем все категории на выбранные
            word_data.categories = selected_categories.copy()
        
        # Сохраняем изменения
        self.word_repository.save_data()
        
        # Показываем сообщение о результате
        QMessageBox.information(
            self, 
            "Перемещение завершено", 
            f"Слова перемещены в {len(selected_categories)} категорий:\n" +
            f"{', '.join(selected_categories)}"
        )
    
    def get_operation_type(self):
        """Возвращает тип выполненной операции"""
        return self.operation_type


class WordEditorDialog(QDialog):
    """Диалог редактирования слова"""
    
    def __init__(self, parent, word_repository, media_manager, index=None):
        super().__init__(parent)
        self.word_repository = word_repository
        self.media_manager = media_manager
        self.index = index
        
        # Получаем данные слова или создаём новые
        if index is not None:
            self.word_data = word_repository.app_data.words[index]
            self.setWindowTitle("Редактировать слово")
        else:
            self.word_data = None
            self.setWindowTitle("Добавить слово")
        
        self.setModal(True)
        self.resize(300, 350)
        self._create_ui()
        
        if self.word_data:
            self._load_word_data()

    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Слово
        word_layout = QHBoxLayout()
        word_layout.addWidget(QLabel("Слово:"))
        self.word_edit = QLineEdit()
        # Убираем прямую связь с предпросмотром
        word_layout.addWidget(self.word_edit)
        layout.addLayout(word_layout)

        # Предпросмотр позиций (изначально скрыт)
        self.preview_layout = QHBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("color: gray; font-size: 10px;")
        self.preview_layout.addWidget(self.preview_label)
        self.preview_layout.addStretch()
        layout.addLayout(self.preview_layout)
        self.preview_label.hide()  # Скрываем предпросмотр по умолчанию
        
        # Категория
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Категория:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.word_repository.app_data.categories)
        self.category_combo.setEditable(True)
        category_layout.addWidget(self.category_combo)
        
        # Кнопка создания категории
        category_buttons_layout = QHBoxLayout()
        
        create_category_btn = QPushButton("Создать категорию")
        create_category_btn.clicked.connect(self._create_category)
        category_buttons_layout.addWidget(create_category_btn)
        
        category_layout.addLayout(category_buttons_layout)
        layout.addLayout(category_layout)
        
        # Аудио
        audio_layout = QHBoxLayout()
        audio_layout.addWidget(QLabel("Аудио файл:"))
        self.audio_edit = QLineEdit()
        self.audio_edit.setReadOnly(True)
        audio_layout.addWidget(self.audio_edit)
        
        audio_browse_btn = QPushButton("Обзор")
        audio_browse_btn.clicked.connect(self._browse_audio)
        audio_layout.addWidget(audio_browse_btn)
        
        layout.addLayout(audio_layout)
        
        # Настройка: Чувствительность к регистру
        case_sensitive_layout = QHBoxLayout()
        self.case_sensitive_checkbox = QCheckBox("Учитывать заглавные буквы")
        #self.case_sensitive_checkbox.setToolTip("Если включено, заглавные буквы будут учитываться при проверке этого слова")
        self.case_sensitive_checkbox.toggled.connect(self._on_case_sensitive_changed)
        case_sensitive_layout.addWidget(self.case_sensitive_checkbox)
        case_sensitive_layout.addStretch()
        layout.addLayout(case_sensitive_layout)
        
        # Поле: Позиции важных букв
        important_positions_layout = QHBoxLayout()
        important_positions_layout.addWidget(QLabel("Позиции:"))
        self.important_positions_edit = QLineEdit()
        self.important_positions_edit.setPlaceholderText("Пример: 3 или 1,6")
        #self.important_positions_edit.setToolTip("Укажите позиции букв, которые должны быть заглавными. Например: для 'С Днём рождения' укажите '3'")
        self.important_positions_edit.setEnabled(False)
        self.important_positions_edit.textChanged.connect(self._update_position_preview)
        important_positions_layout.addWidget(self.important_positions_edit)
        
        info_btn = QPushButton("?")
        info_btn.setFixedSize(25, 25)
        #info_btn.setToolTip("Укажите позиции букв, которые должны быть заглавными.\nНапример: для 'С Днём рождения' укажите '3' (буква 'Д')\nПозиции считаются с 1, пробелы учитываются")
        info_btn.clicked.connect(self._show_important_positions_info)
        important_positions_layout.addWidget(info_btn)
        
        layout.addLayout(important_positions_layout)
        
        # Изображения
        images_group = QGroupBox("Изображения")
        images_layout = QVBoxLayout(images_group)
        
        # Создаем горизонтальный слой для списка изображений и превью
        main_images_layout = QHBoxLayout()
        
        # Список изображений
        self.images_list = QListWidget()
        main_images_layout.addWidget(self.images_list)
        
        # Область для превью изображения
        preview_group = QGroupBox("Превью")
        preview_layout = QVBoxLayout(preview_group)
        
        self.image_preview_label = QLabel()
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setMinimumSize(150, 150)
        self.image_preview_label.setMaximumSize(150, 150)
        self.image_preview_label.setStyleSheet("border: 1px solid gray;")
        self.image_preview_label.setText("Выберите\nизображение")
        preview_layout.addWidget(self.image_preview_label)
        
        main_images_layout.addWidget(preview_group)
        
        images_layout.addLayout(main_images_layout)
        
        images_btn_layout = QHBoxLayout()
        
        add_image_btn = QPushButton("Добавить")
        add_image_btn.clicked.connect(self._add_image)
        images_btn_layout.addWidget(add_image_btn)
        
        remove_image_btn = QPushButton("Удалить")
        remove_image_btn.clicked.connect(self._remove_image)
        images_btn_layout.addWidget(remove_image_btn)
        
        images_layout.addLayout(images_btn_layout)
        
        # Подключаем обработчик выбора изображения для обновления превью
        self.images_list.currentItemChanged.connect(self._update_image_preview)
        
        layout.addWidget(images_group)
        
        # Кнопки сохранения/отмены
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save_word)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)

    def _update_position_preview(self):
        """Обновляет предпросмотр позиций букв"""
        word = self.word_edit.text().strip()
        positions_text = self.important_positions_edit.text().strip()
        
        if not word:
            self.preview_label.setText("")
            return
        
        # Создаем предпросмотр с номерами позиций
        preview_parts = []
        for i, char in enumerate(word, 1):
            preview_parts.append(f"{i}:{char}")
        
        preview_text = " | ".join(preview_parts)
        
        # Показываем какие позиции будут подсвечены
        if positions_text:
            try:
                positions = [int(pos.strip()) for pos in positions_text.split(',') if pos.strip()]
                highlighted_positions = [pos for pos in positions if 1 <= pos <= len(word)]
                
                if highlighted_positions:
                    preview_text += f" → Подсветка: {', '.join(map(str, highlighted_positions))}"
                else:
                    preview_text += " → Нет valid позиций для подсветки"
            except ValueError:
                preview_text += " → Ошибка в формате позиций"
        
        self.preview_label.setText(preview_text)

    def _on_case_sensitive_changed(self, is_checked):
        """Включает/выключает поле позиций и предпросмотр в зависимости от чекбокса"""
        self.important_positions_edit.setEnabled(is_checked)
        
        # Показываем/скрываем предпросмотр в зависимости от чекбокса
        if is_checked:
            self.preview_label.show()
            # Подключаем обновление предпросмотра при изменении текста
            self.word_edit.textChanged.connect(self._update_position_preview)
            self.important_positions_edit.textChanged.connect(self._update_position_preview)
            self._update_position_preview()  # Обновляем сразу
        else:
            self.preview_label.hide()
            # Отключаем обновление предпросмотра
            self.word_edit.textChanged.disconnect(self._update_position_preview)
            self.important_positions_edit.textChanged.disconnect(self._update_position_preview)

    def _show_important_positions_info(self):
        """Показывает информацию о поле позиций"""
        QMessageBox.information(
            self,
            "О позициях заглавных букв",
            "• Позиции считаются с 1\n"
            "• Пробелы учитываются как символы\n"
            "• Указывайте позиции через запятую\n\n"
            "Примеры:\n"
            "• 'С Днём рождения' → позиция 3 (буква 'Д')\n"
            "• 'День Победы' → позиции 1,6 (буквы 'Д', 'П')\n"
            "• 'Москва' → позиция 1, можно не указывать\n\n"
            "Если оставить пустым - будут подсвечиваться ВСЕ заглавные буквы."
        )

    def _load_word_data(self):
        """Загружает данные слова в форму"""
        if self.word_data:
            self.word_edit.setText(self.word_data.word)
            
            # Загружаем категории (используем первую категорию если есть)
            if self.word_data.categories and len(self.word_data.categories) > 0:
                self.category_combo.setCurrentText(self.word_data.categories[0])
            
            self.audio_edit.setText(self.word_data.audio)
            self.images_list.addItems(self.word_data.images)
            self.case_sensitive_checkbox.setChecked(self.word_data.case_sensitive)
            self.important_positions_edit.setText(self.word_data.important_positions)
            self.important_positions_edit.setEnabled(self.word_data.case_sensitive)
            
            # Обновляем превью первого изображения, если есть изображения
            if self.word_data.images and len(self.word_data.images) > 0:
                self.images_list.setCurrentRow(0)
                self._update_image_preview(self.images_list.item(0), None)
        # Обновляем предпросмотр только если включена чувствительность к регистру
        if self.word_data.case_sensitive:
            self._update_position_preview()

    def _create_category(self):
        """Создает новую категорию"""
        new_category, ok = QInputDialog.getText(self, "Новая категория", 
                                              "Введите название новой категории:")
        if ok and new_category:
            if new_category in self.word_repository.app_data.categories:
                QMessageBox.warning(self, "Ошибка", f"Категория '{new_category}' уже существует!")
                return
            
            self.word_repository.add_category(new_category)
            self.category_combo.clear()
            self.category_combo.addItems(self.word_repository.app_data.categories)
            self.category_combo.setCurrentText(new_category)
            self.word_repository.save_data()
            QMessageBox.information(self, "Успех", f"Категория '{new_category}' создана!")

    def _browse_audio(self):
        """Выбирает аудио файл"""
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите аудио файл", "",
                                                "Audio files (*.mp3 *.wav *.ogg)")
        if filename:
            word_text = self.word_edit.text().strip()
            new_filename = self.media_manager.save_audio_file(filename, word_text)
            
            # Если был старый аудиофайл, удаляем его если он не используется в других словах
            old_audio = self.audio_edit.text().strip()
            if old_audio and old_audio != new_filename:
                audio_used_elsewhere = False
                for word_data in self.word_repository.app_data.words:
                    if word_data != self.word_data and word_data.audio == old_audio:
                        audio_used_elsewhere = True
                        break
                
                if not audio_used_elsewhere:
                    old_audio_path = os.path.join(self.media_manager.audio_folder, old_audio)
                    self.media_manager._safe_delete(old_audio_path)
            
            self.audio_edit.setText(new_filename)

    def _update_image_preview(self, current, previous):
        """Обновляет превью выбранного изображения"""
        if current:
            image_name = current.text()
            image_path = os.path.join(self.media_manager.images_folder, image_name)
            
            if os.path.exists(image_path):
                from PySide6.QtGui import QPixmap
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Масштабируем изображение, чтобы оно помещалось в область превью
                    scaled_pixmap = pixmap.scaled(
                        self.image_preview_label.width() - 10,
                        self.image_preview_label.height() - 10,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_preview_label.setPixmap(scaled_pixmap)
                    self.image_preview_label.setAlignment(Qt.AlignCenter)
                else:
                    self.image_preview_label.setText("Ошибка\nзагрузки")
            else:
                self.image_preview_label.setText("Файл не\nнайден")
        else:
            self.image_preview_label.setText("Выберите\nизображение")

    def _add_image(self):
        """Добавляет изображение"""
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "",
                                                "Image files (*.jpg *.jpeg *.png *.gif *.bmp)")
        if filename:
            word_text = self.word_edit.text().strip()
            existing_images = self.word_data.images if self.word_data else []
            new_filename = self.media_manager.save_image_file(filename, word_text, existing_images)
            self.images_list.addItem(new_filename)
            # Обновляем превью, если это первый элемент
            if self.images_list.count() == 1:
                self._update_image_preview(self.images_list.item(0), None)

    def _remove_image(self):
        """Удаляет выбранное изображение"""
        current_row = self.images_list.currentRow()
        if current_row >= 0:
            image_name = self.images_list.item(current_row).text()
            
            # Проверяем, используется ли изображение в других словах
            image_used_elsewhere = False
            for word_data in self.word_repository.app_data.words:
                if word_data != self.word_data and image_name in word_data.images:
                    image_used_elsewhere = True
                    break
            
            # Удаляем файл изображения только если он не используется в других словах
            if not image_used_elsewhere:
                self.media_manager._safe_delete(
                    os.path.join(self.media_manager.images_folder, image_name)
                )
            
            # Удаляем из списка
            self.images_list.takeItem(current_row)
            
            # Обновляем превью - показываем следующее изображение или очищаем превью
            if self.images_list.count() > 0:
                new_row = min(current_row, self.images_list.count() - 1)
                self.images_list.setCurrentRow(new_row)
                self._update_image_preview(self.images_list.item(new_row), None)
            else:
                self.image_preview_label.setText("Выберите\nизображение")

    def _save_word(self):
        """Сохраняет слово с проверкой дубликатов"""
        if not self.word_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введи слово!")
            return
            
        word_text = self.word_edit.text().strip()
        
        # Проверяем корректность позиций
        positions_text = self.important_positions_edit.text().strip()
        if positions_text and self.case_sensitive_checkbox.isChecked():
            try:
                positions = [int(pos.strip()) for pos in positions_text.split(',') if pos.strip()]
                word_length = len(word_text)
                invalid_positions = [pos for pos in positions if pos < 1 or pos > word_length]
                
                if invalid_positions:
                    QMessageBox.warning(
                        self, 
                        "Ошибка", 
                        f"Некорректные позиции: {invalid_positions}\n"
                        f"Длина слова: {word_length}\n"
                        f"Допустимые позиции: 1-{word_length}"
                    )
                    return
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Некорректный формат позиций!\nИспользуйте числа через запятую, например: 1,3,5")
                return
        
        # ПРОВЕРКА ДУБЛИКАТОВ
        existing_uid = None
        if self.word_data:
            existing_uid = self.word_data.uid
            
        duplicates = self.word_repository.find_duplicate_words(word_text, exclude_uid=existing_uid)
        
        if duplicates:
            # Проверяем, есть ли дубликаты в той же категории
            current_category = self.category_combo.currentText()
            same_category_duplicates = [dup for dup in duplicates if current_category in dup.categories]
            
            if same_category_duplicates:
                # Формируем сообщение о дубликатах в той же категории
                duplicate_info = []
                for dup in same_category_duplicates:
                    categories = ", ".join(dup.categories) if dup.categories else "без категории"
                    case_info = " (учет регистра)" if dup.case_sensitive else ""
                    duplicate_info.append(f"• '{dup.word}'{case_info} - категории: {categories}")
                
                duplicate_message = "\n".join(duplicate_info)
                
                reply = QMessageBox.question(
                    self,
                    "Слово уже существует в этой категории",
                    f"Слово '{word_text}' уже существует в категории '{current_category}':\n\n{duplicate_message}\n\n"
                    f"Всё равно создать новое слово?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
        
        # Создаем объект слова
        word_data = WordData(
            word=word_text,
            categories=[self.category_combo.currentText()],
            audio=self.audio_edit.text().strip(),
            images=[self.images_list.item(i).text() for i in range(self.images_list.count())],
            case_sensitive=self.case_sensitive_checkbox.isChecked(),
            important_positions=positions_text
        )
        
        # Сохраняем uid при редактировании
        if self.word_data:
            word_data.uid = self.word_data.uid
        
        # Добавляем новую категорию если нужно
        current_category = self.category_combo.currentText()
        if current_category and current_category not in self.word_repository.app_data.categories:
            self.word_repository.add_category(current_category)
        
        # Сохраняем слово
        if self.index is not None:
            self.word_repository.update_word(self.index, word_data)
        else:
            self.word_repository.add_word(word_data)
        
        self.word_repository.save_data()
        self.accept()


__all__ = ['WordManagerDialog', 'WordEditorDialog', 'CategoryMoveDialog']