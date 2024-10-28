import sys
from PySide6 import QtWidgets
from screenshot_tool import ScreenshotTool
from image_analysis_window import ImageAnalysisWindow
import os
import json

class AISnippingTool:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.load_config()
        self.screenshot_tool = None
        self.image_analysis_window = None
        
    def load_config(self):
        config_path = os.path.join(os.path.expanduser('~'), '.ai-snipping-tool', 'config.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'theme': 'dark',
                'api_key': '',
                'provider': 'gemini'  # or 'openai'
            }
            self.save_config()
            
    def save_config(self):
        config_path = os.path.join(os.path.expanduser('~'), '.ai-snipping-tool', 'config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def start(self):
        self.screenshot_tool = ScreenshotTool()
        self.screenshot_tool.screenshot_taken.connect(self.handle_screenshot)
        self.screenshot_tool.show()
        return self.app.exec()

    def handle_screenshot(self, screenshot_path):
        self.image_analysis_window = ImageAnalysisWindow(self, screenshot_path)
        self.image_analysis_window.show()

if __name__ == '__main__':
    tool = AISnippingTool()
    sys.exit(tool.start())
