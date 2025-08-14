# tasks/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Task, Category, ContextEntry, TaskTag, TaskTagRelation, AIProcessingLog

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'priority', 'priority_score_display', 'status', 'deadline', 'created_at']
    list_filter = ['priority', 'status', 'category', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-priority_score', '-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'status')
        }),
        ('Priority & Timing', {
            'fields': ('priority', 'priority_score', 'deadline', 'estimated_duration')
        }),
        ('AI Enhancement', {
            'fields': ('ai_enhanced_description', 'ai_suggested_tags', 'ai_suggestions'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'priority_score']
    
    def priority_score_display(self, obj):
        score = obj.priority_score
        if score >= 0.8:
            color = 'red'
        elif score >= 0.6:
            color = 'orange'
        elif score >= 0.4:
            color = 'blue'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color, score
        )
    priority_score_display.short_description = 'Priority Score'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'color_display', 'usage_count', 'created_at']
    list_editable = ['color']
    ordering = ['-usage_count', 'name']
    
    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'

@admin.register(ContextEntry)
class ContextEntryAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'source_identifier', 'timestamp', 'processed_status', 'created_at']
    list_filter = ['source_type', 'processed_at', 'timestamp']
    search_fields = ['content', 'source_identifier']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Context Information', {
            'fields': ('content', 'source_type', 'source_identifier', 'timestamp')
        }),
        ('AI Processing Results', {
            'fields': ('processed_insights', 'extracted_tasks', 'urgency_indicators', 'mentioned_deadlines'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('processed_at', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['processed_at', 'created_at']
    
    def processed_status(self, obj):
        if obj.processed_at:
            return format_html('<span style="color: green;">✓ Processed</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    processed_status.short_description = 'AI Status'

@admin.register(TaskTag)
class TaskTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'usage_count', 'created_at']
    ordering = ['-usage_count', 'name']
    search_fields = ['name']

@admin.register(TaskTagRelation)
class TaskTagRelationAdmin(admin.ModelAdmin):
    list_display = ['task', 'tag', 'ai_suggested', 'created_at']
    list_filter = ['ai_suggested', 'created_at']
    search_fields = ['task__title', 'tag__name']

@admin.register(AIProcessingLog)
class AIProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['processing_type', 'model_used', 'success', 'processing_time_ms', 'created_at']
    list_filter = ['processing_type', 'success', 'model_used', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Processing Information', {
            'fields': ('processing_type', 'model_used', 'success', 'processing_time_ms')
        }),
        ('Data', {
            'fields': ('input_data', 'output_data'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # Don't allow manual addition of logs