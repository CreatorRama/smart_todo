# tasks/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    priority_score = models.FloatField(
        default=0.5, 
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="AI-calculated priority score (0-1)"
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    deadline = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.IntegerField(null=True, blank=True, help_text="Duration in minutes")
    
    # AI Enhancement fields
    ai_enhanced_description = models.TextField(blank=True, null=True)
    ai_suggested_tags = models.JSONField(default=list, blank=True)
    ai_suggestions = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority_score', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'completed':
            self.completed_at = None
        super().save(*args, **kwargs)

class ContextEntry(models.Model):
    SOURCE_TYPES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('notes', 'Notes'),
        ('calendar', 'Calendar'),
        ('other', 'Other'),
    ]

    content = models.TextField()
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES,default='other')
    source_identifier = models.CharField(max_length=200, blank=True, help_text="Sender, subject, etc.")
    
    # AI Processing results
    processed_insights = models.JSONField(default=dict, blank=True)
    extracted_tasks = models.JSONField(default=list, blank=True)
    urgency_indicators = models.JSONField(default=list, blank=True)
    mentioned_deadlines = models.JSONField(default=list, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.source_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class TaskTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TaskTagRelation(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='tag_relations')
    tag = models.ForeignKey(TaskTag, on_delete=models.CASCADE)
    ai_suggested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'tag')

class AIProcessingLog(models.Model):
    PROCESSING_TYPES = [
        ('task_prioritization', 'Task Prioritization'),
        ('context_analysis', 'Context Analysis'),
        ('deadline_suggestion', 'Deadline Suggestion'),
        ('task_enhancement', 'Task Enhancement'),
        ('categorization', 'Categorization'),
    ]

    processing_type = models.CharField(max_length=30, choices=PROCESSING_TYPES)
    input_data = models.JSONField()
    output_data = models.JSONField()
    processing_time_ms = models.IntegerField()
    model_used = models.CharField(max_length=100)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']