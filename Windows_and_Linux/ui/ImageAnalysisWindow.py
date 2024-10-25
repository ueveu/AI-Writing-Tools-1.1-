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
        
        # Initialize syntax highlighting formatter with improved styles
        style = 'monokai' if colorMode == 'dark' else 'default'
        background_color = '#1e1e1e' if colorMode == 'dark' else '#f8f8f8'
        self.formatter = HtmlFormatter(
            style=style,
            cssclass='highlight',
            noclasses=True,
            linenos=True,  # Enable line numbers
            linenostart=1,
            lineanchors='line',
            linespans='line',
            prestyles=f"""
                border-radius: 8px;
                padding: 16px;
                margin: 10px 0;
                background-color: {background_color};
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
                overflow-x: auto;
            """
        )
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Image Analysis')
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setMinimumSize(1000, 600)  # Increased width for better readability

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Theme background
        self.background = ThemeBackground(self, self.app.config.get('theme', 'gradient'), is_popup=True)
        main_layout.addWidget(self.background)

        # Title bar
        title_bar = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Image Analysis")
        title_label.setStyleSheet(f"""
            color: {'#fff' if colorMode == 'dark' else '#333'};
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        """)
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        
        # Close button
        close_button = QtWidgets.QPushButton("×")
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-size: 20px;
                border: none;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {'#ff4444' if colorMode == 'dark' else '#ffdddd'};
                border-radius: 5px;
            }}
        """)
        close_button.clicked.connect(self.close)
        title_bar.addWidget(close_button)

        # Content layout
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(20)

        # Left side - Image display
        image_widget = QtWidgets.QWidget()
        image_layout = QtWidgets.QVBoxLayout(image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        # Image frame
        image_frame = QtWidgets.QFrame()
        image_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#222' if colorMode == 'dark' else '#fff'};
                border: 1px solid {'#444' if colorMode == 'dark' else '#ddd'};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        image_frame_layout = QtWidgets.QVBoxLayout(image_frame)
        
        # Load and display the image
        pixmap = QtGui.QPixmap(self.screenshot_path)
        scaled_pixmap = pixmap.scaled(450, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        image_label = QtWidgets.QLabel()
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        image_frame_layout.addWidget(image_label)
        
        image_layout.addWidget(image_frame)
        content_layout.addWidget(image_widget)
        
        # Right side - Chat interface
        chat_widget = QtWidgets.QWidget()
        chat_layout = QtWidgets.QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        # Chat frame
        chat_frame = QtWidgets.QFrame()
        chat_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#222' if colorMode == 'dark' else '#fff'};
                border: 1px solid {'#444' if colorMode == 'dark' else '#ddd'};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        chat_frame_layout = QtWidgets.QVBoxLayout(chat_frame)
        
        # Chat history
        self.chat_history = QtWidgets.QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {'#fff' if colorMode == 'dark' else '#000'};
                border: none;
                font-family: "Segoe UI", "Arial", sans-serif;
                font-size: 14px;
                selection-background-color: {'#444' if colorMode == 'dark' else '#cce8ff'};
            }}
        """)
        chat_frame_layout.addWidget(self.chat_history)
        
        # Input area
        input_frame = QtWidgets.QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#333' if colorMode == 'dark' else '#f5f5f5'};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        input_layout = QtWidgets.QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Ask about the image...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {'#444' if colorMode == 'dark' else '#fff'};
                color: {'#fff' if colorMode == 'dark' else '#000'};
                border: 1px solid {'#555' if colorMode == 'dark' else '#ddd'};
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {'#666' if colorMode == 'dark' else '#999'};
            }}
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        send_button = QtWidgets.QPushButton("Send")
        send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#2e7d32' if colorMode == 'dark' else '#4CAF50'};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {'#1b5e20' if colorMode == 'dark' else '#45a049'};
            }}
            QPushButton:pressed {{
                background-color: {'#194d19' if colorMode == 'dark' else '#3d8b40'};
            }}
        """)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        chat_frame_layout.addWidget(input_frame)
        chat_layout.addWidget(chat_frame)
        content_layout.addWidget(chat_widget, stretch=1)  # Give chat widget more space

        # Add layouts to background
        main_content = QtWidgets.QVBoxLayout(self.background)
        main_content.addLayout(title_bar)
        main_content.addLayout(content_layout)

    def format_code_blocks(self, text):
        """Format code blocks with enhanced syntax highlighting"""
        def replace_code_block(match):
            code = match.group(2)
            lang = match.group(1) if match.group(1) else ''
            
            try:
                if lang:
                    lexer = get_lexer_by_name(lang)
                else:
                    # Try to guess the language, default to python if unsure
                    try:
                        lexer = guess_lexer(code)
                    except ClassNotFound:
                        lexer = get_lexer_by_name('python')
                
                # Add custom CSS wrapper
                highlighted = highlight(code, lexer, self.formatter)
                background_color = '#1e1e1e' if colorMode == 'dark' else '#f8f8f8'
                border_color = '#333' if colorMode == 'dark' else '#ddd'
                
                return f"""
                    <div style="
                        background-color: {background_color};
                        border: 1px solid {border_color};
                        border-radius: 8px;
                        margin: 10px 0;
                        overflow: hidden;
                    ">
                        <div style="
                            padding: 8px 16px;
                            background-color: {'#252525' if colorMode == 'dark' else '#f1f1f1'};
                            border-bottom: 1px solid {border_color};
                            font-family: 'Segoe UI', 'Arial', sans-serif;
                            font-size: 12px;
                            color: {'#ccc' if colorMode == 'dark' else '#666'};
                        ">
                            {lang.upper() if lang else 'CODE'}
                        </div>
                        <div style="padding: 0;">
                            {highlighted}
                        </div>
                    </div>
                """
            except ClassNotFound:
                # If language detection fails, create a basic code block
                background_color = '#1e1e1e' if colorMode == 'dark' else '#f8f8f8'
                border_color = '#333' if colorMode == 'dark' else '#ddd'
                return f"""
                    <div style="
                        background-color: {background_color};
                        border: 1px solid {border_color};
                        border-radius: 8px;
                        padding: 16px;
                        margin: 10px 0;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 13px;
                        line-height: 1.4;
                        white-space: pre;
                        overflow-x: auto;
                        color: {'#fff' if colorMode == 'dark' else '#000'};
                    ">
                        {code}
                    </div>
                """
        
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
        """Add AI response to chat history with enhanced syntax highlighting"""
        # Remove the "AI is thinking..." message
        current_text = self.chat_history.toHtml()
        current_text = current_text.replace('<i>AI is analyzing the image...</i><br>', '')
        self.chat_history.setHtml(current_text)
        
        # Format the response with syntax highlighting for code blocks
        formatted_response = self.format_code_blocks(response)
        
        # Add the AI response with proper spacing
        self.chat_history.append(f"""
            <div style="margin-bottom: 16px;">
                <b style="color: {'#4CAF50' if colorMode == 'dark' else '#2E7D32'};">AI:</b>
                <div style="margin-top: 8px;">
                    {formatted_response}
                </div>
            </div>
        """)
        
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
