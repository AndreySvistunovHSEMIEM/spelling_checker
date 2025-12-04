"""Главный файл для запуска тренажёра орфографии"""
import logging
import sys
import os
import threading

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon, QColor

from ui.main_window import SpellingTrainer

# Настройка логирования
logging.basicConfig(
    level=logging.WARNING,  # По умолчанию только предупреждения и ошибки
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    """Главная функция приложения"""
    logger = logging.getLogger(__name__)
    
    # Создаем приложение
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль
    app.setStyle('Fusion')
    
    # Устанавливаем палитру для светлой темы, чтобы избежать автоматического переключения
    # на темную тему в зависимости от системных настроек Windows
    from PySide6.QtGui import QPalette
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))  # Белый фон окна
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))   # Черный текст
    palette.setColor(QPalette.Base, QColor(240, 240, 240))   # Светлый фон редактирования
    palette.setColor(QPalette.AlternateBase, QColor(250, 250, 250))  # Альтернативный фон
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))    # Фон подсказок
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))         # Текст подсказок
    palette.setColor(QPalette.Text, QColor(0, 0, 0))                # Обычный текст
    palette.setColor(QPalette.Button, QColor(240, 240, 240))        # Кнопки
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))          # Текст на кнопках
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))    # Яркий текст (для ошибок)
    palette.setColor(QPalette.Highlight, QColor(51, 153, 255))      # Выделение
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  # Текст выделения
    app.setPalette(palette)
    
    # Устанавливаем иконку приложения для всех окон
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    try:
        # Создаем и показываем главное окно
        window = SpellingTrainer()
        window.show()
        # Запускаем главный цикл приложения
        return_code = app.exec()
        
        # Корректно завершаем приложение
        sys.exit(return_code)
        
        
    except Exception as e:
        logger.exception("Критическая ошибка запуска приложения: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()