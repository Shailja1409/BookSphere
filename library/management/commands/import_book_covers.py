from django.core.management.base import BaseCommand
from library.models import Book
from django.core.files.base import ContentFile
import requests
from urllib.parse import quote_plus
import time

class Command(BaseCommand):
    help = 'Import book covers from Open Library for books that have no cover'
    
    def get_cover_image(self, title, author, isbn=None):
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
                self.stdout.write(self.style.WARNING(f"Error fetching by ISBN {isbn}: {e}"))
        
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
            self.stdout.write(self.style.WARNING(f"Error fetching by title/author {title}/{author}: {e}"))
        
        return None
    
    def handle(self, *args, **kwargs):
        books = Book.objects.filter(cover_image='')
        total = books.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("All books already have covers!"))
            return
        
        self.stdout.write(self.style.NOTICE(f"Starting download of {total} book covers..."))
        
        success = 0
        for i, book in enumerate(books):
            self.stdout.write(f"Processing ({i+1}/{total}): {book.title} by {book.author}")
            
            # Get the cover image
            image_data = self.get_cover_image(book.title, book.author, book.isbn)
            
            if image_data:
                # Save the image to the book
                filename = f"{book.title.replace(' ', '_')[:30]}.jpg"
                book.cover_image.save(filename, ContentFile(image_data), save=True)
                success += 1
                self.stdout.write(self.style.SUCCESS(f"Downloaded cover for: {book.title}"))
            else:
                self.stdout.write(self.style.ERROR(f"No cover found for: {book.title}"))
            
            # Be nice to the API
            time.sleep(1)
        
        self.stdout.write(self.style.SUCCESS(
            f"Download complete. Successfully added {success} covers out of {total} books."
        )) 