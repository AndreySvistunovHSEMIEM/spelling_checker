"""Диалоги статистики и аналитики"""
import json
import logging
import os
import re
from typing import Dict, Any

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                              QLineEdit, QComboBox, QListWidget, QTreeWidget, QTreeWidgetItem,
                              QGroupBox, QFileDialog, QInputDialog, QMessageBox, QGridLayout, QCheckBox, QListWidgetItem, QFormLayout)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from core.constants import Constants
from core.models import WordData
from utils.helpers import create_dialog, show_silent_message


logger = logging.getLogger(__name__)


class ProblemWordsDialog(QDialog):
    """Диалог проблемных слов"""
    
    def __init__(self, parent, word_repository):
        super().__init__(parent)
        self.word_repository = word_repository
        self.training_state = word_repository.app_data.training_state
        
        self.setWindowTitle("Проблемные слова")
        self.setModal(True)
        
        # Устанавливаем иконку окна
        mistake_icon_path = os.path.join(parent.base_dir, Constants.MISTAKE_WORD_ICON)
        if os.path.exists(mistake_icon_path):
            self.setWindowIcon(QIcon(mistake_icon_path))
        
        self.resize(*Constants.PROBLEM_WORDS_DIALOG_SIZE)
        
        self._create_ui()
    
    def closeEvent(self, event):
        """Вызывается при закрытии диалога"""
        super().closeEvent(event)
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Получаем проблемные слова
        problem_words = self._get_problem_words()
        
        if not problem_words:
            self._create_empty_state(layout)
            return
        
        # Статистика
        self._create_stats_section(layout, problem_words)
        
        # Список слов
        self._create_words_list(layout, problem_words)
        
        # Кнопки управления
        self._create_buttons(layout, problem_words)
    
    def _get_problem_words(self):
        """Возвращает список проблемных слов для всех категорий"""
        # Получаем ошибки для всех категорий
        all_mistakes = {}
        for category, mistakes in self.training_state.mistakes_count.items():
            for word, count in mistakes.items():
                if count > 0:
                    if word in all_mistakes:
                        all_mistakes[word] += count
                    else:
                        all_mistakes[word] = count
        
        return [(word, count) for word, count in all_mistakes.items()]
    
    def _create_empty_state(self, layout):
        """Создает интерфейс когда нет проблемных слов"""
        # Создаем метку с выравниванием по центру и увеличенным шрифтом
        no_errors_label = QLabel("Ошибок нет!")
        no_errors_label.setAlignment(Qt.AlignCenter)
        no_errors_label.setStyleSheet("font-size: 20px; font-weight: bold; font-family: Arial; color: #666666;")  # Увеличенный шрифт
        
        # Добавляем растяжку сверху
        layout.addStretch()
        
        # Добавляем метку
        layout.addWidget(no_errors_label)
        
        # Добавляем растяжку снизу
        layout.addStretch()
        
        # Кнопка закрытия по центру
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn_layout.addWidget(close_btn)
        
        close_btn_layout.addStretch()
        layout.addLayout(close_btn_layout)
    
    def _create_stats_section(self, layout, problem_words):
        """Создает секцию статистики"""
        stats_group = QGroupBox("Статистика ошибок")
        stats_layout = QVBoxLayout(stats_group)
        
        total_words = len(problem_words)
        total_mistakes = sum(count for _, count in problem_words)
        
        stats_layout.addWidget(QLabel(f"Всего проблемных слов: {total_words}"))
        stats_layout.addWidget(QLabel(f"Всего ошибок: {total_mistakes}"))
        
        # Добавляем информацию о категориях
        categories_with_errors = set()
        for category, mistakes in self.training_state.mistakes_count.items():
            for word, count in mistakes.items():
                if count > 0:
                    categories_with_errors.add(category)
        
        stats_layout.addWidget(QLabel(f"Категории с ошибками: {len(categories_with_errors)}"))
        
        layout.addWidget(stats_group)
    
    def _create_words_list(self, layout, problem_words):
        """Создает список проблемных слов"""
        list_group = QGroupBox("Слова с ошибками")
        list_layout = QVBoxLayout(list_group)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["Слово", "Ошибок", "Неправильные ответы"])
        tree.setColumnWidth(0, 110)
        tree.setColumnWidth(1, 60)
        tree.setColumnWidth(2, 150)
        
        # Объединяем неправильные ответы из всех категорий
        all_wrong_answers = {}
        for word, _ in problem_words:
            for category, category_wrong_answers in self.training_state.wrong_answers.items():
                if word in category_wrong_answers:
                    if word not in all_wrong_answers:
                        all_wrong_answers[word] = []
                    all_wrong_answers[word].extend(category_wrong_answers[word])
        
        for word, count in sorted(problem_words, key=lambda x: x[1], reverse=True):
            # Получаем объединенные неправильные ответы для слова
            wrong_answers = all_wrong_answers.get(word, [])
            
            wrong_answers_text = ", ".join(wrong_answers[:3])
            if len(wrong_answers) > 3:
                wrong_answers_text += f"... (ещё {len(wrong_answers) - 3})"
            
            item = QTreeWidgetItem([word, str(count), wrong_answers_text])
            tree.addTopLevelItem(item)
        
        list_layout.addWidget(tree)
        layout.addWidget(list_group)
    
    def _create_buttons(self, layout, problem_words):
        """Создает кнопки управления"""
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Создать категорию")
        create_btn.clicked.connect(lambda: self._create_problem_category(problem_words))
        button_layout.addWidget(create_btn)
        
        clear_btn = QPushButton("Очистить статистику")
        clear_btn.clicked.connect(self._clear_mistakes)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_problem_category(self, problem_words):
        """Создает категорию из проблемных слов"""
        if not problem_words:
            QMessageBox.warning(self, "Ошибка", "Нет проблемных слов!")
            return
        
        category_name = "Проблемные слова"
        problem_words_list = [word for word, _ in problem_words]
        
        # Проверяем существование категории
        if category_name in self.word_repository.app_data.categories:
            reply = QMessageBox.question(self, "Подтверждение", 
                                       f"Категория '{category_name}' уже существует. Перезаписать?\n\n"
                                       "Это удалит категорию из всех текущих слов и добавит её только к проблемным словам.")
            if reply != QMessageBox.Yes:
                return
            
            # УДАЛЯЕМ КАТЕГОРИЮ ИЗ ВСЕХ СЛОВ, а не удаляем сами слова
            for word_data in self.word_repository.app_data.words:
                # Безопасное удаление: проверяем наличие перед удалением
                if category_name in word_data.categories:
                    word_data.categories.remove(category_name)
        
        # Находим существующие слова и ДОБАВЛЯЕМ к ним категорию
        words_updated = 0
        for word_data in self.word_repository.app_data.words:
            if word_data.word in problem_words_list:
                # ДОБАВЛЯЕМ категорию к существующему слову, если её еще нет
                if category_name not in word_data.categories:
                    word_data.categories.append(category_name)
                    words_updated += 1
        
        if words_updated == 0:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти слова для обновления!")
            return
        
        # Добавляем категорию в общий список, если её нет
        if category_name not in self.word_repository.app_data.categories:
            self.word_repository.add_category(category_name)
        
        # ИСПРАВЛЕНИЕ: Сбрасываем прогресс ТОЛЬКО для новой категории, но более аккуратно
        training_state = self.word_repository.app_data.training_state
        
        # Удаляем использованные слова только из новой категории
        words_to_remove = set()
        for word in training_state.used_words:
            # Проверяем, принадлежит ли слово к новой категории
            for word_data in self.word_repository.app_data.words:
                if word_data.word == word and category_name in word_data.categories:
                    words_to_remove.add(word)
                    break
        training_state.used_words -= words_to_remove
        
        # Очищаем статистику ошибок для новой категории
        if category_name in training_state.mistakes_count:
            del training_state.mistakes_count[category_name]
        if category_name in training_state.wrong_answers:
            del training_state.wrong_answers[category_name]
        if category_name in training_state.correct_answers_count:
            del training_state.correct_answers_count[category_name]
        if category_name in training_state.incorrect_answers_count:
            del training_state.incorrect_answers_count[category_name]
        
        # Очищаем некорректные категории
        self.word_repository.cleanup_invalid_categories()
        
        self.word_repository.save_data()
        self.close()
        
        QMessageBox.information(self.parent(), "Успех", 
                              f"Категория '{category_name}' добавлена к {words_updated} словам!\n\n"
                              f"Прогресс по новой категории автоматически сброшен.")
    
    def _clear_mistakes(self):
        """Очищает статистику ошибок (только mistakes_count и wrong_answers)"""
        reply = QMessageBox.question(self, "Подтверждение", 
                                   "Очистить статистику ошибок?\n\n"
                                   "Это удалит:\n"
                                   "• Количество ошибок для каждого слова\n"
                                   "• Список неправильных ответов")
        if reply == QMessageBox.Yes:
            # Очищаем ТОЛЬКО статистику ошибок, не трогая другие данные
            self.training_state.mistakes_count.clear()
            self.training_state.wrong_answers.clear()
            
            self.word_repository.save_data()
            self.close()
            
            show_silent_message(self.parent(), "Успех", "Статистика ошибок очищена")
           

__all__ = ['ProblemWordsDialog']