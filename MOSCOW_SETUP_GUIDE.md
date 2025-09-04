# MoSCoW Matrix Daily Refresh Setup

## Overview
The new MoSCoW Priority Planner automatically rebuilds the priority matrix when:
1. Tasks are created, edited, deleted, or completed (via Django signals)
2. Day changes (manual refresh via management command)

## Management Commands

### 1. Refresh MoSCoW Matrix for All Users
```bash
python manage.py refresh_moscow
```

### 2. Refresh for Specific User
```bash
python manage.py refresh_moscow --user-id 123
```

### 3. Clear All Cache Entries
```bash
python manage.py refresh_moscow --clear-all
```

## Daily Refresh Setup

### Option 1: Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Daily" at 00:01
4. Set action to start program: `python`
5. Add arguments: `manage.py refresh_moscow`
6. Set working directory to your Django project path

### Option 2: PowerShell Script
Create a PowerShell script `refresh_moscow.ps1`:
```powershell
# Navigate to Django project
Set-Location "E:\Taskademic"

# Activate virtual environment if using one
# .\venv\Scripts\Activate.ps1

# Run the refresh command
python manage.py refresh_moscow

# Log the result
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "moscow_refresh.log" -Value "$timestamp - MoSCoW matrix refreshed"
```

Then schedule it with:
```powershell
# Register scheduled task
$trigger = New-ScheduledTaskTrigger -Daily -At "00:01"
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File E:\Taskademic\refresh_moscow.ps1"
Register-ScheduledTask -TaskName "RefreshMoSCoW" -Trigger $trigger -Action $action
```

### Option 3: Django-Crontab (Linux/WSL)
If you're using a Linux environment:
```bash
pip install django-crontab
```

Add to settings.py:
```python
INSTALLED_APPS = [
    # ...
    'django_crontab',
]

CRONJOBS = [
    ('0 0 * * *', 'django.core.management.call_command', ['refresh_moscow']),
]
```

Then run:
```bash
python manage.py crontab add
```

## Features

### Deterministic Classification
- **Input-Output Consistency**: Same input always produces same output
- **No Randomness**: Zero temperature behavior, no random elements
- **Explicit Rules**: Clear, documented rules for every classification

### Task Type Classification (Ordered Priority)
1. **Major Academic** (Importance: 4)
   - Keywords: research paper, term paper, thesis, dissertation, capstone, senior project, major presentation, defense, project, midterm, final, major exam

2. **Regular Coursework** (Importance: 3)
   - Keywords: homework, assignment, lab report, problem set, pset, quiz, weekly quiz, chapter exercises, discussion post, forum participation, presentation, class presentation

3. **Supplementary** (Importance: 2)
   - Keywords: learn, study, practice, review notes, study notes, flashcards, extra credit, bonus assignment, supplementary reading, optional exercises

4. **Non-Academic** (Importance: 1)
   - Keywords: cooking, shopping, laundry, clean room, entertainment, game, movie, hobby, gym

### MoSCoW Rules (Applied in Order)
1. **Hard deadline ≤ 1 day** → Must
2. **Major academic due ≤ 2 days** → Must  
3. **Regular coursework due ≤ 1 day** → Must
4. **Supplementary due ≤ 1 day** → Should
5. **Non-academic** → Won't
6. **Score thresholds**:
   - ≥ 43 → Must
   - 38-42 → Should
   - 28-37 → Could
   - ≤ 27 → Won't

### Score Calculation
```
Score = (Importance × 10) + (Urgency × 3)

Urgency Weights:
- ≤ 1 day: 3
- 2-3 days: 2  
- 4-7 days: 1
- > 7 days or null: 0

Adjustments:
- Major academic or large tasks due ≤ 2 days: urgency = max(current, 2)
- Major academic or large tasks due ≤ 7 days: urgency = max(current, 3)
- Regular coursework small tasks due ≥ 14 days: urgency = min(current, 0)
- Course weight ≥ 30%: urgency += 1 (capped at 3)
- Overdue tasks: urgency = 3
```

## API Usage

### Refresh Matrix via AJAX
```javascript
fetch('/dashboard/ajax/refresh-moscow/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json',
    },
})
.then(response => response.json())
.then(data => {
    console.log('Refreshed:', data.counts);
});
```

### Access from Django Views
```python
from priority_analyzer.signals import MoSCoWCacheService

# Get cached analysis
result = MoSCoWCacheService.get_moscow_analysis(request.user)

# Force refresh
result = MoSCoWCacheService.force_refresh_moscow_analysis(request.user)
```
