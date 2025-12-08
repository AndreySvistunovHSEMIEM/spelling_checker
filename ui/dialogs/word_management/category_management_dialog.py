"""Диалог управления категориями"""
import logging
from typing import Optional

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QListWidget, QInputDialog, QMessageBox)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class CategoryManagementDialog(QDialog):
    def __init__(self, parent, word_repository):
        super().__init__(parent)
        self.word_repository = word_repository
        
        self.setWindowTitle("Управление категориями")
        self.setModal(True)
        self.resize(250, 300)
        
        self._create_ui()
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Список категорий:")
        layout.addWidget(title_label)
        
        # Список категорий
        self.categories_list = QListWidget()
        self.categories_list.setSelectionMode(QListWidget.SingleSelection)
        self._refresh_categories_list()
        layout.addWidget(self.categories_list)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        # Кнопка создания категории
        create_btn = QPushButton("➕")
        create_btn.setToolTip("Создать категорию")
        create_btn.clicked.connect(self._create_category)
        create_btn.setFixedSize(30, 24)  # Стандартная высота кнопок
        button_layout.addWidget(create_btn)
        
        # Кнопка переименования категории
        rename_btn = QPushButton("✏️")
        rename_btn.setToolTip("Переименовать категорию")
        rename_btn.clicked.connect(self._rename_category)
        rename_btn.setFixedSize(30, 24)  # Стандартная высота кнопок
        button_layout.addWidget(rename_btn)
        
        # Кнопка удаления категории
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("Удалить категорию")
        delete_btn.clicked.connect(self._delete_category)
        delete_btn.setFixedSize(30, 24)  # Стандартная высота кнопок
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _refresh_categories_list(self):
        """Обновляет список категорий"""
        self.categories_list.clear()
        self.categories_list.addItems(self.word_repository.app_data.categories)
    
    def _create_category(self):
        """Создает новую категорию"""
        new_category, ok = QInputDialog.getText(self, "Новая категория", 
                                              "Введите название новой категории:")
        if ok and new_category:
            new_category = new_category.strip()
            if not new_category:
                QMessageBox.warning(self, "Ошибка", "Название категории не может быть пустым!")
                return
                
            if new_category in self.word_repository.app_data.categories:
                QMessageBox.warning(self, "Ошибка", f"Категория '{new_category}' уже существует!")
                return
            
            self.word_repository.add_category(new_category)
            self.word_repository.save_data()
            self._refresh_categories_list()
            QMessageBox.information(self, "Успех", f"Категория '{new_category}' создана!")
    
    def _rename_category(self):
        """Переименовывает выбранную категорию"""
        current_item = self.categories_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию для переименования!")
            return
        
        old_category = current_item.text()
        new_category, ok = QInputDialog.getText(self, "Переименовать категорию", 
                                              f"Введите новое название для '{old_category}':",
                                              text=old_category)
        if ok and new_category:
            new_category = new_category.strip()
            if not new_category:
                QMessageBox.warning(self, "Ошибка", "Название категории не может быть пустым!")
                return
                
            if new_category == old_category:
                return  # Нет изменений
            
            if new_category in self.word_repository.app_data.categories:
                QMessageBox.warning(self, "Ошибка", f"Категория '{new_category}' уже существует!")
                return
            
            # Переименовываем категорию во всех словах
            updated_count = 0
            for word_data in self.word_repository.app_data.words:
                if old_category in word_data.categories:
                    word_data.categories.remove(old_category)
                    word_data.categories.append(new_category)
                    updated_count += 1
            
            # Обновляем список категорий
            self.word_repository.app_data.categories.remove(old_category)
            self.word_repository.app_data.categories.append(new_category)
            self.word_repository.app_data.categories.sort()
            
            # Обновляем статистику, если нужно
            training_state = self.word_repository.app_data.training_state
            if old_category in training_state.mistakes_count:
                training_state.mistakes_count[new_category] = training_state.mistakes_count.pop(old_category)
            if old_category in training_state.wrong_answers:
                training_state.wrong_answers[new_category] = training_state.wrong_answers.pop(old_category)
            if old_category in training_state.correct_answers_count:
                training_state.correct_answers_count[new_category] = training_state.correct_answers_count.pop(old_category)
            if old_category in training_state.incorrect_answers_count:
                training_state.incorrect_answers_count[new_category] = training_state.incorrect_answers_count.pop(old_category)
            if old_category in training_state.used_words_by_category:
                training_state.used_words_by_category[new_category] = training_state.used_words_by_category.pop(old_category)
            
            # Если это была текущая категория, обновляем её
            if training_state.current_category == old_category:
                training_state.current_category = new_category
            
            self.word_repository.save_data()
            self._refresh_categories_list()
            QMessageBox.information(self, "Успех", 
                                  f"Категория '{old_category}' переименована в '{new_category}'.\n"
                                  f"Обновлено слов: {updated_count}")
    
    def _delete_category(self):
        """Удаляет выбранную категорию"""
        current_item = self.categories_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию для удаления!")
            return
        
        category = current_item.text()
        
        # Используем ту же логику, что и в WordEditorDialog
        stats = self.word_repository.get_category_stats(category)
        
        if stats['words_with_single_category'] > 0:
            message = (
                f"Невозможно удалить категорию '{category}'.\n\n"
                f"Эта категория является единственной для {stats['words_with_single_category']} слов.\n\n"
                f"Всего слов в категории: {stats['total_words']}\n"
                f"Слов с единственной категорией: {stats['words_with_single_category']}\n"
                f"Слов с несколькими категориями: {stats['words_with_multiple_categories']}"
            )
            QMessageBox.warning(self, "Невозможно удалить категорию", message)
            return
        
        if stats['total_words'] > 0:
            message = (
                f"Удалить категорию '{category}'?\n\n"
                f"Эта категория будет удалена из {stats['total_words']} слов.\n"
                f"Все эти слова имеют другие категории."
            )
            reply = QMessageBox.question(self, "Подтверждение удаления", message)
            if reply != QMessageBox.Yes:
                return
        else:
            reply = QMessageBox.question(self, "Подтверждение", 
                                       f"Удалить пустую категорию '{category}'?")
            if reply != QMessageBox.Yes:
                return
        
        result = self.word_repository.delete_category(category)
        
        if result['success']:
            self._refresh_categories_list()
            QMessageBox.information(self, "Успех", result['message'])
        else:
            QMessageBox.warning(self, "Ошибка", result['message'])