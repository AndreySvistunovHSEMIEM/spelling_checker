"""Диалог для выплаты рублей"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QLineEdit, 
                               QMessageBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class PayoutDialog(QDialog):
    """Диалог для выплаты рублей"""
    
    def __init__(self, parent, current_score):
        """
        Инициализация диалога выплаты
        
        Args:
            parent: Родительское окно
            current_score: Текущий счёт в рублях
        """
        super().__init__(parent)
        self.current_score = current_score
        self.setWindowTitle("Выплата")
        self.setModal(True)
        self.resize(300, 150)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Метка с текущим счётом
        score_label = QLabel(f"Текущий счёт: {self.current_score:.2f} руб.")
        score_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        score_label.setFont(font)
        layout.addWidget(score_label)
        
        # Поле ввода суммы выплаты
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Сумма выплаты:"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Введите сумму...")
        input_layout.addWidget(self.amount_input)
        layout.addLayout(input_layout)
        
        # Кнопка "Вся сумма"
        payout_all_btn = QPushButton("Вся сумма")
        payout_all_btn.clicked.connect(self.set_full_amount)
        layout.addWidget(payout_all_btn)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Кнопки OK и Отмена
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Устанавливаем фокус на поле ввода
        self.amount_input.setFocus()
    
    def set_full_amount(self):
        """Устанавливает сумму выплаты равной всей сумме на счёте"""
        self.amount_input.setText(str(self.current_score))
    
    def validate_and_accept(self):
        """Проверяет введённую сумму и принимает диалог"""
        try:
            amount_str = self.amount_input.text().strip()
            if not amount_str:
                QMessageBox.warning(self, "Ошибка", "Введите сумму выплаты!")
                return
            
            amount = float(amount_str)
            
            if amount <= 0:
                QMessageBox.warning(self, "Ошибка", "Сумма выплаты должна быть больше 0!")
                return
            
            if amount > self.current_score:
                QMessageBox.warning(self, "Ошибка", "Сумма выплаты не может превышать текущий счёт!")
                return
            
            self.amount = amount
            self.accept()
            
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную сумму!")
            return
    
    def get_amount(self):
        """Возвращает введённую сумму"""
        return getattr(self, 'amount', 0.0)