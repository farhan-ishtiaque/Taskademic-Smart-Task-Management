from django.contrib import admin
from .models import UserLevel, PointTransaction, DailyActivity, Achievement, UserAchievement


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_level', 'level_name', 'total_points', 'streak_days', 'longest_streak']
    list_filter = ['current_level', 'level_name']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Level & Points', {
            'fields': ('current_level', 'level_name', 'total_points', 'points_to_next_level')
        }),
        ('Streaks', {
            'fields': ('streak_days', 'longest_streak', 'last_activity_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'transaction_type', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'task')


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'tasks_completed', 'tasks_total', 'completion_rate', 'is_successful_day', 'streak_day']
    list_filter = ['date']
    search_fields = ['user__username']
    date_hierarchy = 'date'
    
    def completion_rate(self, obj):
        return f"{obj.completion_rate:.1f}%"
    completion_rate.short_description = 'Completion Rate'
    
    def is_successful_day(self, obj):
        return obj.is_successful_day
    is_successful_day.short_description = 'Successful Day'
    is_successful_day.boolean = True


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'points_reward', 'criteria_type', 'criteria_value', 'is_active']
    list_filter = ['criteria_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['achievement', 'earned_at']
    search_fields = ['user__username', 'achievement__name']
    readonly_fields = ['earned_at']
