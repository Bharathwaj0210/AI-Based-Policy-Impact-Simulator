import os
import google.generativeai as genai
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

class GeminiAIService:
    """
    Service for interacting with Google Gemini API for scenario generation and explanations.
    """
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.model = None
            return
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash-latest")

    def explain_prediction(self, policy_type, data_summary, prediction_results):
        if not self.model:
            return "⚠️ Gemini API key not found in .env. Please configure GEMINI_API_KEY."

        try:
            prompt = f"""
            You are an expert AI Policy Analyst.
            
            Policy Context: {policy_type}
            Data Summary: {data_summary}
            Prediction Results: {prediction_results}
            
            Please provide a structured explanation:
            1. Risk Interpretation: What do these numbers mean for the users/employees?
            2. Policy Implication: How should the organization react?
            3. Actionable Suggestions: Give 3 clear next steps.
            
            Keep the response concise and professional.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Error generating explanation: {str(e)}"

    def generate_scenario(self, policy_type, scenario_type):
        if not self.model:
            return "⚠️ Gemini API key missing."
            
        try:
            prompt = f"As an AI Policy consultant, describe a '{scenario_type}' scenario for a '{policy_type}' policy. What are the key drivers and potential outcomes?"
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Error generating scenario: {str(e)}"
