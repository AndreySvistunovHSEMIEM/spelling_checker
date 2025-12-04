"""Модуль для создания и управления меню баром приложения"""

from PySide6.QtWidgets import QMenuBar, QMainWindow


class MenuBar:
    """Класс для создания и управления меню баром"""
    
    def __init__(self, main_window: QMainWindow):
        """
        Инициализация меню бара
        
        Args:
            main_window: Ссылка на главное окно приложения
        """
        self.main_window = main_window
        self._create_menu_bar()
    
    def _create_menu_bar(self):
        """Создание меню бара с пунктами File, Edit и Help"""
        menu_bar = self.main_window.menuBar()
        
        # Файл menu
        file_menu = menu_bar.addMenu("Файл")
        
        # Файл -> Настройки
        settings_action = file_menu.addAction("Настройки")
        settings_action.triggered.connect(self.main_window.open_settings)
        
        # Файл -> Выход
        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.main_window.close)
        
        # Правка menu
        edit_menu = menu_bar.addMenu("Правка")
        
        # Правка -> Добавить слов
        add_word_action = edit_menu.addAction("Добавить слово")
        add_word_action.triggered.connect(self.main_window.add_new_word)
        
        # Правка -> Словарь
        dictionary_action = edit_menu.addAction("Словарь")
        dictionary_action.triggered.connect(self.main_window.open_word_manager)
        
        # Правка -> Аналитика
        analytics_action = edit_menu.addAction("Аналитика")
        analytics_action.triggered.connect(self.main_window.show_problem_words)
        
        # Помощь
        help_menu = menu_bar.addMenu("Помощь")
        # Help menu remains empty for now
    
    def _placeholder_action(self):
        """Заглушка для других действий меню"""
        # Пока что ничего не делаем, позже можно добавить функционал
        pass