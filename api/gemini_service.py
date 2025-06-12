import os
from google.generativeai import GenerativeModel
from datetime import datetime
from ..utils.config import Config

class GeminiService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model = GenerativeModel('gemini-2.0-flash') if self.api_key else None
    
    def gerar_relatorio(self, prompt):
        if not self.model:
            raise Exception("API key do Gemini não configurada")
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Erro ao gerar relatório com Gemini: {str(e)}")
