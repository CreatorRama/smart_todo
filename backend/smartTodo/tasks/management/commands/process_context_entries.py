from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import ContextEntry
from tasks.ai_service import AITaskManager

class Command(BaseCommand):
    help = 'Process unprocessed context entries with AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit number of entries to process'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        # Get unprocessed context entries
        unprocessed_entries = ContextEntry.objects.filter(
            processed_at__isnull=True
        ).order_by('-created_at')[:limit]
        
        if not unprocessed_entries:
            self.stdout.write('No unprocessed context entries found.')
            return
        
        self.stdout.write(f'Processing {len(unprocessed_entries)} context entries...')
        
        ai_manager = AITaskManager()
        processed_count = 0
        
        for entry in unprocessed_entries:
            try:
                self.stdout.write(f'Processing entry {entry.id}...')
                
                # Process individual entry
                insights = ai_manager.analyze_context([entry])
                
                # Update entry with results
                entry.processed_insights = insights
                entry.processed_at = timezone.now()
                entry.save()
                
                processed_count += 1
                self.stdout.write(f'Successfully processed entry {entry.id}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing entry {entry.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {processed_count} entries')
        )