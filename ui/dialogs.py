"""Диалоговые окна приложения"""
import json
import logging
import os
import re
import shutil
from typing import Dict, Any

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                              QLineEdit, QComboBox, QListWidget, QTreeWidget, QTreeWidgetItem,
                              QGroupBox, QFileDialog, QInputDialog, QMessageBox, QGridLayout, QCheckBox, QListWidgetItem, QFormLayout)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

from core.constants import Constants
from core.models import WordData
from utils.helpers import create_dialog, show_silent_message

logger = logging.getLogger(__name__)

class ChangePasswordDialog(QDialog):
    """Диалог смены пароля"""
    
    def __init__(self, parent, current_password):
        super().__init__(parent)
        self.current_password = current_password
        self.new_password = None
        
        self.setWindowTitle("Смена пароля")
        self.setModal(True)
        self.resize(*Constants.CHANGE_PASSWORD_DIALOG_SIZE)
        self._create_ui()
        
        # Устанавливаем иконку окна
        change_password_icon_path = os.path.join(parent.base_dir, Constants.CHANGE_PASSWORD_ICON)
        if os.path.exists(change_password_icon_path):
            self.setWindowIcon(QIcon(change_password_icon_path))
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Форма ввода паролей
        form_layout = QFormLayout()
        
        # Старый пароль
        self.old_password_edit = QLineEdit()
        self.old_password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Старый пароль:", self.old_password_edit)
        
        # Новый пароль
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Новый пароль:", self.new_password_edit)
        
        # Подтверждение нового пароля
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Подтверждение:", self.confirm_password_edit)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("ОК")
        ok_btn.clicked.connect(self._change_password)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _change_password(self):
        """Смена пароля"""
        old_password = self.old_password_edit.text().strip()
        new_password = self.new_password_edit.text().strip()
        confirm_password = self.confirm_password_edit.text().strip()
        
        # Проверки
        if not old_password:
            QMessageBox.warning(self, "Ошибка", "Введите старый пароль!")
            return
            
        if old_password != self.current_password:
            QMessageBox.warning(self, "Ошибка", "Старый пароль введён неверно!")
            return
            
        if not new_password:
            QMessageBox.warning(self, "Ошибка", "Введите новый пароль!")
            return
            
        if new_password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Новые пароли не совпадают!")
            return
            
        if new_password == self.current_password:
            QMessageBox.warning(self, "Ошибка", "Новый пароль должен отличаться от старого!")
            return
        
        # Сохраняем новый пароль
        self.new_password = new_password
        self.accept()
    
    def get_new_password(self):
        """Возвращает новый пароль"""
        return self.new_password


class SettingsDialog(QDialog):
    """Диалог настроек"""
    
    def __init__(self, parent, cost_per_word, penalty_per_word, show_correct_answer, 
                 auto_play_enabled, auto_play_delay, require_password_for_settings,
                 repeat_mistakes, repeat_mistakes_range, infinite_mode):
        super().__init__(parent)
        self.cost_per_word = cost_per_word
        self.penalty_per_word = penalty_per_word
        self.show_correct_answer = show_correct_answer
        self.auto_play_enabled = auto_play_enabled
        self.auto_play_delay = auto_play_delay
        self.require_password_for_settings = require_password_for_settings
        self.repeat_mistakes = repeat_mistakes
        self.repeat_mistakes_range = repeat_mistakes_range
        self.infinite_mode = infinite_mode
        
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self._create_ui()
        
        # Устанавливаем иконку окна
        settings_icon_path = os.path.join(parent.base_dir, Constants.SETTINGS_ICON)
        if os.path.exists(settings_icon_path):
            self.setWindowIcon(QIcon(settings_icon_path))
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Форма настроек
        form_layout = QGridLayout()
        
        row = 0
        
        # Награда за слово
        form_layout.addWidget(QLabel("Награда за слово (руб):"), row, 0)
        self.reward_edit = QLineEdit(str(self.cost_per_word))
        form_layout.addWidget(self.reward_edit, row, 1)
        row += 1
        
        # Штраф за ошибку
        form_layout.addWidget(QLabel("Штраф за ошибку (руб):"), row, 0)
        self.penalty_edit = QLineEdit(str(self.penalty_per_word))
        form_layout.addWidget(self.penalty_edit, row, 1)
        row += 1
        
        # Показ правильного ответа
        form_layout.addWidget(QLabel("Показ правильного ответа при ошибке:"), row, 0)
        self.show_correct_checkbox = QCheckBox()
        self.show_correct_checkbox.setChecked(self.show_correct_answer)
        form_layout.addWidget(self.show_correct_checkbox, row, 1)
        row += 1
        
        # ДОБАВЛЯЕМ НОВЫЕ НАСТРОЙКИ НИЖЕ ↓
        
        # Требовать пароль для настроек
        form_layout.addWidget(QLabel("Требовать пароль для входа в настройки:"), row, 0)
        self.require_password_checkbox = QCheckBox()
        self.require_password_checkbox.setChecked(self.require_password_for_settings)
        self.require_password_checkbox.toggled.connect(self._on_require_password_toggled)  # ДОБАВИЛИ ОБРАБОТЧИК
        form_layout.addWidget(self.require_password_checkbox, row, 1)
        row += 1
        
        # Повторять ошибки
        form_layout.addWidget(QLabel("Повторять слова с ошибками:"), row, 0)
        self.repeat_mistakes_checkbox = QCheckBox()
        self.repeat_mistakes_checkbox.setChecked(self.repeat_mistakes)
        self.repeat_mistakes_checkbox.toggled.connect(self._on_repeat_mistakes_toggled)
        form_layout.addWidget(self.repeat_mistakes_checkbox, row, 1)
        row += 1
        
        # Диапазон повторения ошибок
        form_layout.addWidget(QLabel("Диапазон повторения (через N слов):"), row, 0)
        self.repeat_range_edit = QLineEdit(self.repeat_mistakes_range)
        self.repeat_range_edit.setPlaceholderText("7-10")
        self.repeat_range_edit.setEnabled(self.repeat_mistakes)  # Включаем только если флаг активен
        form_layout.addWidget(self.repeat_range_edit, row, 1)
        row += 1
        
        # Бесконечный режим
        form_layout.addWidget(QLabel("Бесконечный режим тренировки:"), row, 0)
        self.infinite_mode_checkbox = QCheckBox()
        self.infinite_mode_checkbox.setChecked(self.infinite_mode)
        form_layout.addWidget(self.infinite_mode_checkbox, row, 1)
        row += 1
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _save_settings(self):
        """Сохранение настроек"""
        try:
            cost = float(self.reward_edit.text())
            penalty = float(self.penalty_edit.text())
            
            # Валидация значений
            if cost < 0:
                QMessageBox.warning(self, "Ошибка", "Награда не может быть отрицательной!")
                return
            if penalty < 0:
                QMessageBox.warning(self, "Ошибка", "Штраф не может быть отрицательным!")
                return
            
            # ВАЛИДАЦИЯ ДИАПАЗОНА ПОВТОРЕНИЯ ↓
            repeat_range = self.repeat_range_edit.text().strip()
            if self.repeat_mistakes_checkbox.isChecked() and repeat_range:
                try:
                    min_val, max_val = map(int, repeat_range.split('-'))
                    if min_val < 1 or max_val < min_val:
                        QMessageBox.warning(self, "Ошибка", "Диапазон повторения должен быть в формате 'min-max' где min ≤ max")
                        return
                except (ValueError, AttributeError):
                    QMessageBox.warning(self, "Ошибка", "Диапазон повторения должен быть в формате 'min-max' (например: 7-10)")
                    return
            
            self.cost_per_word = cost
            self.penalty_per_word = penalty
            self.show_correct_answer = self.show_correct_checkbox.isChecked()
            # Автовоспроизведение оставляем включенным по умолчанию
            self.auto_play_enabled = True
            self.auto_play_delay = 500  # стандартная задержка
            
            # СОХРАНЯЕМ НОВЫЕ НАСТРОЙКИ ↓
            self.require_password_for_settings = self.require_password_checkbox.isChecked()
            self.repeat_mistakes = self.repeat_mistakes_checkbox.isChecked()
            self.repeat_mistakes_range = repeat_range if self.repeat_mistakes else "7-10"
            self.infinite_mode = self.infinite_mode_checkbox.isChecked()
            
            self.accept()
        except ValueError as e:
            logger.warning("Ошибка валидации настроек: %s", e)
            QMessageBox.critical(self, "Ошибка", "Введите корректные числа!")
    
    def get_cost_per_word(self):
        """Возвращает награду за слово"""
        return self.cost_per_word
    
    def get_penalty_per_word(self):
        """Возвращает штраф за ошибку"""
        return self.penalty_per_word
    
    def get_show_correct_answer(self):
        """Возвращает настройку показа правильного ответа"""
        return self.show_correct_answer
        
    def get_auto_play_enabled(self):
        """Возвращает настройку автовоспроизведения"""
        return self.auto_play_enabled

    def get_auto_play_delay(self):
        """Возвращает задержку автовоспроизведения"""
        return self.auto_play_delay
        
    def _on_repeat_mistakes_toggled(self, is_checked):
        """Включает/выключает поле диапазона повторения"""
        self.repeat_range_edit.setEnabled(is_checked)
        
    def get_require_password_for_settings(self):
        """Возвращает настройку требования пароля"""
        return self.require_password_for_settings

    def get_repeat_mistakes(self):
        """Возвращает настройку повторения ошибок"""
        return self.repeat_mistakes

    def get_repeat_mistakes_range(self):
        """Возвращает диапазон повторения ошибок"""
        return self.repeat_mistakes_range

    def get_infinite_mode(self):
        """Возвращает настройку бесконечного режима"""
        return self.infinite_mode
        
    def _on_require_password_toggled(self, is_checked):
        """Обрабатывает снятие флажка требования пароля"""
        if not is_checked:
            # Если флажок снимают - запрашиваем пароль
            password, ok = QInputDialog.getText(
                self, 
                "Подтверждение пароля",
                "Введите текущий пароль:",
                QLineEdit.Password
            )
            
            if ok:
                # Проверяем пароль
                current_password = self.parent().word_repository.app_data.settings.settings_password
                if password == current_password:
                    # Пароль верный - оставляем флажок снятым
                    self.require_password_checkbox.setChecked(False)
                else:
                    # Пароль неверный - возвращаем флажок
                    self.require_password_checkbox.setChecked(True)
                    QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
            else:
                # Пользователь отменил - возвращаем флажок
                self.require_password_checkbox.setChecked(True)


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
        
        delete_category_btn = QPushButton("🗑️ Категория")
        delete_category_btn.setToolTip("Удалить выбранную категорию")
        delete_category_btn.clicked.connect(self._delete_category)
        filter_layout.addWidget(delete_category_btn)
        
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
        
    def _on_category_filter_changed(self, category_filter):
        """Обработчик изменения фильтра категорий"""
        self.current_category_filter = category_filter
        self._refresh_words_tree()
        
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
            
    def _delete_category(self):
        """Удаляет выбранную категорию"""
        current_category = self.category_filter_combo.currentText()
        if current_category == "Все":
            QMessageBox.warning(self, "Ошибка", "Выберите конкретную категорию для удаления!")
            return
        
        # Используем ту же логику, что и в WordEditorDialog
        stats = self.word_repository.get_category_stats(current_category)
        
        if stats['words_with_single_category'] > 0:
            message = (
                f"Невозможно удалить категорию '{current_category}'.\n\n"
                f"Эта категория является единственной для {stats['words_with_single_category']} слов.\n\n"
                f"Всего слов в категории: {stats['total_words']}\n"
                f"Слов с единственной категорией: {stats['words_with_single_category']}\n"
                f"Слов с несколькими категориями: {stats['words_with_multiple_categories']}"
            )
            QMessageBox.warning(self, "Невозможно удалить категорию", message)
            return
        
        if stats['total_words'] > 0:
            message = (
                f"Удалить категорию '{current_category}'?\n\n"
                f"Эта категория будет удалена из {stats['total_words']} слов.\n"
                f"Все эти слова имеют другие категории."
            )
            reply = QMessageBox.question(self, "Подтверждение удаления", message)
            if reply != QMessageBox.Yes:
                return
        else:
            reply = QMessageBox.question(self, "Подтверждение", 
                                       f"Удалить пустую категорию '{current_category}'?")
            if reply != QMessageBox.Yes:
                return
        
        result = self.word_repository.delete_category(current_category)
        
        if result['success']:
            # Обновляем интерфейс
            self.category_filter_combo.clear()
            self.category_filter_combo.addItem("Все")
            self.category_filter_combo.addItems(self.word_repository.app_data.categories)
            self._refresh_words_tree()
            
            QMessageBox.information(self, "Успех", result['message'])
        else:
            QMessageBox.warning(self, "Ошибка", result['message'])
        
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
                duplicate_word_uid_count = 0  # Слова с одинаковым word и uid (уже существуют)
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
                
                # Словари для отслеживания uid в импортируемых данных (для обнаружения конфликтов)
                import_uid_map = {}  # uid -> список слов
                import_word_map = {}  # word -> список uid
                
                for word_dict in import_words:
                    word_lower = word_dict["word"].lower()
                    uid = word_dict.get("uid", "")
                    
                    if uid not in import_uid_map:
                        import_uid_map[uid] = []
                    import_uid_map[uid].append(word_dict)
                    
                    if word_lower not in import_word_map:
                        import_word_map[word_lower] = []
                    import_word_map[word_lower].append(uid)
                
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
            

# dialogs.py - добавляем новый диалог

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
        
        self.images_list = QListWidget()
        images_layout.addWidget(self.images_list)
        
        images_btn_layout = QHBoxLayout()
        
        add_image_btn = QPushButton("Добавить")
        add_image_btn.clicked.connect(self._add_image)
        images_btn_layout.addWidget(add_image_btn)
        
        remove_image_btn = QPushButton("Удалить")
        remove_image_btn.clicked.connect(self._remove_image)
        images_btn_layout.addWidget(remove_image_btn)
        
        images_layout.addLayout(images_btn_layout)
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

    def _add_image(self):
        """Добавляет изображение"""
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", 
                                                "Image files (*.jpg *.jpeg *.png *.gif *.bmp)")
        if filename:
            word_text = self.word_edit.text().strip()
            existing_images = self.word_data.images if self.word_data else []
            new_filename = self.media_manager.save_image_file(filename, word_text, existing_images)
            self.images_list.addItem(new_filename)

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
            # Формируем сообщение о дубликатах
            duplicate_info = []
            for dup in duplicates:
                categories = ", ".join(dup.categories) if dup.categories else "без категории"
                case_info = " (учет регистра)" if dup.case_sensitive else ""
                duplicate_info.append(f"• '{dup.word}'{case_info} - категории: {categories}")
            
            duplicate_message = "\n".join(duplicate_info)
            
            reply = QMessageBox.question(
                self,
                "Слово уже существует",
                f"Слово '{word_text}' уже существует в базе:\n\n{duplicate_message}\n\n"
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
        

__all__ = ['SettingsDialog', 'ProblemWordsDialog', 'WordManagerDialog', 
           'WordEditorDialog', 'ExportCategoriesDialog', 'BulkImportDialog', 'ChangePasswordDialog']