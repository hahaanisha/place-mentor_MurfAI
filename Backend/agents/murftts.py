# murf_tts.py
import requests

class MurfTTS:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.murf.ai/v1/speech/generate"

    def generate_audio(self, text, voice_id="Matthew", model="FALCON", locale="en-US"):
        """
        Send TTS request to Murf.ai with provided text.
        Returns raw audio bytes.
        """
        payload = {
            "text": text,
            "voiceId": voice_id
        }

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(self.url, json=payload, headers=headers)

        if response.status_code != 200:
            print("Error:", response.text)
            return None

        return response.content
