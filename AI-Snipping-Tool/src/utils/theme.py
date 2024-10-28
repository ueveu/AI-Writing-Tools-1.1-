import darkdetect
from PySide6 import QtWidgets, QtGui, QtCore

def get_color_mode():
    return 'dark' if darkdetect.isDark() else 'light'

class ThemeManager:
    @staticmethod
    def apply_theme(widget):
        color_mode = get_color_mode()
        if color_mode == 'dark':
            widget.setStyleSheet("""
                QWidget {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
            """)
        else:
            widget.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
            """)
