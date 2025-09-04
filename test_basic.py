#!/usr/bin/env python
"""
Simple test to verify the MoSCoW system is working
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskademic.settings')
django.setup()

try:
    from priority_analyzer.services import MoSCoWPriorityPlanner
    print("✅ MoSCoWPriorityPlanner imported successfully")
    
    planner = MoSCoWPriorityPlanner()
    print("✅ Planner instance created")
    
    # Test keyword classification
    test_titles = [
        "Final exam: Computer Science",
        "Homework assignment #3", 
        "Study for midterm",
        "Grocery shopping"
    ]
    
    print("\n🔍 Testing keyword classification:")
    for title in test_titles:
        task_type = planner.classify_task_type(title)
        print(f"  '{title}' → {task_type}")
    
    print("\n✅ Basic functionality test passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
