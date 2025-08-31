# Taskademic - Django Task Management System

A comprehensive task management web application built with Django, inspired by modern productivity tools. Taskademic provides a complete solution for personal and team task management with features like Kanban boards, analytics, and calendar views.

## Features

### 🎯 Core Functionality
- **Task Management**: Create, edit, delete, and organize tasks with priorities and due dates
- **Kanban Board**: Drag-and-drop interface for visual task management
- **Dashboard**: Overview of task statistics and recent activities
- **Calendar View**: Time-based task organization and scheduling
- **Analytics**: Detailed insights into productivity and task completion patterns

### 👥 User Management
- User authentication (registration, login, logout)
- User profiles and settings
- Onboarding experience for new users

### 🏷️ Organization
- **Categories**: Color-coded task categorization
- **Priority Levels**: Low, Medium, High, Urgent
- **Status Tracking**: To Do, In Progress, Review, Done
- **Due Dates**: Deadline management with overdue detection

### 📊 Analytics & Insights
- Task completion statistics
- Priority distribution analysis
- Status-based reporting
- Time-based productivity trends

### 🔧 Technical Features
- RESTful API for all operations
- Responsive design with Tailwind CSS
- Interactive UI components with Alpine.js
- Auto-save functionality
- CSRF protection
- Admin interface for data management

## Technology Stack

### Backend
- **Django 5.2.5**: Web framework
- **Django REST Framework**: API development
- **SQLite**: Database (default, easily configurable)
- **Python 3.10+**: Programming language

### Frontend
- **HTML5 & CSS3**: Structure and styling
- **Tailwind CSS**: Utility-first CSS framework
- **Alpine.js**: Lightweight JavaScript framework
- **Chart.js**: Data visualization

### Additional Tools
- **django-cors-headers**: CORS handling
- **Pillow**: Image processing
- **python-decouple**: Environment variable management

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Taskademic
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install django djangorestframework django-cors-headers pillow python-decouple
   ```

4. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser account**
   ```bash
   python manage.py createsuperuser
   ```

6. **Populate sample data (optional)**
   ```bash
   python manage.py populate_sample_data
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main application: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## Demo Credentials

After running the sample data command, you can use these credentials:

**Demo User:**
- Username: `demo`
- Password: `demo123`

**Admin User:**
- Username: `admin`
- Password: `admin`

## Project Structure

```
Taskademic/
├── taskademic/          # Django project settings
├── dashboard/           # Dashboard app
├── tasks/              # Task management app
├── analytics/          # Analytics and reporting app
├── accounts/           # User authentication app
├── templates/          # HTML templates
├── static/             # CSS, JavaScript, and static files
├── media/              # User uploaded files
├── manage.py           # Django management script
└── README.md          # This file
```

## API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/register/` - User registration
- `POST /accounts/logout/` - User logout

### Tasks
- `GET /tasks/api/tasks/` - List all tasks
- `POST /tasks/api/tasks/` - Create new task
- `GET /tasks/api/tasks/{id}/` - Get specific task
- `PUT /tasks/api/tasks/{id}/` - Update task
- `DELETE /tasks/api/tasks/{id}/` - Delete task
- `GET /tasks/api/tasks/kanban_data/` - Get Kanban board data
- `GET /tasks/api/tasks/stats/` - Get task statistics

### Categories
- `GET /tasks/api/categories/` - List all categories
- `POST /tasks/api/categories/` - Create new category

### Analytics
- `GET /analytics/api/` - Get analytics data

## Usage Guide

### Creating Tasks
1. Navigate to the Dashboard or Kanban board
2. Click "Add Task" button
3. Fill in task details (title, description, priority, due date)
4. Select a category (optional)
5. Click "Create Task"

### Managing Tasks
- **Kanban Board**: Drag and drop tasks between status columns
- **Dashboard**: View task summaries and quick actions
- **Calendar**: View tasks by due date
- **Analytics**: Monitor productivity trends

### User Management
- Register new accounts through the registration page
- Access user settings from the navigation menu
- Admin users can manage all data through the Django admin interface

## Customization

### Adding Custom Categories
```python
# In Django shell or admin interface
from tasks.models import Category
Category.objects.create(name="Custom Category", color="#FF6B6B")
```

### Modifying Task Priorities
Update the `PRIORITY_CHOICES` in `tasks/models.py`:
```python
PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('urgent', 'Urgent'),
    ('critical', 'Critical'),  # Add new priority
]
```

### Styling Customization
- Modify `static/css/style.css` for custom styles
- Update Tailwind classes in templates for layout changes
- Customize color schemes in the CSS variables

## Deployment

### Environment Variables
Create a `.env` file for production settings:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=your-database-url
```

### Production Checklist
- [ ] Set `DEBUG = False` in settings
- [ ] Configure allowed hosts
- [ ] Set up a production database (PostgreSQL recommended)
- [ ] Configure static file serving
- [ ] Set up HTTPS
- [ ] Configure email backend for notifications
- [ ] Set up backup strategy

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code comments for implementation details

## Acknowledgments

- Inspired by modern task management tools like Trello, Asana, and Todoist
- Built with Django's excellent documentation and community resources
- UI design influenced by Tailwind CSS component libraries

---

**Taskademic** - Streamline your productivity with intelligent task management.
