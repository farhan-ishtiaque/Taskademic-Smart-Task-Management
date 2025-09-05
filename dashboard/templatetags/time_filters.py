from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def calculate_total_hours(blocks):
    """Calculate total hours from a list of time blocks"""
    if not blocks:
        return 0
    
    total_minutes = 0
    for block in blocks:
        # Calculate duration in minutes
        start_time = block.start_time
        end_time = block.end_time
        
        # Convert to datetime objects for calculation
        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)
        
        # Handle overnight blocks (end time next day)
        if end_datetime <= start_datetime:
            end_datetime += timedelta(days=1)
        
        duration = end_datetime - start_datetime
        total_minutes += duration.total_seconds() / 60
    
    # Convert to hours and round to 1 decimal place
    total_hours = total_minutes / 60
    return round(total_hours, 1)

@register.filter
def format_hours(hours):
    """Format hours display"""
    if hours == 0:
        return "0 hours"
    elif hours == 1:
        return "1 hour"
    elif hours == int(hours):
        return f"{int(hours)} hours"
    else:
        return f"{hours} hours"
