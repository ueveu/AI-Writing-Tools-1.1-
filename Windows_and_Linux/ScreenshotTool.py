import os
import sys
from datetime import datetime
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
import mss
import mss.tools

class ScreenshotTool(QtWidgets.QWidget):
    screenshot_taken = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.is_selecting = False
        
        # Take initial screenshot of the entire screen
        with mss.mss() as sct:
            # Get the primary monitor
            self.monitor = sct.monitors[1]  # Primary monitor
            self.screen_shot = sct.grab(self.monitor)
            
            # Convert to QPixmap for display
            img = QtGui.QImage(bytes(self.screen_shot.rgb), 
                              self.screen_shot.width, 
                              self.screen_shot.height,
                              self.screen_shot.width * 3,
                              QtGui.QImage.Format_RGB888)
            self.background = QtGui.QPixmap.fromImage(img)
        
        # Set up the window to cover the entire screen
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(self.monitor["left"], self.monitor["top"],
                         self.monitor["width"], self.monitor["height"])
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        # Initialize size label
        self.size_label = QtWidgets.QLabel(self)
        self.size_label.setStyleSheet("""
            QLabel {
                background-color: #2e2e2e;
                color: white;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
        """)
        self.size_label.hide()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Draw the screenshot as background
        painter.drawPixmap(self.rect(), self.background)
        
        # Draw semi-transparent overlay
        overlay = QtGui.QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), overlay)

        if self.is_selecting and not self.begin.isNull() and not self.end.isNull():
            rect = QtCore.QRect(self.begin, self.end).normalized()
            
            # Clear the selection area
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            painter.eraseRect(rect)
            
            # Draw border around selection
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            
            # Draw the outer glow effect
            glow_color = QtGui.QColor(0, 255, 0, 40)
            for i in range(3):
                pen = QtGui.QPen(glow_color, i + 1)
                painter.setPen(pen)
                painter.drawRect(rect.adjusted(-i, -i, i, i))
            
            # Draw the main border
            pen = QtGui.QPen(QtGui.QColor(0, 255, 0), 1.5)
            painter.setPen(pen)
            painter.drawRect(rect)
            
            # Draw corner handles
            handle_size = 4
            handle_color = QtGui.QColor(0, 255, 0)
            painter.setPen(QtGui.QPen(handle_color, 1))
            painter.setBrush(QtGui.QBrush(handle_color))
            
            # Draw handles at each corner
            corners = [
                rect.topLeft(), rect.topRight(),
                rect.bottomLeft(), rect.bottomRight()
            ]
            for corner in corners:
                painter.drawRect(QtCore.QRect(
                    corner.x() - handle_size, 
                    corner.y() - handle_size,
                    handle_size * 2, 
                    handle_size * 2
                ))
            
            # Update size label
            size_text = f"{rect.width()} × {rect.height()}px"
            self.size_label.setText(size_text)
            
            # Position the label
            label_x = rect.center().x() - self.size_label.width() // 2
            label_y = rect.top() - 30
            if label_y < 0:
                label_y = rect.bottom() + 10
            self.size_label.move(label_x, label_y)
            self.size_label.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.is_selecting and self.begin != self.end:
                self.capture_screenshot()
                self.close()

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.is_selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end = event.pos()
            self.update()
            
            # Update size label position
            rect = QtCore.QRect(self.begin, self.end).normalized()
            size_text = f"{rect.width()} × {rect.height()}px"
            self.size_label.setText(size_text)
            
            label_x = rect.center().x() - self.size_label.width() // 2
            label_y = rect.top() - 30
            if label_y < 0:
                label_y = rect.bottom() + 10
            self.size_label.move(label_x, label_y)
            self.size_label.show()

    def mouseReleaseEvent(self, event):
        if self.is_selecting:
            # Ensure we have a valid selection
            if self.begin != self.end:
                self.capture_screenshot()
            self.close()

    def capture_screenshot(self):
        if self.begin and self.end:
            rect = QtCore.QRect(self.begin, self.end).normalized()
            x1, y1 = rect.left(), rect.top()
            x2, y2 = rect.right(), rect.bottom()
            width = x2 - x1
            height = y2 - y1
            
            if width <= 0 or height <= 0:
                return

            # Take a new clean screenshot without any overlay or selection border
            with mss.mss() as sct:
                # Adjust coordinates relative to the primary monitor
                x1 += self.monitor["left"]
                y1 += self.monitor["top"]
                
                region = {
                    'top': y1,
                    'left': x1,
                    'width': width,
                    'height': height,
                    'mon': 1  # Ensure we're using the primary monitor
                }
                
                # Capture without any UI elements
                self.hide()  # Hide the selection UI
                QtCore.QTimer.singleShot(50, lambda: self._finish_capture(region))  # Wait for UI to hide

    def _finish_capture(self, region):
        """Helper method to finish the capture after UI is hidden"""
        try:
            with mss.mss() as sct:
                screenshot = sct.grab(region)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'screenshot_{timestamp}.png'
                
                # Save to Documents/WritingTools/screenshots
                docs_path = os.path.join(os.path.expanduser('~'), 'Documents')
                save_path = os.path.join(docs_path, 'WritingTools', 'screenshots')
                os.makedirs(save_path, exist_ok=True)
                
                full_path = os.path.join(save_path, filename)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=full_path)
                
                self.screenshot_taken.emit(full_path)
        finally:
            self.close()
