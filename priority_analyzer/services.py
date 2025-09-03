import os
import requests
from django.conf import settings

class DeepSeekPriorityAnalyzer:
    """Service class to analyze task priority using DeepSeek API"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = "https://api.deepseek.ai/v1/chat/completions"
    
    def analyze_priority(self, task_name, task_description):
        """
        Analyze task priority using DeepSeek API
        Returns one of: 'must', 'should', 'could', 'wont'
        """
        # Craft an expert prompt for the model
        prompt = f"""You are an academic task prioritizer. Classify this task using MoSCoW priorities based ONLY on the task name and description provided.

CLASSIFICATION RULES (Follow these EXACTLY):

MUST have - Major academic deliverables (respond with "must"):
- Research paper, Term paper, Final project, Thesis, Dissertation
- Midterm exam, Final exam, Major exam
- Capstone project, Senior project
- Major presentation, Defense

SHOULD have - Regular coursework (respond with "should"):
- Homework, Assignment, Lab report, Problem set
- Quiz, Weekly quiz, Chapter exercises
- Discussion post, Forum participation
- Regular presentation, Class presentation

COULD have - Supplementary activities (respond with "could"):
- Learn [topic], Study [topic], Practice [skill]
- Review notes, Study notes, Flashcards
- Extra credit, Bonus assignment
- Supplementary reading, Optional exercises

WON'T have - Non-academic tasks (respond with "wont"):
- Cooking, Shopping, Personal tasks
- Entertainment, Hobbies
- Unrelated activities

Task to classify:
Name: "{task_name}"
Description: "{task_description}"

Look at the task name first. If it contains keywords like "research paper", "final project", "thesis", "exam" - classify as MUST.
If it contains "homework", "assignment", "lab" - classify as SHOULD.
If it contains "learn", "study", "practice" - classify as COULD.
If it's not academic - classify as WON'T.

Respond with ONLY one word: must, should, could, or wont"""

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",  # Replace with actual model name
                    "messages": [
                        {"role": "system", "content": "You are an expert project manager skilled in MoSCoW prioritization."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,  # Lower temperature for more consistent outputs
                    "max_tokens": 10  # We only need a single word response
                }
            )
            
            if response.status_code == 200:
                priority = response.json()['choices'][0]['message']['content'].strip().lower()
                # Validate the response
                if priority in ['must', 'should', 'could', 'wont']:
                    return priority
                
            # If API fails, use keyword-based fallback classification
            return self._fallback_classification(task_name, task_description)
            
        except Exception as e:
            # If API error, use keyword-based fallback
            return self._fallback_classification(task_name, task_description)
    
    def _fallback_classification(self, task_name, task_description):
        """Fallback classification based on keywords"""
        text = f"{task_name} {task_description}".lower()
        
        # MUST have keywords
        must_keywords = ['research paper', 'final project', 'thesis', 'dissertation', 
                        'midterm exam', 'final exam', 'major exam', 'capstone', 'defense']
        
        # SHOULD have keywords  
        should_keywords = ['homework', 'assignment', 'lab report', 'quiz', 
                          'discussion post', 'presentation', 'problem set']
        
        # COULD have keywords
        could_keywords = ['learn', 'study', 'practice', 'review', 'notes', 
                         'flashcard', 'extra credit', 'bonus', 'optional']
        
        # Check for MUST keywords first
        for keyword in must_keywords:
            if keyword in text:
                return 'must'
                
        # Check for SHOULD keywords
        for keyword in should_keywords:
            if keyword in text:
                return 'should'
                
        # Check for COULD keywords
        for keyword in could_keywords:
            if keyword in text:
                return 'could'
                
        # Check if it's non-academic (WON'T)
        non_academic = ['cooking', 'shopping', 'personal', 'entertainment', 'hobby']
        for keyword in non_academic:
            if keyword in text:
                return 'wont'
        
        # Default to 'should' for unclassified academic tasks
        return 'should'
