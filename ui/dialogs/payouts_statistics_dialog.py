"""Диалог статистики выплат"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QDateEdit,
                               QTableWidget, QTableWidgetItem, 
                               QHeaderView, QGroupBox, QFormLayout)
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta


class PayoutsStatisticsDialog(QDialog):
    """Диалог для отображения статистики выплат"""
    
    def __init__(self, parent, training_state):
        """
        Инициализация диалога статистики выплат
        
        Args:
            parent: Родительское окно
            training_state: Объект состояния тренировки с историей выплат
        """
        super().__init__(parent)
        self.training_state = training_state
        self.setWindowTitle("Статистика выплат")
        self.resize(300, 370)
        
        self.setup_ui()
        self.update_statistics()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)  # Выравнивание по верху
        
        # Группа для выбора диапазона дат
        date_group = QGroupBox("Диапазон дат")
        date_layout = QHBoxLayout(date_group)  # Изменяем на QHBoxLayout для одной строки
        date_layout.setAlignment(Qt.AlignLeft)  # Выравнивание по левому краю
        
        # Дата начала
        start_date_layout = QHBoxLayout()
        start_date_layout.setAlignment(Qt.AlignLeft)  # Выравнивание по левому краю
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))  # По умолчанию за 30 дней
        self.start_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.start_date_edit.setCalendarPopup(True)
        
        # Удаляем кнопку "Начало"
        start_date_layout.addWidget(QLabel("С:"))
        start_date_layout.addWidget(self.start_date_edit)
        
        # Дата окончания
        end_date_layout = QHBoxLayout()
        end_date_layout.setAlignment(Qt.AlignLeft)  # Выравнивание по левому краю
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())  # По умолчанию текущая дата
        self.end_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.end_date_edit.setCalendarPopup(True)
        
        # Удаляем кнопку "Сейчас"
        end_date_layout.addWidget(QLabel("По:"))
        end_date_layout.addWidget(self.end_date_edit)
        
        date_layout.addLayout(start_date_layout)
        date_layout.addSpacing(10)  # Добавляем небольшой отступ между группами
        date_layout.addLayout(end_date_layout)
        
        # Подключаем сигналы для автоматического обновления
        self.start_date_edit.dateChanged.connect(self.update_statistics)
        self.end_date_edit.dateChanged.connect(self.update_statistics)
        
        layout.addWidget(date_group)
        # Убираем кнопку "Обновить", т.к. обновление теперь автоматическое при выборе даты
        
        # Таблица выплат
        self.payouts_table = QTableWidget()
        self.payouts_table.setColumnCount(2)  # Уменьшаем количество столбцов до 2
        self.payouts_table.setHorizontalHeaderLabels(["Дата", "Сумма"])  # Убираем столбец "Описание"
        
        # Настройка ширины столбцов
        header = self.payouts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Дата
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Сумма
        
        layout.addWidget(self.payouts_table)
        
        # Группа общей статистики
        stats_group = QGroupBox("Общая статистика")
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.setAlignment(Qt.AlignLeft)  # Выравнивание по левому краю
        
        self.total_payouts_label = QLabel("Общая сумма выплат: 0.00 руб.")
        self.total_payouts_label.setStyleSheet("font-weight: bold;")
        
        stats_layout.addWidget(self.total_payouts_label)
        stats_layout.addStretch()  # Добавляем растяжение в конце для выравнивания по левому краю
        
        layout.addWidget(stats_group)
        
        # Кнопка закрытия
        close_btn_layout = QHBoxLayout()  # Создаем отдельный layout для кнопки
        close_btn_layout.setAlignment(Qt.AlignLeft)  # Выравнивание по левому краю
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn.setMaximumWidth(100)  # Ограничиваем ширину кнопки
        
        close_btn_layout.addWidget(close_btn)
        layout.addLayout(close_btn_layout)  # Добавляем layout с кнопкой
        layout.setAlignment(Qt.AlignLeft)  # Выравнивание по левому краю
    
    def set_date_range(self, target):
        """Устанавливает диапазон дат"""
        if target == "start":
            # Устанавливаем дату начала на начало года
            self.start_date_edit.setDate(QDate.currentDate().addDays(-365))
        elif target == "end":
            # Устанавливаем дату окончания на текущую дату
            self.end_date_edit.setDate(QDate.currentDate())
    
    def update_statistics(self):
        """Обновляет статистику выплат"""
        # Получаем даты из виджетов
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        
        # Преобразуем date в datetime, добавляем 23:59 к дате окончания, чтобы включить весь день
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(hour=23, minute=59, second=59)
        
        # Получаем выплаты в заданном диапазоне дат
        payouts = self.training_state.get_payouts_by_date_range(start_datetime, end_datetime)
        
        # Обновляем таблицу
        self.payouts_table.setRowCount(len(payouts))
        
        total_amount = 0.0
        for row, payout in enumerate(payouts):
            # Дата
            date_item = QTableWidgetItem(payout.timestamp.strftime("%d.%m.%Y"))
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.payouts_table.setItem(row, 0, date_item)
            
            # Сумма
            amount_item = QTableWidgetItem(f"{payout.amount:.2f}")
            amount_item.setFlags(amount_item.flags() & ~Qt.ItemIsEditable)
            self.payouts_table.setItem(row, 1, amount_item)
            
            total_amount += payout.amount
        
        # Обновляем общую сумму
        self.total_payouts_label.setText(f"Общая сумма выплат: {total_amount:.2f} руб.")