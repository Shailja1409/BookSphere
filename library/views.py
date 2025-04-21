from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .models import Book, BorrowRecord, UserProfile, BookRequest
from django.contrib.auth.models import User
from datetime import datetime, timedelta

def home(request):
    books = Book.objects.all().order_by('-created_at')[:6]
    
    # Get popular books for homepage
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrowrecord')
    ).order_by('-borrow_count')[:4]
    
    return render(request, 'library/home.html', {
        'books': books,
        'popular_books': popular_books
    })

def book_list(request):
    query = request.GET.get('q', '')
    availability = request.GET.get('availability', 'all')
    
    books = Book.objects.all()
    
    # Apply search filter if query exists
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(genre__icontains=query)
        )
    
    # Apply availability filter
    if availability == 'available':
        books = books.filter(available__gt=0)
    elif availability == 'unavailable':
        books = books.filter(available=0)
    
    return render(request, 'library/book_list.html', {
        'books': books,
        'query': query,
        'availability': availability
    })

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    user_borrow_status = BorrowRecord.objects.filter(
        user=request.user,
        book=book,
        status__in=['pending', 'approved']
    ).first()
    
    # Get similar books by genre
    similar_books = Book.objects.filter(genre=book.genre).exclude(pk=book.pk)[:4]
    
    return render(request, 'library/book_detail.html', {
        'book': book,
        'user_borrow_status': user_borrow_status,
        'similar_books': similar_books
    })

@login_required
def borrow_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    if book.available > 0:
        BorrowRecord.objects.create(
            user=request.user,
            book=book,
            status='pending'
        )
        messages.success(request, 'Borrow request submitted successfully!')
    else:
        messages.error(request, 'Sorry, this book is currently unavailable.')
    
    return redirect('book_detail', pk=pk)

@login_required
def user_dashboard(request):
    user_borrows = BorrowRecord.objects.filter(user=request.user).order_by('-borrow_date')
    
    # Get counts for different borrow statuses
    pending_count = user_borrows.filter(status='pending').count()
    approved_count = user_borrows.filter(status='approved').count()
    returned_count = user_borrows.filter(status='returned').count()
    
    # Get returned borrows for history section
    returned_borrows = user_borrows.filter(status='returned')
    
    # Get recent books for display
    recent_books = Book.objects.filter(available__gt=0).order_by('-created_at')[:8]
    
    return render(request, 'student/dashboard.html', {
        'borrows': user_borrows,
        'returned_borrows': returned_borrows,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'returned_count': returned_count,
        'total_count': user_borrows.count(),
        'recent_books': recent_books,
        'now': timezone.now()
    })

@login_required
def librarian_dashboard(request):
    if not request.user.userprofile.is_librarian:
        return redirect('home')
    
    pending_requests = BorrowRecord.objects.filter(status='pending')
    overdue_books = BorrowRecord.objects.filter(
        status='approved',
        due_date__lt=timezone.now()
    )
    
    books = Book.objects.all()
    books_count = books.count()
    users_count = User.objects.count()
    
    # Additional stats
    total_borrows = BorrowRecord.objects.count()
    current_borrows = BorrowRecord.objects.filter(status='approved').count()
    returned_books = BorrowRecord.objects.filter(status='returned').count()
    
    # Most popular books
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrowrecord')
    ).order_by('-borrow_count')[:5]
    
    return render(request, 'librarian/dashboard.html', {
        'pending_requests': pending_requests,
        'overdue_books': overdue_books,
        'books': books[:10],  # Show only the first 10 books
        'books_count': books_count,
        'users_count': users_count,
        'total_borrows': total_borrows,
        'current_borrows': current_borrows,
        'returned_books': returned_books,
        'popular_books': popular_books
    })

@login_required
def manage_request(request, borrow_id, action):
    if not request.user.userprofile.is_librarian:
        return redirect('home')
    
    borrow_record = get_object_or_404(BorrowRecord, id=borrow_id)
    
    if action == 'approve' and borrow_record.status == 'pending':
        borrow_record.status = 'approved'
        borrow_record.due_date = timezone.now() + timedelta(days=14)
        borrow_record.book.available -= 1
        borrow_record.book.save()
    elif action == 'reject' and borrow_record.status == 'pending':
        borrow_record.status = 'rejected'
    elif action == 'return' and borrow_record.status == 'approved':
        borrow_record.status = 'returned'
        borrow_record.return_date = timezone.now()
        borrow_record.book.available += 1
        borrow_record.book.save()
    
    borrow_record.save()
    messages.success(request, f'Request {action}d successfully!')
    return redirect('librarian_dashboard')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('register')
        
        user = User.objects.create_user(username=username, email=email, password=password1)
        UserProfile.objects.create(user=user)
        
        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('home')
    
    return render(request, 'registration/register.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

def setup_demo_librarian():
    """
    Setup a demo librarian account that can be called from a management command.
    This is not a view but a utility function.
    """
    username = 'librarian'
    password = 'library123'
    email = 'librarian@example.com'
    
    # Check if the user already exists
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,  # Give admin site access
            is_superuser=True  # Full admin permissions
        )
        
        # Create or update the UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.is_librarian = True
        profile.save()
        
        print(f"Librarian account created: {username} / {password}")
    else:
        print(f"Librarian account already exists: {username}")

@login_required
def add_book(request):
    if not request.user.userprofile.is_librarian:
        messages.error(request, 'You do not have permission to add books.')
        return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        genre = request.POST.get('genre')
        description = request.POST.get('description')
        quantity = int(request.POST.get('quantity', 1))
        cover_image = request.FILES.get('cover_image')
        auto_fetch_cover = request.POST.get('auto_fetch_cover') == 'on'
        
        # Validation
        if not all([title, author, isbn, genre, description]):
            messages.error(request, 'All fields are required.')
            return render(request, 'library/add_book.html', {'form_data': request.POST})
        
        if Book.objects.filter(isbn=isbn).exists():
            messages.error(request, 'A book with this ISBN already exists.')
            return render(request, 'library/add_book.html', {'form_data': request.POST})
        
        # Create book
        book = Book.objects.create(
            title=title,
            author=author,
            isbn=isbn,
            genre=genre,
            description=description,
            quantity=quantity,
            available=quantity
        )
        
        # Handle cover image
        if cover_image:
            book.cover_image = cover_image
            book.save()
        elif auto_fetch_cover:
            # Try to fetch cover from online source
            try:
                from .admin import get_cover_image
                image_data = get_cover_image(title, author, isbn)
                if image_data:
                    from django.core.files.base import ContentFile
                    filename = f"{book.title.replace(' ', '_')[:30]}.jpg"
                    book.cover_image.save(filename, ContentFile(image_data), save=True)
                    messages.success(request, f'Cover image for "{title}" was automatically downloaded.')
            except Exception as e:
                messages.warning(request, f'Could not automatically fetch cover image: {str(e)}')
        
        messages.success(request, f'Book "{title}" has been added successfully.')
        return redirect('book_detail', pk=book.pk)
    
    return render(request, 'library/add_book.html')

@login_required
def edit_book(request, pk):
    if not request.user.userprofile.is_librarian:
        messages.error(request, 'You do not have permission to edit books.')
        return redirect('home')
    
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        genre = request.POST.get('genre')
        description = request.POST.get('description')
        quantity = int(request.POST.get('quantity', 1))
        cover_image = request.FILES.get('cover_image')
        auto_fetch_cover = request.POST.get('auto_fetch_cover') == 'on'
        
        # Validation
        if not all([title, author, isbn, genre, description]):
            messages.error(request, 'All fields are required.')
            return render(request, 'library/edit_book.html', {'book': book, 'form_data': request.POST})
        
        # Check if ISBN changed and already exists
        if isbn != book.isbn and Book.objects.filter(isbn=isbn).exists():
            messages.error(request, 'A book with this ISBN already exists.')
            return render(request, 'library/edit_book.html', {'book': book, 'form_data': request.POST})
        
        # Update available copies if quantity changed
        available_change = quantity - book.quantity
        new_available = max(0, book.available + available_change)
        
        # Update book
        book.title = title
        book.author = author
        book.isbn = isbn
        book.genre = genre
        book.description = description
        book.quantity = quantity
        book.available = new_available
        
        # Handle cover image
        if cover_image:
            book.cover_image = cover_image
        elif auto_fetch_cover and not book.cover_image:
            # Try to fetch cover from online source
            try:
                from .admin import get_cover_image
                image_data = get_cover_image(title, author, isbn)
                if image_data:
                    from django.core.files.base import ContentFile
                    filename = f"{book.title.replace(' ', '_')[:30]}.jpg"
                    book.cover_image.save(filename, ContentFile(image_data), save=True)
                    messages.success(request, f'Cover image for "{title}" was automatically downloaded.')
            except Exception as e:
                messages.warning(request, f'Could not automatically fetch cover image: {str(e)}')
        
        book.save()
        
        messages.success(request, f'Book "{title}" has been updated successfully.')
        return redirect('book_detail', pk=book.pk)
    
    return render(request, 'library/edit_book.html', {'book': book})

@login_required
def delete_book(request, pk):
    if not request.user.userprofile.is_librarian:
        messages.error(request, 'You do not have permission to delete books.')
        return redirect('home')
    
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'Book "{title}" has been deleted successfully.')
        return redirect('book_list')
    
    return render(request, 'library/delete_book.html', {'book': book})

@login_required
def issue_book(request, pk):
    """Issue a book directly (librarian function)"""
    if not request.user.userprofile.is_librarian:
        messages.error(request, 'You do not have permission to issue books.')
        return redirect('home')
    
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('book_detail', pk=pk)
        
        if book.available <= 0:
            messages.error(request, 'No copies available for issue.')
            return redirect('book_detail', pk=pk)
        
        # Check if user already has this book
        if BorrowRecord.objects.filter(user=user, book=book, status__in=['pending', 'approved']).exists():
            messages.error(request, f'User {user.username} already has this book checked out.')
            return redirect('book_detail', pk=pk)
        
        # Create and approve borrow record
        borrow = BorrowRecord.objects.create(
            user=user,
            book=book,
            status='approved',
            due_date=timezone.now() + timedelta(days=14)
        )
        
        # Update book availability
        book.available -= 1
        book.save()
        
        messages.success(request, f'Book issued to {user.username} successfully.')
        return redirect('librarian_dashboard')
    
    # Get all users for dropdown
    users = User.objects.all()
    return render(request, 'library/issue_book.html', {'book': book, 'users': users})

@login_required
def return_book(request, borrow_id):
    """Return a book (librarian function)"""
    if not request.user.userprofile.is_librarian:
        messages.error(request, 'You do not have permission for this action.')
        return redirect('home')
    
    borrow_record = get_object_or_404(BorrowRecord, id=borrow_id)
    
    if borrow_record.status != 'approved':
        messages.error(request, 'This book is not currently issued.')
        return redirect('librarian_dashboard')
    
    borrow_record.status = 'returned'
    borrow_record.return_date = timezone.now()
    borrow_record.save()
    
    # Update book availability
    book = borrow_record.book
    book.available += 1
    book.save()
    
    messages.success(request, f'Book returned successfully from {borrow_record.user.username}.')
    return redirect('librarian_dashboard')

@login_required
def request_return(request, borrow_id):
    """Request to return a book (student function)"""
    borrow_record = get_object_or_404(BorrowRecord, id=borrow_id, user=request.user)
    
    if borrow_record.status != 'approved':
        messages.error(request, 'This book is not currently borrowed by you.')
        return redirect('user_dashboard')
    
    # Create a message to notify librarians (in a real system, you might implement notifications)
    messages.success(request, f'Return request for "{borrow_record.book.title}" has been submitted. Please return the book to the library.')
    
    # If you want to implement an immediate return:
    borrow_record.status = 'returned'
    borrow_record.return_date = timezone.now()
    borrow_record.save()
    
    # Update book availability
    book = borrow_record.book
    book.available += 1
    book.save()
    
    return redirect('user_dashboard')

def popular_books(request):
    """View to show most popular books by borrow count"""
    # Get all books with their borrow counts
    books = Book.objects.annotate(
        borrow_count=Count('borrowrecord')
    ).order_by('-borrow_count')
    
    # Get total borrow count
    total_borrows = BorrowRecord.objects.count()
    
    return render(request, 'library/popular_books.html', {
        'books': books,
        'total_borrows': total_borrows
    })

@login_required
def generate_report(request):
    """Generate a report of library activity for librarians"""
    if not request.user.userprofile.is_librarian:
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('home')
    
    # Get report type from query parameter
    report_type = request.GET.get('type', 'books')
    
    if report_type == 'books':
        # Books with their borrow counts and availability
        books = Book.objects.annotate(
            borrow_count=Count('borrowrecord')
        ).order_by('-borrow_count')
        
        return render(request, 'library/reports/book_report.html', {
            'books': books,
            'total_books': books.count(),
            'total_quantity': sum(book.quantity for book in books),
            'total_available': sum(book.available for book in books),
            'report_type': report_type
        })
    
    elif report_type == 'users':
        # Users with their borrow counts
        users = User.objects.annotate(
            borrow_count=Count('borrowrecord')
        ).order_by('-borrow_count')
        
        active_users = users.filter(borrow_count__gt=0)
        
        return render(request, 'library/reports/user_report.html', {
            'users': active_users,
            'total_users': User.objects.count(),
            'active_users': active_users.count(),
            'report_type': report_type
        })
    
    elif report_type == 'activity':
        # Recent borrow activity
        recent_activity = BorrowRecord.objects.all().order_by('-borrow_date')[:50]
        
        # Activity by status
        pending_count = BorrowRecord.objects.filter(status='pending').count()
        approved_count = BorrowRecord.objects.filter(status='approved').count()
        returned_count = BorrowRecord.objects.filter(status='returned').count()
        rejected_count = BorrowRecord.objects.filter(status='rejected').count()
        
        # Activity by timeframe
        today = timezone.now().date()
        this_week = today - timedelta(days=7)
        this_month = today - timedelta(days=30)
        
        activity_today = BorrowRecord.objects.filter(borrow_date__date=today).count()
        activity_week = BorrowRecord.objects.filter(borrow_date__date__gte=this_week).count()
        activity_month = BorrowRecord.objects.filter(borrow_date__date__gte=this_month).count()
        
        return render(request, 'library/reports/activity_report.html', {
            'recent_activity': recent_activity,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'returned_count': returned_count,
            'rejected_count': rejected_count,
            'activity_today': activity_today,
            'activity_week': activity_week,
            'activity_month': activity_month,
            'total_activity': BorrowRecord.objects.count(),
            'report_type': report_type
        })
    
    else:
        messages.error(request, 'Invalid report type specified.')
        return redirect('librarian_dashboard')

@login_required
def request_book(request):
    """View for students to request new books to be added to the library"""
    # Redirect librarians away from this page
    if request.user.userprofile.is_librarian:
        messages.warning(request, 'Librarians should add books directly rather than requesting them.')
        return redirect('add_book')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        genre = request.POST.get('genre')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes')
        
        # Validation
        if not all([title, author, genre, reason]):
            messages.error(request, 'Please fill out all required fields.')
            return render(request, 'student/request_book.html', {
                'form_data': request.POST
            })
        
        # Create book request
        BookRequest.objects.create(
            user=request.user,
            title=title,
            author=author,
            isbn=isbn,
            genre=genre,
            reason=reason,
            notes=notes
        )
        
        messages.success(request, f'Your request for "{title}" has been submitted. The library staff will review it soon.')
        return redirect('user_dashboard')
    
    return render(request, 'student/request_book.html')

@login_required
def manage_book_requests(request):
    """View for librarians to manage book requests"""
    if not request.user.userprofile.is_librarian:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    book_requests = BookRequest.objects.all().order_by('-created_at')
    
    return render(request, 'librarian/manage_book_requests.html', {
        'book_requests': book_requests,
        'pending_count': book_requests.filter(status='pending').count(),
        'approved_count': book_requests.filter(status='approved').count(),
        'rejected_count': book_requests.filter(status='rejected').count()
    })

@login_required
def process_book_request(request, request_id, action):
    """View to process (approve/reject) book requests"""
    if not request.user.userprofile.is_librarian:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    book_request = get_object_or_404(BookRequest, id=request_id)
    
    if action == 'approve':
        # Change status to approved
        book_request.status = 'approved'
        book_request.save()
        
        # Create the book
        Book.objects.create(
            title=book_request.title,
            author=book_request.author,
            isbn=book_request.isbn or 'N/A',
            genre=book_request.genre,
            description=book_request.reason,
            quantity=1,
            available=1
        )
        
        messages.success(request, f'Request approved and book "{book_request.title}" added to the library.')
    
    elif action == 'reject':
        book_request.status = 'rejected'
        book_request.save()
        messages.success(request, f'Request for "{book_request.title}" has been rejected.')
    
    return redirect('manage_book_requests') 