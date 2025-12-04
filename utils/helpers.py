"""Вспомогательные функции"""
import os
from PySide6.QtWidgets import QMessageBox, QDialog
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

def center_window(parent, child_window):
    """
    Центрирует дочернее окно относительно родительского
    
    Args:
        parent: Родительское окно
        child_window: Дочернее окно для центрирования
    """
    child_window_geometry = child_window.frameGeometry()
    main_window_center = parent.frameGeometry().center()
    child_window_geometry.moveCenter(main_window_center)
    child_window.move(child_window_geometry.topLeft())

def set_window_icon(window, icon_path):
    """
    Устанавливает иконку окна
    
    Args:
        window: Окно для установки иконки
        icon_path: Путь к файлу иконки
    """
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

def show_silent_message(parent, title, message, is_error=False):
    """
    Показывает сообщение без системного звука
    
    Args:
        parent: Родительское окно
        title: Заголовок сообщения
        message: Текст сообщения
        is_error: True если это сообщение об ошибке
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    # Устанавливаем иконку приложения
    icon_path = os.path.join(parent.base_dir, "app_icon.png")
    if os.path.exists(icon_path):
        msg_box.setWindowIcon(QIcon(icon_path))
    
    # Отключаем стандартную иконку (которая вызывает системный звук)
    msg_box.setIcon(QMessageBox.NoIcon)
    
    # Добавляем кнопку OK
    ok_button = msg_box.addButton(QMessageBox.Ok)
    msg_box.setDefaultButton(ok_button)
    
    # Показываем сообщение и ждем ответа
    msg_box.exec()

def create_scaled_pixmap(image_path, width, height):
    """
    Создает масштабированное изображение
    """
    try:
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            return pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        pass
    
    return None

def create_dialog(parent, title, width, height):
    """
    Создает стандартное диалоговое окно
    
    Args:
        parent: Родительское окно
        title: Заголовок окна
        width: Ширина окна
        height: Высота окна
        
    Returns:
        Настроенное диалоговое окно
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setGeometry(200, 200, width, height)
    center_window(parent, dialog)
    
    # Устанавливаем иконку
    icon_path = os.path.join(parent.base_dir, "app_icon.png")
    set_window_icon(dialog, icon_path)
    
    return dialog