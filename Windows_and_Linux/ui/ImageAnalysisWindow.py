from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
import os
import re
from .UIUtils import ThemeBackground, colorMode
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

class ImageAnalysisWindow(QtWidgets.QWidget):
    def __init__(self, app, screenshot_path):
        super().__init__()
        self.app = app
        self.screenshot_path = screenshot_path
        
        # Initialize syntax highlighting formatter
        self.formatter = HtmlFormatter(
            style='monokai' if colorMode == 'dark' else 'default',
            cssclass='highlight',
            noclasses=True
        )
        
        self.init_ui()
        
        # Automatically trigger initial analysis
        self.send_message("Please analyze this image and describe what you see.")
        
    def init_ui(self):
        self.setWindowTitle('Image Analysis')
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setMinimumSize(800, 600)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Theme background
        self.background = ThemeBackground(self, self.app.config.get('theme', 'gradient'), is_popup=True)
        main_layout.addWidget(self.background)

        # Content layout
        content_layout = QtWidgets.QHBoxLayout(self.background)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Left side - Image display
        image_widget = QtWidgets.QWidget()
        image_layout = QtWidgets.QVBoxLayout(image_widget)
        
        # Close button
        close_button = QtWidgets.QPushButton("×")
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-size: 20px;
                border: none;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {'#333333' if colorMode == 'dark' else '#ebebeb'};
            }}
        """)
        close_button.clicked.connect(self.close)
        image_layout.addWidget(close_button, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        
        # Load and display the image
        pixmap = QtGui.QPixmap(self.screenshot_path)
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        image_label = QtWidgets.QLabel()
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(image_label)
        
        content_layout.addWidget(image_widget)
        
        # Right side - Chat interface
        chat_widget = QtWidgets.QWidget()
        chat_layout = QtWidgets.QVBoxLayout(chat_widget)
        
        # Chat history with syntax highlighting support
        self.chat_history = QtWidgets.QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet(f"""
            QTextEdit {{
                background-color: {'#333' if colorMode == 'dark' else '#fff'};
                color: {'#fff' if colorMode == 'dark' else '#000'};
                border: 1px solid {'#555' if colorMode == 'dark' else '#ccc'};
                border-radius: 5px;
                padding: 10px;
                font-family: "Consolas", monospace;
            }}
            .highlight {{
                margin: 5px 0;
                padding: 10px;
                border-radius: 5px;
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
        send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#2e7d32' if colorMode == 'dark' else '#4CAF50'};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: {'#1b5e20' if colorMode == 'dark' else '#45a049'};
            }}
        """)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        chat_layout.addLayout(input_layout)
        content_layout.addWidget(chat_widget)

    def format_code_blocks(self, text):
        """Format code blocks with syntax highlighting"""
        def replace_code_block(match):
            code = match.group(2)
            lang = match.group(1) if match.group(1) else ''
            
            try:
                if lang:
                    lexer = get_lexer_by_name(lang)
                else:
                    lexer = guess_lexer(code)
                return highlight(code, lexer, self.formatter)
            except ClassNotFound:
                # If language detection fails, default to plain text
                return f'<pre style="background-color: {"#444" if colorMode == "dark" else "#f5f5f5"}; padding: 10px; border-radius: 5px;">{code}</pre>'
        
        # Replace ```language\ncode``` blocks
        pattern = r'```(\w+)?\n(.*?)```'
        text = re.sub(pattern, replace_code_block, text, flags=re.DOTALL)
        
        return text

    def send_message(self, default_prompt=None):
        """Send a message to the AI for analysis"""
        question = default_prompt if default_prompt else self.input_field.text().strip()
        if not question:
            return
            
        # Add user question to chat history
        self.chat_history.append(f'<b>You:</b> {question}<br>')
        
        # Clear input field
        self.input_field.clear()
        
        # Add "AI is thinking..." message
        self.chat_history.append('<i>AI is analyzing the image...</i><br>')
        
        # Send to AI for analysis
        try:
            self.app.current_provider.analyze_image(self.screenshot_path, question)
        except Exception as e:
            self.add_ai_response(f"Error analyzing image: {str(e)}")
        
    def add_ai_response(self, response):
        """Add AI response to chat history with syntax highlighting"""
        # Remove the "AI is thinking..." message
        current_text = self.chat_history.toHtml()
        current_text = current_text.replace('<i>AI is analyzing the image...</i><br>', '')
        self.chat_history.setHtml(current_text)
        
        # Format the response with syntax highlighting for code blocks
        formatted_response = self.format_code_blocks(response)
        
        # Add the AI response
        self.chat_history.append(f'<b>AI:</b> {formatted_response}<br>')
        
        # Scroll to bottom
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
