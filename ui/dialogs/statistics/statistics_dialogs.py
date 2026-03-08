"""Диалоги статистики и аналитики"""
import json
import logging
import os
import re
from typing import Dict, Any

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QLineEdit, QComboBox, QListWidget, QTreeWidgetItem, QTreeWidget,
                               QGroupBox, QFileDialog, QInputDialog, QMessageBox, QGridLayout, QCheckBox, QListWidgetItem, QFormLayout,
                               QDateEdit, QCalendarWidget, QTabWidget, QSplitter, QWidget, QSizePolicy)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QDate

from core.constants import Constants
from core.models import WordData
from utils.helpers import show_silent_message
from .visualization import VisualizationWidget


logger = logging.getLogger(__name__)


class ProblemWordsDialog(QDialog):
    """Диалог проблемных слов и графиков ошибок (объединенный)"""
    
    def __init__(self, parent, word_repository):
        super().__init__(parent)
        self.word_repository = word_repository
        self.training_state = word_repository.app_data.training_state
        
        self.setWindowTitle("Проблемные слова и графики ошибок")
        self.setModal(True)
        
        # Устанавливаем иконку окна
        mistake_icon_path = os.path.join(parent.base_dir, Constants.MISTAKE_WORD_ICON)
        if os.path.exists(mistake_icon_path):
            self.setWindowIcon(QIcon(mistake_icon_path))
        
        self.resize(500, 600)
        
        # Инициализируем диапазон дат (по умолчанию за последние 30 дней)
        from datetime import datetime, timedelta
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)
        
        self._create_ui()
    
    def closeEvent(self, event):
        """Вызывается при закрытии диалога"""
        super().closeEvent(event)
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Создаем вкладки
        tabs = QTabWidget()
        
        # Первая вкладка: Проблемные слова
        problem_words_tab = self._create_problem_words_tab()
        tabs.addTab(problem_words_tab, "Проблемные слова")
        
        # Вторая вкладка: Таблица ошибок
        error_table_tab = self._create_dynamics_table_tab()
        tabs.addTab(error_table_tab, "Таблица ошибок")
        
        # Третья вкладка: Графики
        charts_tab = self._create_charts_tab()
        tabs.addTab(charts_tab, "Графики")
        
        layout.addWidget(tabs)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_problem_words_tab(self):
        """Создает вкладку с проблемными словами"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Добавляем фильтр по дате
        self._create_date_filter_section(layout)
        
        # Получаем проблемные слова
        problem_words = self._get_problem_words()
        
        if not problem_words:
            self._create_empty_state(layout)
        
        # Статистика
        self._create_stats_section(layout, problem_words)
        
        # Список слов
        self._create_words_list(layout, problem_words)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Создать категорию")
        create_btn.clicked.connect(lambda: self._create_problem_category(problem_words))
        button_layout.addWidget(create_btn)
        
        clear_btn = QPushButton("Очистить статистику")
        clear_btn.clicked.connect(self._clear_mistakes)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return tab
    
    
    def _create_dynamics_table_tab(self):
        """Создает вкладку с таблицей динамики ошибок"""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # Добавляем фильтр по дате
        self._create_date_filter_section(table_layout)
        
        # Добавляем статистику по динамике
        self._create_dynamics_section(table_layout)
        return table_widget
    
    def _create_charts_tab(self):
        """Создает вкладку с графиками"""
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        # Добавляем фильтр по дате
        self._create_date_filter_section(chart_layout)
        
        # Создаем виджет для визуализации
        self.visualization_widget = VisualizationWidget()
        chart_layout.addWidget(self.visualization_widget)
        
        # Добавляем выпадающий список для выбора типа графика
        chart_type_layout = QHBoxLayout()
        chart_type_layout.addWidget(QLabel("Тип графика:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "Общее количество ошибок по дням",
            "Ошибки по категориям",
            "Прогресс (улучшение/ухудшение)"
        ])
        self.chart_type_combo.currentTextChanged.connect(self._update_visualizations)
        chart_type_layout.addWidget(self.chart_type_combo)
        chart_type_layout.addStretch()
        chart_layout.addLayout(chart_type_layout)
        
        # Инициализируем визуализации
        self._update_visualizations()
        
        return chart_widget
    
    def _create_dynamics_section(self, layout):
        """Создает секцию отображения динамики ошибок"""
        dynamics_group = QGroupBox("Динамика ошибок по датам")
        dynamics_layout = QVBoxLayout(dynamics_group)
        
        # Создаем таблицу для отображения динамики
        self.dynamics_table = QTreeWidget()
        self.dynamics_table.setHeaderLabels(["Дата", "Количество ошибок"])
        self.dynamics_table.setColumnWidth(0, 150)
        self.dynamics_table.setColumnWidth(1, 100)
        
        # Заполняем таблицу данными
        self._fill_dynamics_table()
        
        dynamics_layout.addWidget(self.dynamics_table)
        layout.addWidget(dynamics_group)
    
    def _fill_dynamics_table(self):
        """Заполняет таблицу данными динамики ошибок"""
        # Очищаем таблицу
        self.dynamics_table.clear()
        
        # Получаем ошибки в заданном диапазоне дат
        if hasattr(self.training_state, 'mistake_history') and self.training_state.mistake_history:
            filtered_mistakes = self.training_state.get_mistakes_by_date_range(
                self.start_date, self.end_date
            )
            
            # Группируем ошибки по датам
            mistakes_by_date = {}
            for mistake in filtered_mistakes:
                date_key = mistake.timestamp.strftime('%d.%m.%Y')
                if date_key not in mistakes_by_date:
                    mistakes_by_date[date_key] = 0
                mistakes_by_date[date_key] += 1
            
            # Сортируем по дате и добавляем в таблицу
            for date_str in sorted(mistakes_by_date.keys()):
                count = mistakes_by_date[date_str]
                item = QTreeWidgetItem([date_str, str(count)])
                self.dynamics_table.addTopLevelItem(item)
        else:
            # Если нет истории ошибок с датами, показываем сообщение
            item = QTreeWidgetItem(["Нет данных", ""])
            self.dynamics_table.addTopLevelItem(item)
    
    def _update_visualizations(self):
        """Обновляет графики визуализации"""
        if hasattr(self, 'visualization_widget'):
            # Определяем тип графика по текущему выбору
            chart_type_text = self.chart_type_combo.currentText()
            chart_type_map = {
                "Общее количество ошибок по дням": "total",
                "Ошибки по категориям": "by_category",
                "Прогресс (улучшение/ухудшение)": "progress"
            }
            chart_type = chart_type_map.get(chart_type_text, "total")
            
            # Обновляем визуализацию
            if hasattr(self.training_state, 'mistake_history') and self.training_state.mistake_history:
                self.visualization_widget.plot_errors_dynamics(
                    self.training_state.mistake_history,
                    self.start_date,
                    self.end_date,
                    chart_type
                )
    
    def _get_problem_words(self):
        """Возвращает список проблемных слов для всех категорий в заданном диапазоне дат"""
        # Получаем ошибки для всех категорий в заданном диапазоне дат
        all_mistakes = {}
        
        # Если есть история ошибок с датами
        if hasattr(self.training_state, 'mistake_history') and self.training_state.mistake_history:
            # Фильтруем ошибки по диапазону дат
            filtered_mistakes = self.training_state.get_mistakes_by_date_range(
                self.start_date, self.end_date
            )
            
            # Подсчитываем количество ошибок для каждого слова в заданном диапазоне дат
            for mistake in filtered_mistakes:
                word = mistake.word
                if word in all_mistakes:
                    all_mistakes[word] += 1
                else:
                    all_mistakes[word] = 1
        else:
            # Если нет истории ошибок с датами, используем старую логику
            for category, mistakes in self.training_state.mistakes_count.items():
                for word, count in mistakes.items():
                    if count > 0:
                        if word in all_mistakes:
                            all_mistakes[word] += count
                        else:
                            all_mistakes[word] = count
        
        return [(word, count) for word, count in all_mistakes.items()]
    
    def _create_date_filter_section(self, layout):
        """Создает секцию фильтрации по дате"""
        date_group = QGroupBox("Фильтр по дате")
        date_layout = QHBoxLayout(date_group)  # Changed from QFormLayout to QHBoxLayout
        
        # Создаем горизонтальный макет для элементов управления
        filter_layout = QHBoxLayout()
        
        # Метка и выбор начальной даты
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate(self.start_date.year, self.start_date.month, self.start_date.day))
        self.start_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.start_date_edit.setCalendarPopup(True)
        
        # Метка и выбор конечной даты
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate(self.end_date.year, self.end_date.month, self.end_date.day))
        self.end_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.end_date_edit.setCalendarPopup(True)
        
        # Добавляем элементы в горизонтальный макет
        filter_layout.addWidget(QLabel("С:"))
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addWidget(QLabel("По:"))
        filter_layout.addWidget(self.end_date_edit)
        
        # Кнопки управления
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._apply_date_filter)
        filter_layout.addWidget(refresh_btn)
        
        reset_btn = QPushButton("Сбросить")
        reset_btn.clicked.connect(self._reset_date_filter)
        filter_layout.addWidget(reset_btn)
        
        # Добавляем фильтр в макет группы (а не в QFormLayout)
        date_layout.addLayout(filter_layout)  # Add the filter layout directly
        date_layout.addStretch()  # Add stretch to the right to align to the left
        
        # Уменьшаем высоту группы
        date_group.setMaximumHeight(70)
        
        layout.addWidget(date_group)
    
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
        
        # Убираем лишнюю кнопку закрытия, так как основная кнопка "Закрыть" уже есть внизу диалога
        # Оставляем только пустое пространство для центрирования сообщения
        layout.addStretch()
    
    
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
        """Очищает статистику ошибок (mistake_history, mistakes_count, wrong_answers)"""
        reply = QMessageBox.question(self, "Подтверждение",
                                   "Очистить статистику ошибок?\n\n"
                                   "Это удалит:\n"
                                   "• Историю ошибок с датами\n"
                                   "• Количество ошибок для каждого слова\n"
                                   "• Список неправильных ответов")
        if reply == QMessageBox.Yes:
            # Очищаем ВСЕ статистику ошибок, включая историю с датами
            self.training_state.mistake_history.clear()
            self.training_state.mistakes_count.clear()
            self.training_state.wrong_answers.clear()
            
            self.word_repository.save_data()
            
            # Обновляем интерфейс
            self._refresh_ui()
            
            show_silent_message(self.parent(), "Успех", "Статистика ошибок очищена")
    
    def _apply_date_filter(self):
        """Применяет фильтр по дате"""
        from datetime import datetime
        start_qdate = self.start_date_edit.date()
        end_qdate = self.end_date_edit.date()
        
        # Преобразуем QDate в datetime
        self.start_date = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
        self.end_date = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day())
        
        # Обновляем интерфейс с учетом фильтра
        self._refresh_ui()
    
    def _reset_date_filter(self):
        """Сбрасывает фильтр по дате к значению по умолчанию"""
        from datetime import datetime, timedelta
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)
        
        # Обновляем виджеты дат
        self.start_date_edit.setDate(QDate(self.start_date.year, self.start_date.month, self.start_date.day))
        self.end_date_edit.setDate(QDate(self.end_date.year, self.end_date.month, self.end_date.day))
        
        # Обновляем интерфейс
        self._refresh_ui()
    
    def _refresh_ui(self):
        """Обновляет интерфейс с учетом текущего фильтра по дате"""
        # Получаем текущий макет
        main_layout = self.layout()
        if main_layout is not None:
            # Удаляем все дочерние элементы, кроме последнего (предполагаем, что это кнопки управления)
            if main_layout.count() > 1:
                # Удаляем вкладки (первый элемент), оставляя кнопки управления
                old_tabs = main_layout.takeAt(0)
                if old_tabs.widget():
                    old_tabs.widget().deleteLater()
                elif old_tabs.layout():
                    self._clear_layout(old_tabs.layout())
            
            # Создаем только вкладки без повторного создания основного макета
            tabs = QTabWidget()
            
            # Первая вкладка: Проблемные слова
            problem_words_tab = self._create_problem_words_tab()
            tabs.addTab(problem_words_tab, "Проблемные слова")
            
            # Вторая вкладка: Таблица ошибок
            error_table_tab = self._create_dynamics_table_tab()
            tabs.addTab(error_table_tab, "Таблица ошибок")
            
            # Третья вкладка: Графики
            charts_tab = self._create_charts_tab()
            tabs.addTab(charts_tab, "Графики")
            
            # Вставляем вкладки на первое место в макете
            main_layout.insertWidget(0, tabs)
    
    def _clear_layout(self, layout):
        """Рекурсивно очищает макет и все его дочерние элементы"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
    
    def _get_mistakes_by_date_range(self):
        """Возвращает ошибки в заданном диапазоне дат"""
        if hasattr(self.training_state, 'mistake_history') and self.training_state.mistake_history:
            return self.training_state.get_mistakes_by_date_range(
                self.start_date, self.end_date
            )
        return []
    
    def _create_stats_section(self, layout, problem_words):
        """Создает секцию статистики"""
        stats_group = QGroupBox("Статистика ошибок")
        stats_layout = QFormLayout(stats_group)
        
        total_words = len(problem_words)
        total_mistakes = sum(count for _, count in problem_words)
        
        # Создаем горизонтальный макет для статистики
        stats_info_layout = QHBoxLayout()
        
        # Добавляем виджеты статистики
        total_words_label = QLabel(f"{total_words}")
        total_mistakes_label = QLabel(f"{total_mistakes}")
        
        # Показываем диапазон дат
        date_range_label = QLabel(f"{self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}")
        
        # Добавляем информацию о категориях
        categories_with_errors = set()
        filtered_mistakes = self._get_mistakes_by_date_range()
        
        for mistake in filtered_mistakes:
            if mistake.category:
                categories_with_errors.add(mistake.category)
        
        categories_label = QLabel(f"{len(categories_with_errors)}")
        
        # Добавляем элементы в форму
        stats_layout.addRow("Всего проблемных слов:", total_words_label)
        stats_layout.addRow("Всего ошибок:", total_mistakes_label)
        stats_layout.addRow("Период:", date_range_label)
        stats_layout.addRow("Категории с ошибками:", categories_label)
        
        # Уменьшаем ширину группы
        stats_group.setMaximumWidth(300)
        
        layout.addWidget(stats_group)
    
    def _create_words_list(self, layout, problem_words):
        """Создает список проблемных слов"""
        list_group = QGroupBox("Слова с ошибками")
        list_layout = QVBoxLayout(list_group)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["Слово", "Ошибок", "Неправильные ответы", "Категория"])
        tree.setColumnWidth(0, 110)
        tree.setColumnWidth(1, 60)
        tree.setColumnWidth(2, 150)
        tree.setColumnWidth(3, 100)
        
        # Объединяем неправильные ответы из всех категорий в заданном диапазоне дат
        all_wrong_answers = {}
        all_categories = {}
        filtered_mistakes = self._get_mistakes_by_date_range()
        
        for mistake in filtered_mistakes:
            word = mistake.word
            if word not in all_wrong_answers:
                all_wrong_answers[word] = []
            if mistake.wrong_answer not in all_wrong_answers[word]:
                all_wrong_answers[word].append(mistake.wrong_answer)
            
            if word not in all_categories:
                all_categories[word] = set()
            if mistake.category:
                all_categories[word].add(mistake.category)
        
        for word, count in sorted(problem_words, key=lambda x: x[1], reverse=True):
            # Получаем объединенные неправильные ответы для слова
            wrong_answers = all_wrong_answers.get(word, [])
            categories = list(all_categories.get(word, []))
            
            wrong_answers_text = ", ".join(wrong_answers[:3])
            if len(wrong_answers) > 3:
                wrong_answers_text += f"... (ещё {len(wrong_answers) - 3})"
            
            categories_text = ", ".join(categories[:2])
            if len(categories) > 2:
                categories_text += f"... (ещё {len(categories) - 2})"
            
            item = QTreeWidgetItem([word, str(count), wrong_answers_text, categories_text])
            tree.addTopLevelItem(item)
        
        list_layout.addWidget(tree)
        
        # Обеспечиваем, чтобы область слов с ошибками занимала оставшееся пространство
        list_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout.addWidget(list_group)
__all__ = ['ProblemWordsDialog']