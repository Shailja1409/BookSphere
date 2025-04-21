# BookSphere - Digital Library Management System

BookSphere is a modern digital library management system built with Django and Bootstrap. It allows students and faculty to manage book borrowing, digital reading access, overdue tracking, and recommendations.

## Features

- User Authentication (Student/Faculty and Librarian roles)
- Book catalog with search and filtering
- Book borrowing and return management
- Overdue tracking system
- User dashboard with borrowing history
- Librarian dashboard with analytics
- Responsive design with Bootstrap 5

## Prerequisites

- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/booksphere.git
cd booksphere
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create MySQL database:
```sql
CREATE DATABASE booksphere CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

5. Configure database settings in `booksphere/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'booksphere',
        'USER': 'your_mysql_user',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

6. Apply migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

7. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

8. Create required directories:
```bash
mkdir media
mkdir static
```

9. Run the development server:
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to access the application.

## Usage

1. Admin Interface:
   - Access at http://127.0.0.1:8000/admin/
   - Use superuser credentials to log in
   - Manage books, users, and borrowing records

2. User Registration:
   - Click "Register" in the navigation bar
   - Fill in the required information
   - Regular users are created as students/faculty by default

3. Librarian Access:
   - Create a user through registration
   - Access admin panel and edit their UserProfile
   - Set is_librarian to True

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 