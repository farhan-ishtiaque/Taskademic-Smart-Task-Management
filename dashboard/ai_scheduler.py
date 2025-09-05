import json
import requests
import time
import random
import logging
from datetime import datetime, timedelta, time
from django.conf import settings
from django.utils import timezone
from .models import ScheduledTask, DailySchedule
from tasks.models import Task, TimeBlock
from priority_analyzer.signals import MoSCoWCacheService


class DeepSeekSchedulerService:
    """Service for AI-powered task scheduling using DeepSeek via OpenRouter API"""
    
    def __init__(self):
        # OpenRouter API configuration for DeepSeek
        self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "deepseek/deepseek-r1:free"
    
    def create_scheduling_prompt(self, user, target_date, available_time_blocks, moscow_tasks):
        """Create a detailed prompt for DeepSeek to schedule tasks optimally"""
        
        # Calculate total available time
        total_minutes = sum(self._calculate_duration(block) for block in available_time_blocks)
        
        prompt = f"""You are an expert academic productivity scheduler. Your task is to create an optimal daily schedule for a student.

**STUDENT CONTEXT:**
- Student: {user.first_name} {user.last_name}
- Target Date: {target_date.strftime('%A, %B %d, %Y')}
- Total Available Time: {total_minutes} minutes ({total_minutes/60:.1f} hours)

**AVAILABLE TIME BLOCKS:**
"""
        
        for block in available_time_blocks:
            duration = self._calculate_duration(block)
            prompt += f"- {block.start_time.strftime('%H:%M')}-{block.end_time.strftime('%H:%M')}: {duration} minutes\n"
        
        prompt += f"""
**TASKS TO SCHEDULE (Moscow Matrix Priority):**

MUST HAVE (Urgent & Important) - SCHEDULE ALL OF THESE:
"""
        must_tasks = moscow_tasks.get('must', [])
        if not must_tasks:
            prompt += "- No MUST tasks found\n"
        else:
            for task_data in must_tasks:
                task = Task.objects.get(id=task_data['id'])
                due_info = f"Due: {task.due_date.strftime('%m/%d/%Y')}" if task.due_date else "No deadline"
                days_until_due = task_data.get('due_in_days', 'N/A')
                prompt += f"- ID:{task.id} | {task.title}: {task.description or 'No description'} | {due_info} | Days until due: {days_until_due}\n"
        
        prompt += f"""
SHOULD HAVE (Important but less urgent):
"""
        should_tasks = moscow_tasks.get('should', [])
        if not should_tasks:
            prompt += "- No SHOULD tasks found\n"
        else:
            for task_data in should_tasks[:5]:  # Limit to top 5 should tasks
                task = Task.objects.get(id=task_data['id'])
                due_info = f"Due: {task.due_date.strftime('%m/%d/%Y')}" if task.due_date else "No deadline"
                days_until_due = task_data.get('due_in_days', 'N/A')
                prompt += f"- ID:{task.id} | {task.title}: {task.description or 'No description'} | {due_info} | Days until due: {days_until_due}\n"

        prompt += f"""
**TASK SUMMARY:**
- MUST HAVE tasks to schedule: {len(must_tasks)} (ALL must be scheduled)
- SHOULD HAVE tasks available: {len(should_tasks)} (schedule if time permits)
- Total available time: {total_minutes} minutes

**IMPORTANT**: You have {len(must_tasks)} MUST tasks that are critical. ALL {len(must_tasks)} MUST tasks must be scheduled before any SHOULD tasks.
"""
        
        prompt += f"""

**TASK DURATION ESTIMATION GUIDELINES:**
Use your knowledge to estimate realistic durations:
- Final exam preparation: 3-5 hours (split across sessions)
- Midterm preparation: 2-3 hours  
- Major research paper/project: 4-6 hours (split across multiple days)
- Regular homework/assignments: 45-90 minutes
- Lab reports: 1-2 hours
- Quiz preparation: 30-60 minutes
- Problem sets: 1-2 hours
- Presentations: 2-3 hours
- Reading assignments: 30-45 minutes per chapter
- Discussion posts: 15-30 minutes

**SCHEDULING RULES:**
1. **PRIORITY: Schedule ALL MUST HAVE tasks first** - these are urgent and critical, DO NOT skip any MUST tasks
2. **MUST tasks are mandatory** - If there are multiple MUST tasks, schedule ALL of them before any SHOULD tasks
3. **Use all available time efficiently** - Don't leave large gaps unused if there are tasks to schedule
4. **Use Pomodoro Technique**: Break long tasks into 25-minute focused sessions with 5-minute breaks
5. **For tasks >2 hours**: Use 52-minute work sessions with 17-minute breaks (52-17 technique)
6. **Account for breaks**: Include break time in your calculations
7. **Consider cognitive load**: Don't pack too many difficult tasks back-to-back
8. **Buffer time**: Leave 10-15 minutes buffer between different tasks
9. **Realistic expectations**: Don't over-schedule; better to complete fewer tasks well
10. **If you can't fit all MUST tasks**: Explain why in the summary and suggest what to do

**REQUIRED OUTPUT FORMAT:**
Return ONLY a valid JSON object with this exact structure:

{{
  "schedule": [
    {{
      "task_id": "12",
      "task_title": "Linear Algebra Homework",
      "time_block_start": "09:00",
      "time_block_end": "11:00", 
      "scheduled_start": "09:00",
      "scheduled_end": "10:30",
      "estimated_duration_minutes": 90,
      "pomodoro_sessions": 3,
      "break_minutes": 10,
      "reasoning": "High priority assignment due tomorrow. Scheduled in morning block when concentration is highest. 3 pomodoro sessions (25min each) with breaks.",
      "priority_score": 95
    }}
  ],
  "summary": {{
    "total_scheduled_minutes": 90,
    "total_break_minutes": 10,
    "tasks_scheduled": 1,
    "moscow_must_scheduled": 1,
    "moscow_should_scheduled": 0,
    "remaining_time_minutes": 330,
    "scheduling_strategy": "Prioritized MUST tasks first, used pomodoro technique for focus"
  }}
}}

**CRITICAL REQUIREMENTS:**
- task_id MUST match the ID from the task list above
- scheduled_start and scheduled_end MUST be within the available time blocks
- ALL MUST HAVE tasks MUST be scheduled unless physically impossible (explain why if not)
- Include realistic break time calculations
- Don't exceed available time blocks
- Focus on MUST tasks first, then SHOULD tasks if time permits
- Provide clear reasoning for each scheduling decision
- Use 24-hour time format (HH:MM)
- If you cannot schedule a MUST task, explain why in the summary

⚠️ **WARNING**: MUST tasks are critical academic deadlines. Not scheduling them could result in failed assignments or missed deadlines. Always prioritize fitting ALL MUST tasks first.

Schedule the tasks now:"""

        return prompt
    
    def call_deepseek_api_smart(self, prompt):
        """Make API call to DeepSeek via OpenRouter with minimal retries for rate limits"""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8000",  # OpenRouter requirement
            "X-Title": "TaskAdemic AI Scheduler"  # OpenRouter requirement
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent scheduling
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    raise ValueError("No JSON found in AI response")
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse AI response as JSON: {e}")
                
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Rate limit error
                # For rate limits, immediately fall back instead of retrying
                raise ValueError(f"API rate limit hit (429): {e}")
            else:
                # Other HTTP errors
                raise ValueError(f"API request failed: {e}")
        except requests.exceptions.RequestException as e:
            # Network errors
            raise ValueError(f"API request failed: {e}")

    def call_deepseek_api(self, prompt):
        """Make API call to DeepSeek via OpenRouter with rate limit handling"""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8000",  # OpenRouter requirement
            "X-Title": "TaskAdemic AI Scheduler"  # OpenRouter requirement
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent scheduling
            "max_tokens": 2000
        }
        
        # Retry logic with exponential backoff for rate limits
        max_retries = 3
        base_delay = 1  # Start with 1 second
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON in the response
                    start_idx = ai_response.find('{')
                    end_idx = ai_response.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = ai_response[start_idx:end_idx]
                        return json.loads(json_str)
                    else:
                        raise ValueError("No JSON found in AI response")
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse AI response as JSON: {e}")
                    
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:  # Rate limit error
                    if attempt < max_retries:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logging.warning(f"Rate limit hit, retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        logging.error("Max retries reached for rate limit, falling back to basic scheduling")
                        raise ValueError(f"API request failed after {max_retries} retries: {e}")
                else:
                    # Other HTTP errors, don't retry
                    raise ValueError(f"API request failed: {e}")
            except requests.exceptions.RequestException as e:
                # Network errors, don't retry
                raise ValueError(f"API request failed: {e}")
    
    def generate_daily_schedule(self, user, target_date):
        """Generate a complete daily schedule for the user with smart fallback"""
        
        # Get available time blocks for the target day
        # Convert target_date weekday to integer (0=Monday, 6=Sunday)
        day_number = target_date.weekday()  # Monday=0, Sunday=6
        
        available_blocks = TimeBlock.objects.filter(
            user=user,
            day_of_week=day_number,
            is_available=True
        ).order_by('start_time')
        
        if not available_blocks.exists():
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            raise ValueError(f"No available time blocks for {days[day_number]}")
        
        # Get Moscow Matrix analysis
        moscow_result = MoSCoWCacheService.get_moscow_analysis(user)
        
        # Try AI scheduling first, but use smart fallback for rate limits
        try:
            # Create AI prompt
            prompt = self.create_scheduling_prompt(user, target_date, available_blocks, moscow_result['buckets'])
            
            # Call DeepSeek API with reduced retries for rate limits
            ai_response = self.call_deepseek_api_smart(prompt)
            
            # Create daily schedule record
            daily_schedule = DailySchedule.objects.create(
                user=user,
                date=target_date,
                total_available_minutes=sum(self._calculate_duration(block) for block in available_blocks),
                total_scheduled_minutes=ai_response['summary']['total_scheduled_minutes'],
                total_break_minutes=ai_response['summary']['total_break_minutes'],
                tasks_count=ai_response['summary']['tasks_scheduled'],
                moscow_must_count=ai_response['summary']['moscow_must_scheduled'],
                moscow_should_count=ai_response['summary']['moscow_should_scheduled'],
                ai_prompt_used=prompt,
                ai_response=json.dumps(ai_response, indent=2)
            )
            
            # Create scheduled task records
            scheduled_tasks = []
            for schedule_item in ai_response['schedule']:
                # Find the appropriate time block
                start_time = datetime.strptime(schedule_item['scheduled_start'], '%H:%M').time()
                end_time = datetime.strptime(schedule_item['scheduled_end'], '%H:%M').time()
                
                # Find matching time block
                time_block = None
                for block in available_blocks:
                    if block.start_time <= start_time and block.end_time >= end_time:
                        time_block = block
                        break
                
                if time_block:
                    task = Task.objects.get(id=schedule_item['task_id'])
                    scheduled_task = ScheduledTask.objects.create(
                        user=user,
                        task=task,
                        time_block=time_block,
                        estimated_duration_minutes=schedule_item['estimated_duration_minutes'],
                        scheduled_date=target_date,
                        start_time=start_time,
                        end_time=end_time,
                        pomodoro_sessions=schedule_item.get('pomodoro_sessions', 1),
                        break_minutes=schedule_item.get('break_minutes', 5),
                        ai_reasoning=schedule_item['reasoning'],
                        priority_score=schedule_item['priority_score']
                    )
                    scheduled_tasks.append(scheduled_task)
            
            return daily_schedule, scheduled_tasks
            
        except ValueError as e:
            # If API fails (including rate limits), use intelligent fallback
            if "429" in str(e) or "rate limit" in str(e).lower():
                logging.warning(f"Rate limit hit, using intelligent fallback scheduling for {user.username}")
            else:
                logging.warning(f"AI scheduling failed ({str(e)}), using intelligent fallback for {user.username}")
            
            # Use the enhanced fallback scheduling
            fallback_result = self.get_fallback_schedule(user, target_date, available_blocks, moscow_result['buckets'])
            
            # Create daily schedule record with fallback data
            daily_schedule = DailySchedule.objects.create(
                user=user,
                date=target_date,
                total_available_minutes=sum(self._calculate_duration(block) for block in available_blocks),
                total_scheduled_minutes=fallback_result['summary']['total_scheduled_minutes'],
                total_break_minutes=fallback_result['summary']['total_break_minutes'],
                tasks_count=fallback_result['summary']['tasks_scheduled'],
                moscow_must_count=fallback_result['summary']['moscow_must_scheduled'],
                moscow_should_count=fallback_result['summary']['moscow_should_scheduled'],
                ai_prompt_used="Fallback scheduling due to API issues",
                ai_response=json.dumps(fallback_result, indent=2)
            )
            
            # Create scheduled task records from fallback
            scheduled_tasks = []
            for schedule_item in fallback_result['schedule']:
                start_time = datetime.strptime(schedule_item['scheduled_start'], '%H:%M').time()
                end_time = datetime.strptime(schedule_item['scheduled_end'], '%H:%M').time()
                
                # Find matching time block
                time_block = None
                for block in available_blocks:
                    if block.start_time <= start_time and block.end_time >= end_time:
                        time_block = block
                        break
                
                if time_block:
                    task = Task.objects.get(id=schedule_item['task_id'])
                    scheduled_task = ScheduledTask.objects.create(
                        user=user,
                        task=task,
                        time_block=time_block,
                        estimated_duration_minutes=schedule_item['estimated_duration_minutes'],
                        scheduled_date=target_date,
                        start_time=start_time,
                        end_time=end_time,
                        pomodoro_sessions=schedule_item.get('pomodoro_sessions', 1),
                        break_minutes=schedule_item.get('break_minutes', 5),
                        ai_reasoning=schedule_item['reasoning'],
                        priority_score=schedule_item['priority_score']
                    )
                    scheduled_tasks.append(scheduled_task)
            
            return daily_schedule, scheduled_tasks
    
    def _calculate_duration(self, time_block):
        """Calculate duration of a time block in minutes"""
        start_minutes = time_block.start_time.hour * 60 + time_block.start_time.minute
        end_minutes = time_block.end_time.hour * 60 + time_block.end_time.minute
        
        # Handle overnight time blocks
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60  # Add 24 hours
        
        return end_minutes - start_minutes
    
    def get_fallback_schedule(self, user, target_date, available_blocks, moscow_tasks):
        """Create a basic schedule if AI fails - prioritize ALL MUST tasks"""
        
        scheduled_tasks = []
        
        # Get all MUST tasks first
        must_tasks = moscow_tasks.get('must', [])
        should_tasks = moscow_tasks.get('should', [])
        
        # Sort blocks by start time
        sorted_blocks = sorted(available_blocks, key=lambda x: x.start_time)
        
        # Track available time in each block
        block_availability = {}
        for block in sorted_blocks:
            block_availability[block.id] = {
                'start_time': block.start_time,
                'end_time': block.end_time,
                'remaining_minutes': self._calculate_duration(block)
            }
        
        def schedule_task(task_data, priority_score, is_must=True):
            task = Task.objects.get(id=task_data['id'])
            
            # Smart duration estimation based on task content
            estimated_minutes = self._estimate_task_duration(task)
            
            # Find best fitting block
            for block_id, availability in block_availability.items():
                if availability['remaining_minutes'] >= estimated_minutes:
                    # Schedule the task
                    start_time = availability['start_time']
                    end_time = (datetime.combine(target_date, start_time) + 
                               timedelta(minutes=estimated_minutes)).time()
                    
                    scheduled_task = {
                        'task_id': task.id,
                        'task_title': task.title,
                        'time_block_start': start_time.strftime('%H:%M'),
                        'time_block_end': availability['end_time'].strftime('%H:%M'),
                        'scheduled_start': start_time.strftime('%H:%M'),
                        'scheduled_end': end_time.strftime('%H:%M'),
                        'estimated_duration_minutes': estimated_minutes,
                        'pomodoro_sessions': max(1, estimated_minutes // 25),
                        'break_minutes': 5 if estimated_minutes < 60 else 10,
                        'reasoning': f"{'Priority MUST task' if is_must else 'SHOULD task'}: {task.title}. Scheduled optimally with {max(1, estimated_minutes // 25)} Pomodoro sessions.",
                        'priority_score': priority_score
                    }
                    
                    scheduled_tasks.append(scheduled_task)
                    
                    # Update block availability
                    buffer_time = 10  # 10 minute buffer between tasks
                    used_time = estimated_minutes + buffer_time
                    availability['remaining_minutes'] -= used_time
                    
                    # Update start time for next task in this block
                    availability['start_time'] = (datetime.combine(target_date, start_time) + 
                                                 timedelta(minutes=used_time)).time()
                    
                    return True
            return False
        
        # Schedule ALL MUST tasks first
        must_scheduled = 0
        for task_data in must_tasks:
            if schedule_task(task_data, 95, is_must=True):
                must_scheduled += 1
        
        # Schedule SHOULD tasks if there's remaining time
        should_scheduled = 0
        for task_data in should_tasks[:5]:  # Limit to top 5 should tasks
            if schedule_task(task_data, 70, is_must=False):
                should_scheduled += 1
        
        # Calculate totals
        total_scheduled_minutes = sum(task['estimated_duration_minutes'] for task in scheduled_tasks)
        total_break_minutes = sum(task['break_minutes'] for task in scheduled_tasks)
        
        return {
            'schedule': scheduled_tasks,
            'summary': {
                'total_scheduled_minutes': total_scheduled_minutes,
                'total_break_minutes': total_break_minutes,
                'tasks_scheduled': len(scheduled_tasks),
                'moscow_must_scheduled': must_scheduled,
                'moscow_should_scheduled': should_scheduled,
                'remaining_time_minutes': sum(avail['remaining_minutes'] for avail in block_availability.values()),
                'scheduling_strategy': f"Fallback scheduling: Prioritized ALL {len(must_tasks)} MUST tasks, scheduled {must_scheduled}. Added {should_scheduled} SHOULD tasks."
            }
        }
    
    def _estimate_task_duration(self, task):
        """Smart duration estimation based on task content"""
        title_lower = task.title.lower()
        description_lower = (task.description or "").lower()
        combined_text = f"{title_lower} {description_lower}"
        
        # Exam and test preparation
        if any(word in combined_text for word in ['final exam', 'final test', 'midterm exam']):
            return 180  # 3 hours
        elif any(word in combined_text for word in ['exam', 'test', 'midterm']):
            return 120  # 2 hours
        elif 'quiz' in combined_text:
            return 45   # 45 minutes
        
        # Major assignments
        elif any(word in combined_text for word in ['research paper', 'term paper', 'thesis', 'project']):
            return 240  # 4 hours
        elif any(word in combined_text for word in ['presentation', 'lab report']):
            return 120  # 2 hours
        elif any(word in combined_text for word in ['assignment', 'homework', 'problem set']):
            return 90   # 1.5 hours
        
        # Study activities
        elif any(word in combined_text for word in ['study', 'review', 'practice']):
            return 75   # 1.25 hours
        elif any(word in combined_text for word in ['read', 'reading']):
            return 60   # 1 hour
        
        # Default based on task complexity
        else:
            # Estimate based on description length if available
            if task.description and len(task.description) > 100:
                return 120  # Complex task
            elif task.description and len(task.description) > 50:
                return 90   # Medium task
            else:
                return 60   # Simple task

    def _calculate_duration(self, time_block):
        """Calculate duration of a time block in minutes"""
        start_minutes = time_block.start_time.hour * 60 + time_block.start_time.minute
        end_minutes = time_block.end_time.hour * 60 + time_block.end_time.minute
        return end_minutes - start_minutes
