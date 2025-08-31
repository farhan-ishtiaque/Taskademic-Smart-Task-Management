# Taskademic - Enhanced Task Management System

A comprehensive Django-based task management application with advanced team collaboration features, inspired by modern project management tools.

## 🆕 Latest Updates (SRS-Driven Enhancements)

### New Features Added:

#### 1. **Team Management System**
- Create and manage teams with role-based access control
- Team roles: Admin, Manager, Member, Viewer
- Multi-team membership support
- Team-based task assignment and collaboration

#### 2. **Project Management**
- Organize tasks within projects
- Project status tracking: Planning, Active, On Hold, Completed, Cancelled
- Project timeline management with start and end dates
- Budget tracking capabilities
- Team-project association

#### 3. **Enhanced Task Features**
- **Task Assignment**: Assign tasks to team members
- **Difficulty Levels**: Easy, Medium, Hard, Expert
- **Time Tracking**: Estimated vs. actual hours
- **Task Hierarchy**: Parent-child task relationships
- **Tagging System**: Flexible tag-based organization
- **Recurring Tasks**: Support for recurring task patterns
- **Enhanced Priority System**: Low, Medium, High, Urgent

#### 4. **Advanced Dashboard**
- Team overview with member information
- Active projects display
- Tasks assigned to you by others
- Enhanced task metadata display (difficulty, assignment, project)
- Improved analytics and progress tracking

#### 5. **Enhanced Kanban Board**
- Display additional task metadata (difficulty, assignee, project)
- Enhanced task creation form with new fields
- Better visual organization with tags and assignments
- Time tracking integration

## 🚀 Features

### Core Functionality
- **User Authentication & Authorization**
  - Secure login/logout system
  - User registration with email verification
  - Profile management
  - Password reset functionality

- **Task Management**
  - Create, edit, delete tasks with rich metadata
  - Priority levels and status tracking
  - Due date management with overdue notifications
  - Task categories with color coding
  - File attachments and comments
  - Task hierarchy (parent-child relationships)
  - Time tracking (estimated vs. actual hours)
  - Difficulty assessment
  - Tag-based organization

- **Team Collaboration**
  - Team creation and management
  - Role-based permissions (Admin, Manager, Member, Viewer)
  - Task assignment to team members
  - Team-based project organization

- **Project Organization**
  - Project creation with timeline management
  - Budget tracking and resource allocation
  - Project status monitoring
  - Team-project associations

### User Interface
- **Dashboard**
  - Comprehensive overview of tasks, teams, and projects
  - Statistics and progress tracking
  - Quick access to recent and upcoming tasks
  - Team and project summaries

- **Kanban Board**
  - Drag-and-drop task management
  - Visual status columns (Todo, In Progress, Review, Done)
  - Real-time updates and task metadata display
  - Enhanced task cards with assignee and project info

- **Calendar View**
  - Monthly calendar with task visualization
  - Due date tracking and overdue highlights
  - Interactive task management

- **Analytics Dashboard**
  - Task completion trends
  - Team productivity metrics
  - Project progress visualization
  - Customizable date ranges

## 🛠️ Technical Stack

- **Backend**: Django 5.2.5
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: HTML5, Tailwind CSS, Alpine.js
- **API**: Django REST Framework
- **Charts**: Chart.js for analytics
- **Authentication**: Django's built-in auth system
- **File Storage**: Django's file handling system

## 📊 Database Schema

### Core Models

#### Task Model (Enhanced)
```python
- title, description
- user (creator), assigned_to (assignee)
- project (FK to Project)
- category (FK to Category)
- priority (low, medium, high, urgent)
- status (todo, in_progress, review, done)
- difficulty (easy, medium, hard, expert)
- due_date, start_date
- estimated_hours, actual_hours
- tags (comma-separated)
- parent_task (self-referencing FK)
- is_recurring, recurring_type
- created_at, updated_at, completed_at
```

#### Team Model
```python
- name, description
- members (M2M through TeamMembership)
- created_by (FK to User)
- created_at
```

#### Project Model
```python
- name, description
- team (FK to Team)
- status (planning, active, on_hold, completed, cancelled)
- start_date, end_date
- budget
- created_by (FK to User)
- created_at, updated_at
```

#### TeamMembership Model
```python
- user (FK to User)
- team (FK to Team)
- role (admin, manager, member, viewer)
- joined_at
```

## 🔧 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd taskademic
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Populate sample data (optional)**
   ```bash
   python populate_sample_data.py
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main application: http://127.0.0.1:8000
   - Admin interface: http://127.0.0.1:8000/admin

## 📚 API Endpoints

### Core Endpoints
- `/api/tasks/` - Task management (CRUD operations)
- `/api/categories/` - Category management
- `/api/comments/` - Task comments
- `/api/teams/` - Team management
- `/api/team-memberships/` - Team membership management
- `/api/projects/` - Project management

### Specialized Endpoints
- `/tasks/api/tasks/kanban_data/` - Kanban board data
- `/tasks/api/tasks/calendar_data/` - Calendar view data
- `/analytics/api/` - Analytics data with date ranges

## 🎯 Usage Examples

### Creating a Team and Project
1. Navigate to Django admin or use the API
2. Create a team with members
3. Create a project associated with the team
4. Assign tasks to team members within the project

### Enhanced Task Creation
1. Go to Kanban board and click "Add Task"
2. Fill in enhanced fields:
   - Title, description, priority
   - Difficulty level
   - Estimated hours
   - Tags (comma-separated)
   - Assignment to team member
   - Project association

### Team Collaboration
1. Join or create teams
2. View team dashboard for member tasks
3. Track project progress
4. Assign and manage tasks across team members

## 🔐 Permissions & Security

- **Team-based access control**: Users can only see teams they're members of
- **Project visibility**: Limited to team members
- **Task assignment**: Only within team contexts
- **Role-based permissions**: Different access levels within teams
- **Secure authentication**: Django's built-in security features

## 🚀 Deployment

The application is ready for deployment with:
- Environment-based configuration
- Static file management
- Database flexibility (SQLite to PostgreSQL)
- Security best practices implemented

## 📈 Future Enhancements

- Real-time notifications
- Advanced reporting and analytics
- Integration with external calendars
- Mobile application
- Advanced recurring task patterns
- File versioning and collaboration
- Time tracking with timers
- Advanced project templates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Check the documentation
- Review the API endpoints
- Examine the sample data in `populate_sample_data.py`
- Use Django admin for advanced management

---

*Last updated: August 28, 2025 - Enhanced with SRS-driven features including team management, project organization, and advanced task capabilities.*
