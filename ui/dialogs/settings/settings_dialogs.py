"""Диалоги настроек приложения"""
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                              QLineEdit, QComboBox, QGroupBox, QGridLayout, QCheckBox, QFormLayout, QInputDialog, QMessageBox)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from core.constants import Constants
from utils.helpers import show_silent_message


class SettingsDialog(QDialog):
    """Диалог настроек"""
    
    def __init__(self, parent, cost_per_word, penalty_per_word, show_correct_answer,
                 auto_play_enabled, auto_play_delay, require_password_for_settings,
                 repeat_mistakes, repeat_mistakes_range, infinite_mode, reward_type="rubles",
                 points_cost_per_word=1, points_penalty_per_word=1, rubles_cost_per_word=0.5, rubles_penalty_per_word=0.25):
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
        self.reward_type = reward_type
        # Store separate values for points and rubles
        self.points_cost_per_word = points_cost_per_word
        self.points_penalty_per_word = points_penalty_per_word
        self.rubles_cost_per_word = rubles_cost_per_word
        self.rubles_penalty_per_word = rubles_penalty_per_word
        
        # Use the stored separate values directly
        # Update the main cost/penalty values based on current reward type for backward compatibility
        if reward_type == "points":
            self.cost_per_word = self.points_cost_per_word
            self.penalty_per_word = self.points_penalty_per_word
        else:  # rubles
            self.cost_per_word = self.rubles_cost_per_word
            self.penalty_per_word = self.rubles_penalty_per_word
        
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
        
        # Тип награды
        form_layout.addWidget(QLabel("Тип награды:"), row, 0)
        self.reward_type_combo = QComboBox()
        self.reward_type_combo.addItems(["рубли", "баллы"])
        self.reward_type_combo.setCurrentText("рубли" if self.reward_type == "rubles" else "баллы")
        form_layout.addWidget(self.reward_type_combo, row, 1)
        row += 1
        
        # Награда за слово
        reward_unit = "(балл)" if self.reward_type == "points" else "(руб)"
        self.reward_label = QLabel(f"Награда за слово {reward_unit}:")
        form_layout.addWidget(self.reward_label, row, 0)
        if self.reward_type == "points":
            self.reward_edit = QLineEdit(str(self.points_cost_per_word))
        else:
            # Format rubles value to remove unnecessary decimal places if it's an integer
            rubles_value = self.rubles_cost_per_word
            if rubles_value.is_integer():
                self.reward_edit = QLineEdit(str(int(rubles_value)))
            else:
                self.reward_edit = QLineEdit(str(rubles_value))
        form_layout.addWidget(self.reward_edit, row, 1)
        row += 1
        
        # Штраф за ошибку
        self.penalty_label = QLabel(f"Штраф за ошибку {reward_unit}:")
        form_layout.addWidget(self.penalty_label, row, 0)
        if self.reward_type == "points":
            self.penalty_edit = QLineEdit(str(self.points_penalty_per_word))
        else:
            # Format rubles value to remove unnecessary decimal places if it's an integer
            rubles_value = self.rubles_penalty_per_word
            if rubles_value.is_integer():
                self.penalty_edit = QLineEdit(str(int(rubles_value)))
            else:
                self.penalty_edit = QLineEdit(str(rubles_value))
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
        
        # Connect reward type change signal
        self.reward_type_combo.currentTextChanged.connect(self._on_reward_type_changed)
    
    def _save_settings(self):
        """Сохранение настроек"""
        try:
            # Проверяем тип награды и валидируем соответствующим образом
            # Поддерживаем запятую как десятичный разделитель
            reward_text = self.reward_edit.text().replace(',', '.')
            penalty_text = self.penalty_edit.text().replace(',', '.')
            
            if self.reward_type == "points":
                # Для баллов используем целые числа
                cost = int(float(reward_text))  # Двойное преобразование для обработки строк вроде "5.0"
                penalty = int(float(penalty_text))
                # Update the separate points values ONLY
                self.points_cost_per_word = cost
                self.points_penalty_per_word = penalty
                # DO NOT modify rubles values when in points mode
            else:
                # Для рублей используем дробные числа
                cost = float(reward_text)
                penalty = float(penalty_text)
                # Update the separate rubles values ONLY
                self.rubles_cost_per_word = cost
                self.rubles_penalty_per_word = penalty
                # DO NOT modify points values when in rubles mode
            
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
            
            # УБРАНО: Обновление старых полей cost_per_word и penalty_per_word при сохранении
            # Эти поля должны использоваться ТОЛЬКО для миграции старых данных при загрузке
            # При сохранении должны обновляться только points_cost_per_word/points_penalty_per_word и rubles_cost_per_word/rubles_penalty_per_word
                
            self.show_correct_answer = self.show_correct_checkbox.isChecked()
            
            # Автовоспроизведение оставляем включенным по умолчанию
            self.auto_play_enabled = True
            self.auto_play_delay = 500  # стандартная задержка
            
            # СОХРАНЯЕМ НОВЫЕ НАСТРОЙКИ ↓
            self.require_password_for_settings = self.require_password_checkbox.isChecked()
            self.repeat_mistakes = self.repeat_mistakes_checkbox.isChecked()
            self.repeat_mistakes_range = repeat_range if self.repeat_mistakes else "7-10"
            self.infinite_mode = self.infinite_mode_checkbox.isChecked()
            # Тип награды уже обновляется в _on_reward_type_changed, используем текущее значение
            # self.reward_type = "rubles" if self.reward_type_combo.currentText() == "рубли" else "points"
            
            self.accept()
        except ValueError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Ошибка валидации настроек: %s", e)
            QMessageBox.critical(self, "Ошибка", "Введите корректные числа!")
    
    def get_cost_per_word(self):
        """Возвращает награду за слово - обновляем в зависимости от типа награды"""
        if self.reward_type == "points":
            return self.points_cost_per_word
        else:  # rubles
            return self.rubles_cost_per_word
    
    def get_penalty_per_word(self):
        """Возвращает штраф за ошибку - обновляем в зависимости от типа награды"""
        if self.reward_type == "points":
            return self.points_penalty_per_word
        else:  # rubles
            return self.rubles_penalty_per_word
    
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
        
    def get_reward_type(self):
        """Возвращает тип награды"""
        return self.reward_type
        
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
                    
    def _on_reward_type_changed(self, text):
        """Обновляет поля ввода и метки при изменении типа награды"""
        new_reward_type = "points" if text == "баллы" else "rubles"
        
        # Сохраняем текущие значения из полей ввода в соответствующую переменную ДО переключения
        try:
            current_reward = float(self.reward_edit.text().replace(',', '.'))
            current_penalty = float(self.penalty_edit.text().replace(',', '.'))
            
            if self.reward_type == "points":
                self.points_cost_per_word = int(current_reward)
                self.points_penalty_per_word = int(current_penalty)
            else:  # rubles
                self.rubles_cost_per_word = float(current_reward)
                self.rubles_penalty_per_word = float(current_penalty)
        except ValueError:
            # Если не удается преобразовать, пропускаем сохранение
            pass
        
        # Обновляем метки
        reward_unit = "(балл)" if new_reward_type == "points" else "(руб)"
        self.reward_label.setText(f"Награда за слово {reward_unit}:")
        self.penalty_label.setText(f"Штраф за ошибку {reward_unit}:")
        
        # Устанавливаем значения из соответствующих переменных в поля ввода
        if new_reward_type == "points":
            self.reward_edit.setText(str(self.points_cost_per_word))
            self.penalty_edit.setText(str(self.points_penalty_per_word))
        else:  # rubles
            # Проверяем, нужно ли отображать значение с запятой
            rubles_reward_str = str(self.rubles_cost_per_word)
            rubles_penalty_str = str(self.rubles_penalty_per_word)
            
            # Если значения содержат только .0, отображаем как целые числа
            if self.rubles_cost_per_word.is_integer():
                rubles_reward_str = str(int(self.rubles_cost_per_word))
            if self.rubles_penalty_per_word.is_integer():
                rubles_penalty_str = str(int(self.rubles_penalty_per_word))
                
            self.reward_edit.setText(rubles_reward_str)
            self.penalty_edit.setText(rubles_penalty_str)
        
        # Обновляем внутреннюю переменную типа награды
        self.reward_type = new_reward_type


__all__ = ['SettingsDialog']