from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
import os
from .UIUtils import UIUtils, colorMode

class ImageAnalysisWindow(QtWidgets.QWidget):
    def __init__(self, app, screenshot_path):
        super().__init__()
        self.app = app
        self.screenshot_path = screenshot_path
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Image Analysis')
        self.setMinimumSize(800, 500)
        UIUtils.setup_window_and_layout(self)
        
        # Main layout
        main_layout = QtWidgets.QHBoxLayout(self.background)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left side - Image display
        image_widget = QtWidgets.QWidget()
        image_layout = QtWidgets.QVBoxLayout(image_widget)
        
        # Load and display the image
        pixmap = QtGui.QPixmap(self.screenshot_path)
        # Scale the image to fit while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        image_label = QtWidgets.QLabel()
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(image_label)
        
        main_layout.addWidget(image_widget)
        
        # Right side - Chat interface
        chat_widget = QtWidgets.QWidget()
        chat_layout = QtWidgets.QVBoxLayout(chat_widget)
        
        # Chat history
        self.chat_history = QtWidgets.QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet(f"""
            QTextEdit {{
                background-color: {'#333' if colorMode == 'dark' else '#fff'};
                color: {'#fff' if colorMode == 'dark' else '#000'};
                border: 1px solid {'#555' if colorMode == 'dark' else '#ccc'};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        chat_layout.addWidget(self.chat_history)
        
        # Input area
        input_layout = QtWidgets.QHBoxLayout()
        
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Ask about the image...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {'#444' if colorMode == 'dark' else '#fff'};
                color: {'#fff' if colorMode == 'dark' else '#000'};
                border: 1px solid {'#555' if colorMode == 'dark' else '#ccc'};
                border-radius: 5px;
                padding: 8px;
            }}
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        # Send button
        send_button = QtWidgets.QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        chat_layout.addLayout(input_layout)
        main_layout.addWidget(chat_widget)

    def send_message(self):
        question = self.input_field.text().strip()
        if not question:
            return
            
        # Add user question to chat history
        self.chat_history.append(f'<b>You:</b> {question}')
        
        # Clear input field
        self.input_field.clear()
        
        # Send to AI for analysis
        self.app.current_provider.analyze_image(self.screenshot_path, question)
        
    def add_ai_response(self, response):
        self.chat_history.append(f'<b>AI:</b> {response}')
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
