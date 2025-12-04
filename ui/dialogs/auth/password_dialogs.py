"""Диалоги аутентификации и управления паролем"""
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                              QLineEdit, QFormLayout, QMessageBox, QInputDialog)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from core.constants import Constants
from utils.helpers import show_silent_message


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


__all__ = ['ChangePasswordDialog']