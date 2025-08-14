from django.core.management.base import BaseCommand
from tasks.models import Category, TaskTag

class Command(BaseCommand):
    help = 'Setup initial categories and tags for the Smart Todo application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create default categories
        default_categories = [
            {'name': 'Work', 'color': '#3B82F6'},
            {'name': 'Personal', 'color': '#10B981'},
            {'name': 'Shopping', 'color': '#F59E0B'},
            {'name': 'Health', 'color': '#EF4444'},
            {'name': 'Learning', 'color': '#8B5CF6'},
            {'name': 'Finance', 'color': '#06B6D4'},
            {'name': 'Family', 'color': '#F97316'},
            {'name': 'Travel', 'color': '#84CC16'},
        ]
        
        created_categories = 0
        for cat_data in default_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'color': cat_data['color']}
            )
            if created:
                created_categories += 1
                self.stdout.write(f'Created category: {category.name}')
        
        # Create default tags
        default_tags = [
            'urgent', 'important', 'meeting', 'call', 'email', 'research',
            'development', 'review', 'planning', 'follow-up', 'deadline',
            'quick', 'complex', 'creative', 'routine', 'documentation',
            'presentation', 'analysis', 'discussion', 'approval'
        ]
        
        created_tags = 0
        for tag_name in default_tags:
            tag, created = TaskTag.objects.get_or_create(name=tag_name)
            if created:
                created_tags += 1
                self.stdout.write(f'Created tag: {tag.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_categories} categories and {created_tags} tags'
            )
        )
