import logging
import webbrowser
from abc import ABC, abstractmethod
from typing import List

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from openai import OpenAI
from PySide6 import QtWidgets
from PySide6.QtWidgets import QVBoxLayout

from ui.UIUtils import colorMode


class AIProviderSetting(ABC):
    def __init__(self, name: str, display_name: str = None, default_value: str = None, description: str = None):
        self.name = name
        self.display_name = display_name if display_name else name
        self.default_value = default_value if default_value else ""
        self.description = description if description else ""

    @abstractmethod
    def render_to_layout(self, layout: QVBoxLayout):
        pass

    @abstractmethod
    def set_value(self, value):
        pass

    @abstractmethod
    def get_value(self):
        pass

class TextSetting(AIProviderSetting):
    def __init__(self, name: str, display_name: str = None, default_value: str = None, description: str = None):
        super().__init__(name, display_name, default_value, description)

        self.internal_value = default_value
        self.input = None

    def render_to_layout(self, layout: QVBoxLayout):
        row_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(self.display_name)
        label.setStyleSheet(f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};")
        row_layout.addWidget(label)

        self.input = QtWidgets.QLineEdit(self.internal_value)
        self.input.setStyleSheet(f"""
            font-size: 16px;
            padding: 5px;
            background-color: {'#444' if colorMode == 'dark' else 'white'};
            color: {'#ffffff' if colorMode == 'dark' else '#000000'};
            border: 1px solid {'#666' if colorMode == 'dark' else '#ccc'};
        """)

        self.input.setPlaceholderText(self.description)

        row_layout.addWidget(self.input)
        layout.addLayout(row_layout)

    def set_value(self, value):
        self.internal_value = value

    def get_value(self):
        return self.input.text()


class AIProvider(ABC):
    # settings: List[AIProviderSetting] is a list of AIProviderSetting objects that define the settings of the AI provider.
    def __init__(self, app, provider_name: str, settings: List[AIProviderSetting], description: str = "An unfinished AI provider!", logo: str = "generic", button_text: str = "Go to URL", button_action: callable = None):
        self.provider_name = provider_name
        self.settings = settings
        self.app = app
        self.description = description if description else "An unfinished AI provider!"

        self.logo = logo
        self.button_text = button_text
        self.button_action = button_action

    @abstractmethod
    def get_response(self, system_instruction: str, prompt: str) -> str:
        """
        Pass a system instruction and a prompt to the AI provider and return the response.
        """
        pass

    def load_config(self, config: dict):
        """
        Load the configuration into this provider's memory.
        """
        for setting in self.settings:
            if setting.name in config:
                setattr(self, setting.name, config[setting.name])

                setting.set_value(config[setting.name])
            else:
                setattr(self, setting.name, setting.default_value)

        self.after_load()

    def save_config(self):
        """
        Save the provider's memory to the config, and then save the config to disk.
        """
        config = {}
        for setting in self.settings:
            config[setting.name] = setting.get_value()

        self.app.config["providers"][self.provider_name] = config
        self.app.save_config(self.app.config)

    @abstractmethod
    def after_load(self):
        """
        A method to be overridden by subclasses that is called after the settings have been loaded.
        """
        pass

    @abstractmethod
    def before_load(self):
        """
        A method to be overridden by subclasses that is called before the settings have been loaded.
        Useful for performing cleanup etc.
        """
        pass

    @abstractmethod
    def cancel(self):
        """
        Cancel the current request.
        """
        pass

    def analyze_image(self, messages):
        """
        Analyze an image using the OpenAI API
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",  # Make sure to use the vision model
                messages=messages,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error analyzing image: {str(e)}")
            raise

class Gemini15FlashProvider(AIProvider):

    def __init__(self, app):
        """
        Initialize the Gemini 1.5 Flash provider.
        """
        self.close_requested = False
        self.model = None

        settings = [
            TextSetting(name = "api_key", display_name = "API Key", description = "Paste your Gemini API key here"),
        ]
        super().__init__(app, "Gemini 1.5 Flash (Recommended)", settings, "• Gemini 1.5 Flash is a powerful AI model that has a free tier available.\n• Writing Tools needs an \"API key\" to connect to Gemini on your behalf.\n• Simply click Get API Key button below, copy your API key, and paste it below.\n• Note: With the free tier of the Gemini API, Google may anonymize & store the text that you send Writing Tools, for Gemini\'s improvement.", "gemini", "Get API Key", lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))

    def get_response(self, system_instruction: str, prompt: str):
        self.close_requested = False

        response = self.model.generate_content(
            contents=[system_instruction, prompt],
            stream=self.app.config.get("streaming", False)
        )

        # Check if the response was blocked
        if response.prompt_feedback.block_reason:
            logging.warning('Response was blocked due to safety settings')
            self.app.show_message_signal.emit('Content Blocked',
                                          'The generated content was blocked due to safety settings.')
            return

        try:
            for chunk in response:
                if self.close_requested:
                    break
                else:
                    # Strip any trailing newlines from chunks
                    self.app.output_ready_signal.emit(chunk.text.rstrip('\n'))
        except Exception as e:
            logging.error(f"Error while streaming: {e}")
            self.app.output_ready_signal.emit("An error occurred while streaming.")
        finally:
            self.close_requested = False
            self.app.replace_text(True)


    def after_load(self):
        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                max_output_tokens=1000,
                temperature=0.5
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

    def before_load(self):
        self.model = None

    def cancel(self):
        self.close_requested = True

    def analyze_image(self, screenshot_path, prompt):
        """
        Analyze an image using Gemini's vision capabilities
        """
        try:
            import PIL.Image
            
            # Load the image
            image = PIL.Image.open(screenshot_path)
            
            # Create the model response
            response = self.model.generate_content(
                [
                    prompt,
                    image
                ],
                stream=False  # Don't stream for image analysis
            )
            
            # Check if response was blocked
            if response.prompt_feedback.block_reason:
                raise Exception("Response was blocked due to safety settings")
                
            # Get the text response
            text_response = response.text
            
            # Find the ImageAnalysisWindow instance and update it
            for window in QtWidgets.QApplication.topLevelWidgets():
                if window.__class__.__name__ == 'ImageAnalysisWindow':
                    window.add_ai_response(text_response)
                    break
                    
        except Exception as e:
            logging.error(f"Error in Gemini image analysis: {str(e)}")
            for window in QtWidgets.QApplication.topLevelWidgets():
                if window.__class__.__name__ == 'ImageAnalysisWindow':
                    window.add_ai_response(f"Error analyzing image: {str(e)}")
                    break

class OpenAICompatibleProvider(AIProvider):
    def __init__(self, app):
        """
        Initialize the OpenAI-compatible provider.
        """
        self.close_requested = None
        self.client = None

        settings = [
            TextSetting(name = "api_key", display_name = "API Key", description = "API key for the OpenAI-compatible API."),
            TextSetting("api_base", "API Base URL", "https://api.openai.com/v1", "Eg. https://api.openai.com/v1"),
            TextSetting("api_organisation", "API Organisation", "", "Leave blank if not applicable."),
            TextSetting("api_project", "API Project", "", "Leave blank if not applicable."),
            TextSetting("api_model", "API Model", "gpt-4o-mini", "Eg. gpt-4o-mini"),
        ]

        super().__init__(app, "OpenAI Compatible (For Experts)", settings, "• Connect to ANY Open-AI Compatible API, such as OpenAI, Mistral AI, Anthropic, or locally hosted models via llama.cpp, KoboldCPP, TabbyAPI, vLLM, etc.\n• Note: You must adhere to the connected service's Terms of Service, and your text will be processed as per their Privacy Policies etc.", "openai", "Get OpenAI API Key", lambda: webbrowser.open("https://platform.openai.com/account/api-keys"))

    def get_response(self, system_instruction: str, prompt: str):
        self.close_requested = False
        streaming = self.app.config.get("streaming", False)

        response = self.client.chat.completions.create(
            model=self.api_model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            stream=streaming
        )

        if streaming:
            try:
                for chunk in response:
                    if self.close_requested:
                        break
                    else:
                        # Strip any trailing newlines from chunks
                        if chunk.choices[0].delta.content:
                            self.app.output_ready_signal.emit(chunk.choices[0].delta.content.rstrip('\n'))

            except Exception as e:
                logging.error(f"Error while streaming: {e}")
                self.app.output_ready_signal.emit("An error occurred while streaming.")

            finally:
                response.close()
                self.close_requested = False
                self.app.replace_text(True)

        else:
            # Strip any trailing newlines from the complete response
            self.app.output_ready_signal.emit(response.choices[0].message.content.strip())
            self.app.replace_text(True)

    def after_load(self):
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base, organization=self.api_organisation, project=self.api_project)

    def before_load(self):
        self.client = None

    def cancel(self):
        self.close_requested = True

    def analyze_image(self, screenshot_path, prompt):
        """
        Analyze an image using OpenAI's vision capabilities
        """
        try:
            import base64
            
            # Read and encode the image
            with open(screenshot_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create the API request
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Get the response text
            text_response = response.choices[0].message.content
            
            # Find the ImageAnalysisWindow instance and update it
            for window in QtWidgets.QApplication.topLevelWidgets():
                if window.__class__.__name__ == 'ImageAnalysisWindow':
                    window.add_ai_response(text_response)
                    break
                    
        except Exception as e:
            logging.error(f"Error in OpenAI image analysis: {str(e)}")
            for window in QtWidgets.QApplication.topLevelWidgets():
                if window.__class__.__name__ == 'ImageAnalysisWindow':
                    window.add_ai_response(f"Error analyzing image: {str(e)}")
                    break
