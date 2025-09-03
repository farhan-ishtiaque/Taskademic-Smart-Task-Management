from django.contrib import admin
from .models import GoogleCalendarSettings, GoogleCalendarToken, TaskCalendarSync


@admin.register(GoogleCalendarSettings)
class GoogleCalendarSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'sync_enabled', 'calendar_id', 'last_sync', 'created_at')
    list_filter = ('sync_enabled', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(GoogleCalendarToken)
class GoogleCalendarTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_expires_at', 'is_expired', 'created_at')
    list_filter = ('token_expires_at', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'is_expired')
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Token Expired'


@admin.register(TaskCalendarSync)
class TaskCalendarSyncAdmin(admin.ModelAdmin):
    list_display = ('task', 'google_event_id', 'sync_status', 'last_synced')
    list_filter = ('sync_status', 'calendar_id', 'last_synced')
    search_fields = ('task__title', 'task__user__username', 'google_event_id')
    readonly_fields = ('last_synced',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('task', 'task__user')
