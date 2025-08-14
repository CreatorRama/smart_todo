from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, CategoryViewSet, ContextEntryViewSet, TaskTagViewSet,
    AITaskSuggestionView, TaskPrioritizationView
)

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'context-entries', ContextEntryViewSet)
router.register(r'tags', TaskTagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('ai/task-suggestions/', AITaskSuggestionView.as_view(), name='ai-task-suggestions'),
    path('ai/task-prioritization/', TaskPrioritizationView.as_view(), name='ai-task-prioritization'),
]