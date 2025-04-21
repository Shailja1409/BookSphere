from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/popular/', views.popular_books, name='popular_books'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('librarian/', views.librarian_dashboard, name='librarian_dashboard'),
    path('manage-request/<int:borrow_id>/<str:action>/', views.manage_request, name='manage_request'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Book management
    path('book/add/', views.add_book, name='add_book'),
    path('book/<int:pk>/edit/', views.edit_book, name='edit_book'),
    path('book/<int:pk>/delete/', views.delete_book, name='delete_book'),
    
    # Book circulation
    path('book/<int:pk>/issue/', views.issue_book, name='issue_book'),
    path('borrow/<int:borrow_id>/return/', views.return_book, name='return_book'),
    path('borrow/<int:borrow_id>/request-return/', views.request_return, name='request_return'),
    
    # Reports
    path('reports/', views.generate_report, name='generate_report'),
    
    # Book Requests
    path('request-book/', views.request_book, name='request_book'),
    path('manage-book-requests/', views.manage_book_requests, name='manage_book_requests'),
    path('book-request/<int:request_id>/<str:action>/', views.process_book_request, name='process_book_request'),
] 