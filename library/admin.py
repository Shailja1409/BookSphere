from django.contrib import admin
from .models import Book, BorrowRecord, UserProfile, BookRequest
import requests
from django.core.files.base import ContentFile
from urllib.parse import quote_plus
from django.contrib import messages

def get_cover_image(title, author, isbn=None):
    """
    Try to get a book cover image from Open Library
    First try by ISBN if available, then by title and author
    """
    image_data = None
    
    # First attempt: ISBN lookup if available
    if isbn and isbn != 'N/A':
        try:
            # Clean ISBN - remove dashes, spaces, etc.
            clean_isbn = ''.join(c for c in isbn if c.isdigit() or c.lower() == 'x')
            
            # Try Open Library ISBN API
            url = f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-L.jpg"
            response = requests.get(url)
            
            # If response is valid and not the default "no image" response
            if response.status_code == 200 and len(response.content) > 1000:
                return response.content
        except Exception as e:
            print(f"Error fetching by ISBN {isbn}: {e}")
    
    # Second attempt: Title + Author lookup
    try:
        search_title = quote_plus(title)
        search_author = quote_plus(author)
        
        # Use Open Library search API
        search_url = f"https://openlibrary.org/search.json?title={search_title}&author={search_author}"
        search_response = requests.get(search_url)
        
        if search_response.status_code == 200:
            data = search_response.json()
            if data.get('docs') and len(data['docs']) > 0:
                # Get the first result
                first_book = data['docs'][0]
                
                # Check if it has a cover edition key
                if first_book.get('cover_edition_key'):
                    cover_edition_key = first_book['cover_edition_key']
                    cover_url = f"https://covers.openlibrary.org/b/olid/{cover_edition_key}-L.jpg"
                    img_response = requests.get(cover_url)
                    
                    if img_response.status_code == 200 and len(img_response.content) > 1000:
                        return img_response.content
                
                # Try cover_i if cover_edition_key didn't work
                elif first_book.get('cover_i'):
                    cover_i = first_book['cover_i']
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
                    img_response = requests.get(cover_url)
                    
                    if img_response.status_code == 200 and len(img_response.content) > 1000:
                        return img_response.content
    
    except Exception as e:
        print(f"Error fetching by title/author {title}/{author}: {e}")
    
    return None

def download_book_covers(modeladmin, request, queryset):
    """Admin action to download book covers for selected books"""
    success_count = 0
    error_count = 0
    
    for book in queryset:
        if not book.cover_image:
            image_data = get_cover_image(book.title, book.author, book.isbn)
            
            if image_data:
                filename = f"{book.title.replace(' ', '_')[:30]}.jpg"
                book.cover_image.save(filename, ContentFile(image_data), save=True)
                success_count += 1
            else:
                error_count += 1
    
    if success_count:
        messages.success(request, f"Successfully downloaded {success_count} book covers.")
    if error_count:
        messages.warning(request, f"Could not find covers for {error_count} books.")

download_book_covers.short_description = "Download book covers from Open Library"

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'quantity', 'available', 'has_cover')
    list_filter = ('genre', 'created_at')
    search_fields = ('title', 'author', 'isbn', 'genre')
    ordering = ('-created_at',)
    actions = [download_book_covers]
    
    def has_cover(self, obj):
        return bool(obj.cover_image)
    has_cover.boolean = True
    has_cover.short_description = "Has Cover"

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'borrow_date', 'due_date', 'return_date')
    list_filter = ('status', 'borrow_date')
    search_fields = ('user__username', 'book__title')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_librarian')
    list_filter = ('is_librarian',)
    search_fields = ('user__username', 'user__email')

@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'genre')
    search_fields = ('title', 'author', 'user__username') 