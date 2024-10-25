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

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        
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
            
            # Draw border around selection without extending outside the selection area
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            pen = QtGui.QPen(QtGui.QColor(0, 255, 0), 1)  # Reduced pen width to 1
            painter.setPen(pen)
            
            # Draw the border inside the selection area
            painter.drawRect(rect.adjusted(0, 0, -1, -1))  # Adjust by -1 to keep border inside

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
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

    def mouseReleaseEvent(self, event):
        if self.is_selecting:
            # Ensure we have a valid selection
            if self.begin and self.end and self.begin != self.end:
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

            # Adjust coordinates relative to the primary monitor
            x1 += self.monitor["left"]
            y1 += self.monitor["top"]
            
            # Capture the selected region
            with mss.mss() as sct:
                region = {
                    'top': y1,
                    'left': x1,
                    'width': width,
                    'height': height
                }
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
