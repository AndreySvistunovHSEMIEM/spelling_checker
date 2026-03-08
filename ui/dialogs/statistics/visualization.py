"""Модуль визуализации прогресса и ошибок по датам"""
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 backend for compatibility
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from PySide6.QtWidgets import QWidget, QVBoxLayout
from typing import List, Dict, Tuple, Optional
from core.models import MistakeRecord
import numpy as np


class StatisticsVisualizer:
    """Класс для визуализации статистики ошибок по датам"""
    
    def __init__(self):
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.fig.patch.set_facecolor('white')
        
    def _add_interactivity(self, ax):
        """Добавляет интерактивные элементы к графику"""
        # Включаем сетку
        ax.grid(True, alpha=0.3)
        
        # Добавляем возможность увеличения/уменьшения
        self.fig.tight_layout()
        
        # Поворачиваем метки дат для лучшего отображения и уменьшаем размер шрифта
        for label in ax.get_xticklabels():
            label.set_rotation(45)
            label.set_ha('right')
            label.set_fontsize(8)  # Уменьшаем размер шрифта дат
        
    def create_error_dynamics_chart(self, 
                                  mistake_history: List[MistakeRecord], 
                                  start_date: datetime, 
                                  end_date: datetime,
                                  chart_type: str = "total") -> Figure:
        """
        Создает график динамики ошибок
        
        Args:
            mistake_history: История ошибок
            start_date: Начальная дата
            end_date: Конечная дата
            chart_type: Тип графика ("total", "by_category", "progress")
        """
        # Очистка предыдущего графика
        self.fig.clear()
        
        # Фильтрация ошибок по дате
        filtered_mistakes = [
            m for m in mistake_history 
            if start_date <= m.timestamp <= end_date
        ]
        
        if chart_type == "total":
            return self._create_total_errors_chart(filtered_mistakes, start_date, end_date)
        elif chart_type == "by_category":
            return self._create_errors_by_category_chart(filtered_mistakes, start_date, end_date)
        elif chart_type == "progress":
            return self._create_progress_chart(filtered_mistakes, start_date, end_date)
        else:
            return self._create_total_errors_chart(filtered_mistakes, start_date, end_date)
    
    def _create_total_errors_chart(self, 
                                 mistakes: List[MistakeRecord], 
                                 start_date: datetime, 
                                 end_date: datetime) -> Figure:
        """Создает график общего количества ошибок по дням"""
        ax = self.fig.add_subplot(111)
        
        # Генерация всех дат в диапазоне
        date_range = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            date_range.append(datetime.combine(current_date, datetime.min.time()))
            current_date += timedelta(days=1)
        
        # Подсчет ошибок по дням
        error_counts = {}
        for mistake in mistakes:
            date_key = mistake.timestamp.date()
            error_counts[date_key] = error_counts.get(date_key, 0) + 1
        
        # Подготовка данных для графика
        dates = []
        counts = []
        for date_obj in date_range:
            date_only = date_obj.date()
            dates.append(date_obj)
            counts.append(error_counts.get(date_only, 0))
        
        # Построение графика
        line = ax.plot(dates, counts, marker='o', linewidth=2, markersize=6, label='Ошибки', picker=True, pickradius=5)
        
        # Настройка внешнего вида
        ax.set_title('Динамика ошибок по дням', fontsize=12)
        ax.set_xlabel('Дата', fontsize=10)
        ax.set_ylabel('Количество ошибок', fontsize=10)
        ax.legend()
        
        # Настройка оси Y для отображения только целых чисел
        from matplotlib.ticker import MaxNLocator
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Добавляем интерактивные элементы
        self._add_interactivity(ax)
        
        # Форматирование дат на оси X
        date_format = DateFormatter('%d.%m')
        ax.xaxis.set_major_formatter(date_format)
        
        # Уменьшаем размер шрифта для меток дат
        for label in ax.get_xticklabels():
            label.set_fontsize(8)
        
        # Автоматическое масштабирование графика под видимую область
        ax.relim()
        ax.autoscale_view()
        
        self.fig.tight_layout()
        return self.fig
    
    def _create_errors_by_category_chart(self, 
                                       mistakes: List[MistakeRecord], 
                                       start_date: datetime, 
                                       end_date: datetime) -> Figure:
        """Создает график ошибок по категориям"""
        ax = self.fig.add_subplot(111)
        
        # Группировка ошибок по категориям
        categories_data = {}
        for mistake in mistakes:
            category = mistake.category or "Без категории"
            if category not in categories_data:
                categories_data[category] = {}
            
            date_key = mistake.timestamp.date()
            categories_data[category][date_key] = categories_data[category].get(date_key, 0) + 1
        
        # Генерация всех дат в диапазоне
        date_range = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            date_range.append(datetime.combine(current_date, datetime.min.time()))
            current_date += timedelta(days=1)
        
        # Построение графика для каждой категории
        for category, daily_counts in categories_data.items():
            dates = []
            counts = []
            for date_obj in date_range:
                date_only = date_obj.date()
                dates.append(date_obj)
                counts.append(daily_counts.get(date_only, 0))
            
            line = ax.plot(dates, counts, marker='o', linewidth=2, markersize=4, label=category, picker=True, pickradius=5)
        
        # Настройка внешнего вида
        ax.set_title('Ошибки по категориям', fontsize=12)
        ax.set_xlabel('Дата', fontsize=10)
        ax.set_ylabel('Количество ошибок', fontsize=10)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Добавляем интерактивные элементы
        self._add_interactivity(ax)
        
        # Форматирование дат на оси X
        date_format = DateFormatter('%d.%m')
        ax.xaxis.set_major_formatter(date_format)
        
        # Уменьшаем размер шрифта для меток дат
        for label in ax.get_xticklabels():
            label.set_fontsize(8)
        
        # Автоматическое масштабирование графика под видимую область
        ax.relim()
        ax.autoscale_view()
        
        self.fig.tight_layout()
        return self.fig
    
    def _create_progress_chart(self, 
                             mistakes: List[MistakeRecord], 
                             start_date: datetime, 
                             end_date: datetime) -> Figure:
        """Создает график прогресса (улучшение/ухудшение)"""
        ax = self.fig.add_subplot(111)
        
        # Группировка ошибок по дням
        daily_mistakes = {}
        for mistake in mistakes:
            date_key = mistake.timestamp.date()
            if date_key not in daily_mistakes:
                daily_mistakes[date_key] = 0
            daily_mistakes[date_key] += 1
        
        # Генерация всех дат в диапазоне
        date_range = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            date_range.append(datetime.combine(current_date, datetime.min.time()))
            current_date += timedelta(days=1)
        
        # Подготовка данных для графика прогресса
        dates = []
        cumulative_errors = []
        total_errors = 0
        
        for date_obj in date_range:
            date_only = date_obj.date()
            daily_error_count = daily_mistakes.get(date_only, 0)
            total_errors += daily_error_count
            dates.append(date_obj)
            cumulative_errors.append(total_errors)
        
        # Построение графика
        line1 = ax.plot(dates, cumulative_errors, marker='o', linewidth=2, markersize=6,
                label='Накопленные ошибки', color='red', picker=True, pickradius=5)
        
        # Вычисление скользящего среднего для тренда
        if len(cumulative_errors) >= 3:
            window_size = min(3, len(cumulative_errors))
            moving_avg = []
            for i in range(len(cumulative_errors)):
                start_idx = max(0, i - window_size + 1)
                avg_val = sum(cumulative_errors[start_idx:i+1]) / (i - start_idx + 1)
                moving_avg.append(avg_val)
            
            line2 = ax.plot(dates, moving_avg, linestyle='--', linewidth=2,
                    label='Скользящее среднее', color='blue', picker=True, pickradius=5)
        
        # Настройка внешнего вида
        ax.set_title('Прогресс по ошибкам (накопленные)', fontsize=12)
        ax.set_xlabel('Дата', fontsize=10)
        ax.set_ylabel('Количество ошибок', fontsize=10)
        ax.legend()
        
        # Добавляем интерактивные элементы
        self._add_interactivity(ax)
        
        # Форматирование дат на оси X
        date_format = DateFormatter('%d.%m')
        ax.xaxis.set_major_formatter(date_format)
        
        # Уменьшаем размер шрифта для меток дат
        for label in ax.get_xticklabels():
            label.set_fontsize(8)
        
        # Автоматическое масштабирование графика под видимую область
        ax.relim()
        ax.autoscale_view()
        
        self.fig.tight_layout()
        return self.fig


class VisualizationWidget(QWidget):
    """Виджет для отображения визуализаций в Qt интерфейсе"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Создание холста для matplotlib
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        self.visualizer = StatisticsVisualizer()
    
    def plot_errors_dynamics(self, 
                           mistake_history: List[MistakeRecord], 
                           start_date: datetime, 
                           end_date: datetime,
                           chart_type: str = "total"):
        """Отображает график динамики ошибок"""
        # Создание графика
        fig = self.visualizer.create_error_dynamics_chart(
            mistake_history, start_date, end_date, chart_type
        )
        
        # Обновление холста
        self.canvas.figure = fig
        self.canvas.draw()