# tasks/views.py
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Q
import logging

from .models import Task, Category, ContextEntry, TaskTag, TaskTagRelation
from .serializers import (
    TaskSerializer, TaskCreateSerializer, CategorySerializer, 
    ContextEntrySerializer, ContextEntryCreateSerializer, TaskTagSerializer,
    AITaskSuggestionRequestSerializer, AITaskSuggestionResponseSerializer,
    TaskPrioritizationRequestSerializer, TaskPrioritizationResponseSerializer
)
from .ai_service import AITaskManager

logger = logging.getLogger(__name__)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category', 'priority', 'status']
    ordering_fields = ['priority_score', 'created_at', 'deadline', 'updated_at']
    ordering = ['-priority_score', '-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the task
        task = serializer.save()
        
        # Return full task data
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Handle tags if provided
        if 'tags' in request.data:
            tags_data = request.data['tags']
            # Clear existing non-AI tags
            instance.tag_relations.filter(ai_suggested=False).delete()
            
            # Add new tags
            for tag_name in tags_data:
                tag, created = TaskTag.objects.get_or_create(name=tag_name.lower())
                TaskTagRelation.objects.get_or_create(
                    task=instance, 
                    tag=tag, 
                    defaults={'ai_suggested': False}
                )
                if not created:
                    tag.usage_count += 1
                    tag.save()
        
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get task statistics"""
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status='completed').count()
        pending_tasks = Task.objects.filter(status='pending').count()
        in_progress_tasks = Task.objects.filter(status='in_progress').count()
        overdue_tasks = Task.objects.filter(
            deadline__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count()

        return Response({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'in_progress_tasks': in_progress_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        })

    @action(detail=False, methods=['get'])
    def priority_distribution(self, request):
        """Get task distribution by priority"""
        priorities = Task.objects.values('priority').distinct()
        distribution = {}
        
        for priority_item in priorities:
            priority = priority_item['priority']
            count = Task.objects.filter(priority=priority, status__in=['pending', 'in_progress']).count()
            distribution[priority] = count
        
        return Response(distribution)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most used categories"""
        categories = Category.objects.order_by('-usage_count')[:10]
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)

class ContextEntryViewSet(viewsets.ModelViewSet):
    queryset = ContextEntry.objects.all()
    serializer_class = ContextEntrySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['source_type']
    ordering = ['-timestamp']

    def get_serializer_class(self):
        if self.action == 'create':
            return ContextEntryCreateSerializer
        return ContextEntrySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the context entry
        context_entry = serializer.save()
        
        # Process with AI in background (optional)
        try:
            ai_manager = AITaskManager()
            insights = ai_manager.analyze_context([context_entry])
            
            context_entry.processed_insights = insights
            context_entry.processed_at = timezone.now()
            context_entry.save()
        except Exception as e:
            logger.error(f"Error processing context entry: {str(e)}")
        
        # Return full context data
        response_serializer = ContextEntrySerializer(context_entry)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple context entries at once"""
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of context entries'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_entries = []
        errors = []
        
        for i, entry_data in enumerate(request.data):
            serializer = ContextEntryCreateSerializer(data=entry_data)
            if serializer.is_valid():
                context_entry = serializer.save()
                created_entries.append(context_entry)
            else:
                errors.append({'index': i, 'errors': serializer.errors})
        
        # Process all entries with AI
        if created_entries:
            try:
                ai_manager = AITaskManager()
                insights = ai_manager.analyze_context(created_entries)
                
                # Update entries with insights
                for entry in created_entries:
                    entry.processed_insights = insights
                    entry.processed_at = timezone.now()
                    entry.save()
            except Exception as e:
                logger.error(f"Error processing context entries: {str(e)}")
        
        response_data = {
            'created': len(created_entries),
            'errors': errors,
            'entries': ContextEntrySerializer(created_entries, many=True).data
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        return {}

class TaskTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskTag.objects.all()
    serializer_class = TaskTagSerializer
    ordering = ['-usage_count', 'name']

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most used tags"""
        tags = TaskTag.objects.order_by('-usage_count')[:20]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)

class AITaskSuggestionView(APIView):
    """
    POST API for getting AI-powered task suggestions and prioritization
    """
    
    def post(self, request):
        request_serializer = AITaskSuggestionRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = request_serializer.validated_data
        task_data = validated_data['task_data']
        context_entry_ids = validated_data.get('context_entries', [])
        user_preferences = validated_data.get('user_preferences', {})
        current_task_load = validated_data.get('current_task_load', 0)
        
        try:
            ai_manager = AITaskManager()
            
            # Get context entries if provided
            context_entries = []
            if context_entry_ids:
                context_entries = ContextEntry.objects.filter(id__in=context_entry_ids)
                
            print(task_data)
            
            # Get AI recommendations
            recommendations = ai_manager.get_task_recommendations(
                task_data=task_data,
                context_entries=list(context_entries),
                user_preferences=user_preferences,
                current_task_load=current_task_load
            )
            
            response_serializer = AITaskSuggestionResponseSerializer(data=recommendations)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(recommendations, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting AI task suggestions: {str(e)}")
            return Response(
                {'error': 'Failed to get AI suggestions', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TaskPrioritizationView(APIView):
    def post(self, request):
        try:
            request_serializer = TaskPrioritizationRequestSerializer(data=request.data)
            request_serializer.is_valid(raise_exception=True)
            
            validated_data = request_serializer.validated_data
            task_ids = validated_data['task_ids']
            context_entry_ids = validated_data.get('context_entries', [])
            
            # Get tasks with existence check
            tasks = Task.objects.filter(id__in=task_ids)
            if len(tasks) != len(task_ids):
                missing_ids = set(task_ids) - set(t.id for t in tasks)
                return Response(
                    {"error": f"Tasks not found: {missing_ids}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Process with AI
            ai_manager = AITaskManager()
            results = []
            
            for task in tasks:
                try:
                    result = ai_manager.prioritize_task(task)
                    task.priority_score = result.get('priority_score', task.priority_score)
                    task.save()
                    results.append({
                        'task_id': task.id,
                        'priority_score': task.priority_score,
                        'reasoning': result.get('reasoning', '')
                    })
                except Exception as e:
                    logger.error(f"Error processing task {task.id}: {str(e)}")
                    results.append({
                        'task_id': task.id,
                        'error': str(e),
                        'priority_score': task.priority_score
                    })
            
            return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Task prioritization failed: {str(e)}", exc_info=True)
            return Response(
                {"error": "Task prioritization failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    """
    POST API for bulk task prioritization based on context
    """
    
    def post(self, request):
        request_serializer = TaskPrioritizationRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = request_serializer.validated_data
        task_ids = validated_data['task_ids']
        context_entry_ids = validated_data.get('context_entries', [])
        user_preferences = validated_data.get('user_preferences', {})
        
        try:
            # Get tasks and context
            tasks = Task.objects.filter(id__in=task_ids)
            context_entries = []
            if context_entry_ids:
                context_entries = ContextEntry.objects.filter(id__in=context_entry_ids)
            
            ai_manager = AITaskManager()
            
            # Analyze context once for all tasks
            context_analysis = {}
            if context_entries:
                context_analysis = ai_manager.analyze_context(list(context_entries))
            
            # Get prioritization for each task
            results = []
            for task in tasks:
                prioritization = ai_manager.prioritize_task(task, context_analysis, list(tasks))
                
                # Update task with new priority score
                task.priority_score = prioritization.get('priority_score', task.priority_score)
                task.ai_suggestions = prioritization
                task.save()
                
                results.append({
                    'task_id': task.id,
                    'priority_score': task.priority_score,
                    'reasoning': prioritization.get('reasoning', '')
                })
            
            response_serializer = TaskPrioritizationResponseSerializer(data=results, many=True)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in task prioritization: {str(e)}")
            return Response(
                {'error': 'Failed to prioritize tasks', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )