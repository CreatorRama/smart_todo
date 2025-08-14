# tasks/serializers.py
from rest_framework import serializers
from .models import Task, Category, ContextEntry, TaskTag, TaskTagRelation, AIProcessingLog

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'usage_count', 'created_at', 'updated_at']
        read_only_fields = ['usage_count', 'created_at', 'updated_at']

class TaskTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTag
        fields = ['id', 'name', 'usage_count']
        read_only_fields = ['usage_count']

class TaskSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'priority', 'priority_score', 'status', 'deadline',
            'estimated_duration', 'ai_enhanced_description', 
            'ai_suggested_tags', 'ai_suggestions',
            'tags', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['priority_score', 'ai_enhanced_description', 
                           'ai_suggested_tags', 'ai_suggestions', 
                           'created_at', 'updated_at', 'completed_at']

    def get_tags(self, obj):
        tag_relations = obj.tag_relations.select_related('tag')
        return [{
            'id': rel.tag.id,
            'name': rel.tag.name,
            'ai_suggested': rel.ai_suggested
        } for rel in tag_relations]

class TaskCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'category', 'priority', 
            'deadline', 'estimated_duration', 'tags'
        ]

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        task = Task.objects.create(**validated_data)
        
        # Create tag relations
        for tag_name in tags_data:
            tag, created = TaskTag.objects.get_or_create(name=tag_name.lower())
            TaskTagRelation.objects.create(task=task, tag=tag, ai_suggested=False)
            if not created:
                tag.usage_count += 1
                tag.save()
        
        return task

class ContextEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextEntry
        fields = [
            'id', 'content', 'source_type', 'source_identifier',
            'processed_insights', 'extracted_tasks', 'urgency_indicators',
            'mentioned_deadlines', 'timestamp', 'processed_at', 'created_at'
        ]
        read_only_fields = ['processed_insights', 'extracted_tasks', 
                           'urgency_indicators', 'mentioned_deadlines', 
                           'processed_at', 'created_at']

class ContextEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextEntry
        fields = ['content', 'source_type', 'source_identifier', 'timestamp']

class AITaskSuggestionRequestSerializer(serializers.Serializer):
    task_data = serializers.JSONField()
    context_entries = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    user_preferences = serializers.JSONField(required=False)
    current_task_load = serializers.IntegerField(required=False)

class AITaskSuggestionResponseSerializer(serializers.Serializer):
    priority_score = serializers.FloatField()
    suggested_priority = serializers.CharField()
    enhanced_description = serializers.CharField(allow_blank=True)
    suggested_tags = serializers.ListField(child=serializers.CharField())
    suggested_category = serializers.CharField(allow_blank=True)
    suggested_deadline = serializers.DateTimeField(allow_null=True)
    estimated_duration = serializers.IntegerField(allow_null=True)
    context_analysis = serializers.JSONField()
    reasoning = serializers.CharField()

class TaskPrioritizationRequestSerializer(serializers.Serializer):
    task_ids = serializers.ListField(child=serializers.IntegerField())
    context_entries = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    user_preferences = serializers.JSONField(required=False)

class TaskPrioritizationResponseSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    priority_score = serializers.FloatField()
    reasoning = serializers.CharField()

class AIProcessingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProcessingLog
        fields = [
            'id', 'processing_type', 'input_data', 'output_data',
            'processing_time_ms', 'model_used', 'success',
            'error_message', 'created_at'
        ]
        read_only_fields = ['created_at']