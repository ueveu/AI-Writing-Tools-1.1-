from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
import os
import re
from .UIUtils import ThemeBackground, colorMode
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

class ImageAnalysisWindow(QtWidgets.QMainWindow):
    def __init__(self, app, screenshot_path):
        super().__init__()
        self.app = app
        self.screenshot_path = screenshot_path
        
        # Initialize syntax highlighting formatter with custom styles
        style = 'monokai' if colorMode == 'dark' else 'default'
        self.formatter = HtmlFormatter(
            style=style,
            cssclass='highlight',
            noclasses=True,
            linenos=False,
            prestyles='border-radius: 5px; padding: 15px; margin: 10px 0;'
        )
        
        self.init_ui()

    def init_ui(self):
        # Use native window frame
        self.setWindowTitle('Image Analysis')
        self.setWindowFlags(QtCore.Qt.Window)  # Use native window frame
        self.setMinimumSize(1000, 600)

        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Main layout for central widget
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content container
        content_container = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout(content_container)
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(20)

        # Left side - Image display
        image_frame = QtWidgets.QFrame()
        image_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#222' if colorMode == 'dark' else '#fff'};
                border: 1px solid {'#444' if colorMode == 'dark' else '#ddd'};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        image_layout = QtWidgets.QVBoxLayout(image_frame)
        
        # Load and display the image
        pixmap = QtGui.QPixmap(self.screenshot_path)
        scaled_pixmap = pixmap.scaled(450, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.image_label = QtWidgets.QLabel()
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_label)
        
        content_layout.addWidget(image_frame)
        
        # Right side - Chat interface
        chat_frame = QtWidgets.QFrame()
        chat_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#222' if colorMode == 'dark' else '#fff'};
                border: 1px solid {'#444' if colorMode == 'dark' else '#ddd'};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        chat_layout = QtWidgets.QVBoxLayout(chat_frame)
        
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
        chat_layout.addWidget(self.chat_history)
        
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
        
        chat_layout.addWidget(input_frame)
        content_layout.addWidget(chat_frame, stretch=1)

        main_layout.addWidget(content_container)

        # Set window background color
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {'#1e1e1e' if colorMode == 'dark' else '#f0f0f0'};
            }}
        """)

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

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if click is in resize area (window edges)
            edge_size = 8
            pos = event.position()
            x, y = pos.x(), pos.y()
            width, height = self.width(), self.height()
            
            # Determine which edge was clicked
            left_edge = x <= edge_size
            right_edge = width - edge_size <= x <= width
            top_edge = y <= edge_size
            bottom_edge = height - edge_size <= y <= height
            
            if any([left_edge, right_edge, top_edge, bottom_edge]):
                self.resizing = True
                self.resize_edge = (left_edge, right_edge, top_edge, bottom_edge)
                self.resize_start_geometry = self.geometry()
                self.resize_cursor_start = event.globalPosition()
                event.accept()
            else:
                # Handle window dragging
                self.dragging = True
                self.drag_position = event.globalPosition() - self.frameGeometry().topLeft()
                event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        if self.resizing and event.buttons() == Qt.LeftButton:
            # Handle resizing
            delta = event.globalPosition() - self.resize_cursor_start
            new_geometry = self.resize_start_geometry
            left_edge, right_edge, top_edge, bottom_edge = self.resize_edge
            
            if left_edge:
                new_geometry.setLeft(new_geometry.left() + delta.x())
            if right_edge:
                new_geometry.setRight(new_geometry.right() + delta.x())
            if top_edge:
                new_geometry.setTop(new_geometry.top() + delta.y())
            if bottom_edge:
                new_geometry.setBottom(new_geometry.bottom() + delta.y())
                
            # Ensure minimum size is maintained
            if new_geometry.width() >= self.minimumWidth() and new_geometry.height() >= self.minimumHeight():
                self.setGeometry(new_geometry)
                
        elif self.dragging and event.buttons() == Qt.LeftButton:
            # Handle window dragging
            self.move(event.globalPosition().toPoint() - self.drag_position.toPoint())
            event.accept()
        else:
            # Update cursor based on mouse position
            self.update_cursor(event.position())

    def update_cursor(self, pos):
        edge_size = 8
        x, y = pos.x(), pos.y()
        width, height = self.width(), self.height()
        
        left_edge = x <= edge_size
        right_edge = width - edge_size <= x <= width
        top_edge = y <= edge_size
        bottom_edge = height - edge_size <= y <= height
        
        if (top_edge and left_edge) or (bottom_edge and right_edge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif (top_edge and right_edge) or (bottom_edge and left_edge):
            self.setCursor(Qt.SizeBDiagCursor)
        elif left_edge or right_edge:
            self.setCursor(Qt.SizeHorCursor)
        elif top_edge or bottom_edge:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
