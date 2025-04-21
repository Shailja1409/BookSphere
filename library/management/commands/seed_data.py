from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from library.models import Book, BorrowRecord, UserProfile
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Seeds the database with sample books and borrow records'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        
        # Create sample books
        books_data = [
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'isbn': '9780743273565',
                'genre': 'Classic',
                'description': 'A story of wealth, love, and the American Dream in the 1920s.',
                'quantity': 5,
                'available': 3
            },
            {
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'isbn': '9780060935467',
                'genre': 'Fiction',
                'description': 'A novel about racial injustice and moral growth in the American South.',
                'quantity': 4,
                'available': 2
            },
            {
                'title': '1984',
                'author': 'George Orwell',
                'isbn': '9780451524935',
                'genre': 'Dystopian',
                'description': 'A dystopian novel about totalitarianism, surveillance, and control.',
                'quantity': 3,
                'available': 1
            },
            {
                'title': 'The Hobbit',
                'author': 'J.R.R. Tolkien',
                'isbn': '9780547928227',
                'genre': 'Fantasy',
                'description': 'A fantasy novel about a hobbit who embarks on an adventure.',
                'quantity': 6,
                'available': 4
            },
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'isbn': '9780141439518',
                'genre': 'Classic',
                'description': 'A romantic novel about societal expectations and personal growth.',
                'quantity': 4,
                'available': 3
            },
            {
                'title': 'The Catcher in the Rye',
                'author': 'J.D. Salinger',
                'isbn': '9780316769488',
                'genre': 'Fiction',
                'description': 'A novel about teenage angst and alienation in 1950s America.',
                'quantity': 3,
                'available': 2
            },
            {
                'title': 'Harry Potter and the Philosopher\'s Stone',
                'author': 'J.K. Rowling',
                'isbn': '9780747532743',
                'genre': 'Fantasy',
                'description': 'The first book in the Harry Potter series about a young wizard.',
                'quantity': 7,
                'available': 5
            },
            {
                'title': 'The Lord of the Rings',
                'author': 'J.R.R. Tolkien',
                'isbn': '9780618640157',
                'genre': 'Fantasy',
                'description': 'An epic fantasy novel about a quest to destroy a powerful ring.',
                'quantity': 5,
                'available': 3
            },
            {
                'title': 'Brave New World',
                'author': 'Aldous Huxley',
                'isbn': '9780060850524',
                'genre': 'Dystopian',
                'description': 'A dystopian novel about a genetically engineered future society.',
                'quantity': 4,
                'available': 2
            },
            {
                'title': 'The Alchemist',
                'author': 'Paulo Coelho',
                'isbn': '9780062315007',
                'genre': 'Fiction',
                'description': 'A novel about following your dreams and finding your destiny.',
                'quantity': 6,
                'available': 4
            }
        ]
        
        # Create some students
        student_usernames = ['student1', 'student2', 'student3', 'student4']
        students = []
        
        for username in student_usernames:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='password123'
                )
                UserProfile.objects.create(user=user, is_librarian=False)
                students.append(user)
                self.stdout.write(f'Created student: {username}')
            else:
                students.append(User.objects.get(username=username))
                self.stdout.write(f'Student {username} already exists')
        
        # Create books if they don't exist
        created_books = []
        for book_data in books_data:
            if not Book.objects.filter(isbn=book_data['isbn']).exists():
                book = Book.objects.create(**book_data)
                created_books.append(book)
                self.stdout.write(f'Created book: {book.title}')
            else:
                book = Book.objects.get(isbn=book_data['isbn'])
                created_books.append(book)
                self.stdout.write(f'Book {book.title} already exists')
        
        # Create some borrow records
        statuses = ['pending', 'approved', 'returned']
        
        # Clear existing borrow records if needed
        # BorrowRecord.objects.all().delete()
        
        # Create 15 random borrow records
        for i in range(15):
            student = random.choice(students)
            book = random.choice(created_books)
            status = random.choice(statuses)
            
            borrow_date = timezone.now() - timedelta(days=random.randint(1, 30))
            due_date = borrow_date + timedelta(days=14)
            return_date = None
            
            if status == 'returned':
                return_date = borrow_date + timedelta(days=random.randint(1, 14))
            
            BorrowRecord.objects.create(
                user=student,
                book=book,
                status=status,
                borrow_date=borrow_date,
                due_date=due_date,
                return_date=return_date
            )
            
            self.stdout.write(f'Created borrow record: {student.username} - {book.title} - {status}')
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded the database!')) 