# Smart Todo Backend

An AI-powered task management API built with Django REST Framework that provides intelligent task prioritization, context analysis, and task enhancement features.

## Features

- **Task Management**: Create, update, and organize tasks with categories and tags
- **AI-Powered Prioritization**: Automatic priority scoring based on deadlines, context, and workload
- **Context Analysis**: Extract insights from various sources (WhatsApp, email, notes, calendar)
- **Task Enhancement**: AI-generated descriptions, tags, and categorization
- **Priority Distribution**: Visual task distribution by priority levels
- **Statistics Dashboard**: Task completion rates and analytics

## Tech Stack

- **Backend**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL
- **AI Integration**: LM Studio (Local LLM)
- **Additional**: Circuit Breaker pattern, CORS support, Django Filters

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL
- LM Studio running locally (or compatible OpenAI API endpoint)

### Installation

1. Clone and setup:
```bash
git clone https://github.com/CreatorRama/smart_todo.git
cd backend
pip install -r requirements.txt
cd smartTodo
```

2. Configure environment variables:
```bash
# .env file
SECRET_KEY=your-secret-key
DB_NAME=smart_todo
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
LM_STUDIO_BASE_URL=http://localhost:1234
LM_STUDIO_MODEL=llama-3.2-3b-instruct
```

3. Setup database:
```bash
python manage.py migrate
python manage.py createsuperuser
```

4. Run server:
```bash
python manage.py runserver
```

## API Endpoints

### Core Resources
- `GET/POST /api/tasks/` - Task management
- `GET/POST /api/categories/` - Category management
- `GET/POST /api/context-entries/` - Context data
- `GET /api/tags/` - Task tags

### AI Features
- `POST /api/ai/task-suggestions/` - Get AI task recommendations
- `POST /api/ai/task-prioritization/` - Bulk task prioritization

### Analytics
- `GET /api/tasks/statistics/` - Task statistics
- `GET /api/tasks/priority_distribution/` - Priority distribution

## Example API Usage

### Create a Task
```json
POST /api/tasks/
{
  "title": "Complete project documentation",
  "description": "Write comprehensive docs for the API",
  "priority": "high",
  "deadline": "2024-12-31T23:59:59Z",
  "tags": ["documentation", "urgent"]
}
```

### Get AI Task Suggestions
```json
POST /api/ai/task-suggestions/
{
  "task_data": {
    "title": "Review quarterly report",
    "description": "Analyze Q4 performance metrics"
  },
  "user_preferences": {"work_hours": "9-17"},
  "current_task_load": 5
}
```

## Models Overview

- **Task**: Core task entity with AI enhancement fields
- **Category**: Task categorization with usage tracking
- **ContextEntry**: External data sources for AI analysis
- **TaskTag**: Flexible tagging system
- **AIProcessingLog**: AI operation logging and monitoring

## AI Integration

The system uses LM Studio for local AI processing with:
- Circuit breaker pattern for reliability
- Fallback prioritization when AI is unavailable
- Comprehensive logging for AI operations
- JSON-structured prompts for consistent responses

## Configuration

Key settings in `settings.py`:
- REST Framework pagination (20 items/page)
- CORS support for frontend integration
- Circuit breaker configuration
- AI service timeout and retry settings

## Development

The codebase follows Django best practices with:
- Proper serializer validation
- ViewSet-based API structure
- Comprehensive error handling
- Logging for debugging and monitoring

## License

[Your License Here]