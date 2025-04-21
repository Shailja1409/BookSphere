from django.core.management.base import BaseCommand
from library.views import setup_demo_librarian

class Command(BaseCommand):
    help = 'Creates a demo librarian account'

    def handle(self, *args, **options):
        setup_demo_librarian()
        self.stdout.write(self.style.SUCCESS('Demo librarian account setup completed!')) 