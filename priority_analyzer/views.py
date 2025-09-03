from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .services import DeepSeekPriorityAnalyzer

@csrf_exempt
@require_http_methods(["POST"])
def analyze_priority(request):
    """API endpoint to analyze task priority"""
    try:
        data = json.loads(request.body)
        task_name = data.get('task_name', '')
        task_description = data.get('task_description', '')
        
        if not task_name:
            return JsonResponse({
                'error': 'Task name is required'
            }, status=400)
            
        analyzer = DeepSeekPriorityAnalyzer()
        priority = analyzer.analyze_priority(task_name, task_description)
        
        return JsonResponse({
            'priority': priority
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
