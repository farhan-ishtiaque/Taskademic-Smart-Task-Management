from django.contrib import admin
from .models import Team, TeamInvite


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'member_count', 'invite_code', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'invite_code']
    readonly_fields = ['invite_code', 'created_at']
    
    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = 'Members'


@admin.register(TeamInvite)
class TeamInviteAdmin(admin.ModelAdmin):
    list_display = ['email', 'team', 'invited_by', 'is_accepted', 'is_expired', 'created_at']
    list_filter = ['is_accepted', 'created_at', 'expires_at']
    search_fields = ['email', 'team__name']
    readonly_fields = ['invite_token', 'created_at', 'accepted_at']
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
