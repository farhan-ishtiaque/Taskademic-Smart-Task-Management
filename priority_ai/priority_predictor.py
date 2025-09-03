import os
import requests
import json
from typing import Tuple

class PriorityPredictor:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # Replace with actual DeepSeek API endpoint
        
    def predict_priority(self, task_name: str, task_description: str) -> Tuple[str, float]:
        """
        Predicts MoSCoW priority for a task using DeepSeek API.
        Returns: Tuple of (priority, confidence_score)
        """
        prompt = self._generate_prompt(task_name, task_description)
        
        try:
            response = self._call_deepseek_api(prompt)
            priority, confidence = self._parse_response(response)
            return priority, confidence
        except Exception as e:
            print(f"Error predicting priority: {e}")
            return 'should', 0.5  # Default fallback
    
    def _generate_prompt(self, task_name: str, task_description: str) -> str:
        """
        Generates an optimized prompt for DeepSeek API to analyze task priority.
        """
        return f"""Given this task, determine its MoSCoW priority (Must Have, Should Have, Could Have, Won't Have) based on:
1. Task urgency and importance
2. Impact on project success
3. Dependencies and blockers
4. Resource requirements
5. Time sensitivity

Task Name: {task_name}
Task Description: {task_description}

Analyze the task and respond in JSON format:
{{
    "priority": "must|should|could|wont",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Consider:
- "Must Have": Critical tasks that directly impact core functionality or project success
- "Should Have": Important but not critical tasks
- "Could Have": Desired features that can be postponed
- "Won't Have": Tasks that can be excluded from current scope

Focus on extracting key indicators of priority from the task name and description."""
    
    def _call_deepseek_api(self, prompt: str) -> dict:
        """
        Makes API call to DeepSeek with proper error handling.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",  # Replace with actual model name
            "messages": [
                {"role": "system", "content": "You are an expert project manager skilled at prioritizing tasks using the MoSCoW method."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3  # Lower temperature for more consistent results
        }
        
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def _parse_response(self, response: dict) -> Tuple[str, float]:
        """
        Parses API response to extract priority and confidence.
        """
        try:
            content = response['choices'][0]['message']['content']
            result = json.loads(content)
            return result['priority'], result['confidence']
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing API response: {e}")
            return 'should', 0.5  # Default fallback
