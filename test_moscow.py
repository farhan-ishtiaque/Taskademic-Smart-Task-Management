#!/usr/bin/env python
"""
Test script for the new MoSCoW Priority Planner
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

from priority_analyzer.services import MoSCoWPriorityPlanner


def test_moscow_planner():
    """Test the MoSCoW planner with sample data"""
    
    planner = MoSCoWPriorityPlanner()
    
    # Test data - various types of academic tasks
    now = datetime.now()
    test_tasks = {
        'now': now.isoformat(),
        'timezone': 'UTC',
        'tasks': [
            {
                'id': 't1',
                'title': 'Final exam: Algorithms',
                'description': 'covers DP and graphs',
                'due_at': (now + timedelta(days=2)).isoformat(),
                'estimated_size': 'large',
                'course_weight': 0.5
            },
            {
                'id': 't2', 
                'title': 'Homework 3: Calculus',
                'description': 'Integration problems',
                'due_at': (now + timedelta(days=2)).isoformat(),  # Changed to 2 days to test that it's not Must anymore
            },
            {
                'id': 't3',
                'title': 'Study notes for Physics',
                'description': 'Review quantum mechanics',
                'due_at': (now + timedelta(days=10)).isoformat(),
            },
            {
                'id': 't4',
                'title': 'Research paper: Machine Learning',
                'description': 'Deep learning applications',
                'due_at': (now + timedelta(days=2)).isoformat(),  # Changed to 2 days to test new rule
                'estimated_size': 'large'
            },
            {
                'id': 't5',
                'title': 'Grocery shopping',
                'description': 'Weekly groceries',
                'due_at': (now + timedelta(days=3)).isoformat(),
            },
            {
                'id': 't6',
                'title': 'Quiz: Chemistry',
                'description': 'Organic chemistry quiz',
                'due_at': (now - timedelta(days=1)).isoformat(),  # Overdue
            }
        ]
    }
    
    print("🎯 Testing MoSCoW Priority Planner")
    print("=" * 50)
    
    # Analyze tasks
    result = planner.analyze_tasks(test_tasks)
    
    # Print results
    print(f"Analysis generated at: {result['generated_at']}")
    print()
    
    # Print buckets
    for bucket_name, tasks in result['buckets'].items():
        count = len(tasks)
        print(f"📋 {bucket_name.upper()} ({count} tasks):")
        
        if tasks:
            for task in tasks:
                print(f"  • {task['title']} (Score: {task['score']}, Due in: {task['due_in_days']} days)")
        else:
            print("  (No tasks)")
        print()
    
    # Print decision log
    print("🔍 Decision Log:")
    print("-" * 30)
    for log in result['decision_log']:
        print(f"Task: {log['id']} - {test_tasks['tasks'][int(log['id'][1:])-1]['title']}")
        print(f"  Type: {log['type']} | Importance: {log['importance']} | Urgency: {log['urgency']}")
        print(f"  Score: {log['score']} | Due in: {log['due_in_days']} days")
        print(f"  Rule: {log['matched_rule']}")
        print(f"  Final: {log['final'].upper()}")
        print()
    
    # Test edge cases
    print("🧪 Testing Edge Cases:")
    print("-" * 30)
    
    # Test with no due date
    edge_test = {
        'now': now.isoformat(),
        'timezone': 'UTC',
        'tasks': [
            {
                'id': 'e1',
                'title': 'Learn Python',
                'description': 'Self-study',
                'due_at': None,
            }
        ]
    }
    
    edge_result = planner.analyze_tasks(edge_test)
    edge_task = edge_result['decision_log'][0]
    print(f"No due date task: {edge_task['final']} (Score: {edge_task['score']})")
    
    # Test keyword matching
    test_keywords = [
        'Final project submission',
        'Weekly assignment',
        'Practice exercises',
        'Movie night'
    ]
    
    print("\n🔤 Keyword Classification Test:")
    for title in test_keywords:
        task_type = planner.classify_task_type(title)
        print(f"  '{title}' → {task_type}")
    
    print("\n✅ Test completed!")


if __name__ == '__main__':
    test_moscow_planner()
