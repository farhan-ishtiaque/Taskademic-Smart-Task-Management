from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .services import MoSCoWPriorityPlanner

@csrf_exempt
@require_http_methods(["POST"])
def analyze_priority(request):
    """API endpoint to analyze task priority using MoSCoW planner"""
    try:
        data = json.loads(request.body)
        task_name = data.get('task_name', '')
        task_description = data.get('task_description', '')
        due_date = data.get('due_date')  # Optional: ISO format string
        
        if not task_name:
            return JsonResponse({
                'error': 'Task name is required'
            }, status=400)
        
        # Create task data for MoSCoW analysis
        tasks_data = {
            'now': timezone.now().isoformat(),
            'timezone': 'UTC',
            'tasks': [{
                'id': 'temp_task',
                'title': task_name,
                'description': task_description,
                'due_at': due_date,
            }]
        }
        
        planner = MoSCoWPriorityPlanner()
        result = planner.analyze_tasks(tasks_data)
        
        # Get the analysis for our task
        if result['decision_log']:
            analysis = result['decision_log'][0]
            return JsonResponse({
                'priority': analysis['final'],
                'score': analysis['score'],
                'task_type': analysis['type'],
                'reasoning': analysis['matched_rule'],
                'importance': analysis['importance'],
                'urgency': analysis['urgency'],
                'due_in_days': analysis['due_in_days']
            })
        else:
            return JsonResponse({
                'priority': 'should',
                'score': 30,
                'task_type': 'Regular coursework',
                'reasoning': 'Default classification'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
