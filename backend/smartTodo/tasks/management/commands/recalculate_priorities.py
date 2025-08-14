from django.core.management.base import BaseCommand
from tasks.models import Task, ContextEntry
from tasks.ai_service import AITaskManager

class Command(BaseCommand):
    help = 'Recalculate priority scores for all tasks based on current context'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            type=str,
            default='pending',
            help='Task status to recalculate (pending, in_progress, all)'
        )

    def handle(self, *args, **options):
        status_filter = options['status']
        
        # Get tasks to recalculate
        if status_filter == 'all':
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(status=status_filter)
        
        if not tasks:
            self.stdout.write('No tasks found to recalculate.')
            return
        
        self.stdout.write(f'Recalculating priorities for {len(tasks)} tasks...')
        
        # Get recent context for analysis
        recent_context = ContextEntry.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=7)
        )[:50]
        
        ai_manager = AITaskManager()
        
        # Analyze context once
        context_analysis = {}
        if recent_context:
            context_analysis = ai_manager.analyze_context(list(recent_context))
        
        updated_count = 0
        
        for task in tasks:
            try:
                self.stdout.write(f'Processing task: {task.title}')
                
                # Get new prioritization
                prioritization = ai_manager.prioritize_task(
                    task, 
                    context_analysis, 
                    list(tasks)
                )
                
                # Update task
                old_score = task.priority_score
                task.priority_score = prioritization.get('priority_score', task.priority_score)
                task.ai_context_analysis = prioritization
                task.save()
                
                updated_count += 1
                self.stdout.write(
                    f'Updated {task.title}: {old_score:.2f} -> {task.priority_score:.2f}'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing task {task.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} tasks')
        )