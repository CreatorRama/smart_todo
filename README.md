# Smart Todo - AI-Powered Task Management System

A modern, full-stack task management application with intelligent AI features for task prioritization, suggestions, and context analysis.

## Features

### Frontend Features
- 📋 **Task Management** - Create, edit, and organize tasks with priorities and deadlines
- 🤖 **AI Integration** - Intelligent task prioritization and suggestions
- 📊 **Dashboard** - Visual overview of task statistics and progress
- 📝 **Context Management** - Add daily context for better AI recommendations
- 📱 **Responsive Design** - Mobile-friendly interface
- 🎯 **Smart Filtering** - Filter tasks by status, priority, and categories

### Backend Features
- **AI-Powered Prioritization** - Automatic priority scoring based on deadlines, context, and workload
- **Context Analysis** - Extract insights from various sources (WhatsApp, email, notes, calendar)
- **Task Enhancement** - AI-generated descriptions, tags, and categorization
- **Priority Distribution** - Visual task distribution by priority levels
- **Statistics Dashboard** - Task completion rates and analytics
- **Circuit Breaker Pattern** - Reliable AI service integration with fallbacks

## Tech Stack

### Frontend
- **Framework**: Next.js (Pages Router)
- **UI Library**: React with Hooks
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Date Handling**: date-fns
- **Notifications**: React Hot Toast

### Backend
- **Backend**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL
- **AI Integration**: LM Studio (Local LLM)
- **Additional**: Circuit Breaker pattern, CORS support, Django Filters

## Getting Started

### Prerequisites

- Node.js 16.x or later
- Python 3.8+
- PostgreSQL
- LM Studio running locally (or compatible OpenAI API endpoint)
- npm or yarn

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/CreatorRama/smart_todo.git
cd smart_todo
```

#### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
cd smartTodo
```

**Configure environment variables** (`.env` file):
```env
SECRET_KEY=your-secret-key
DB_NAME=smart_todo
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
LM_STUDIO_BASE_URL=http://localhost:1234
LM_STUDIO_MODEL=llama-3.2-3b-instruct
```

**Setup database:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

**Run backend server:**
```bash
python manage.py runserver
```
Backend will be available at [http://localhost:8000](http://localhost:8000)

#### 3. Frontend Setup

```bash
cd ../frontend
npm install
# or
yarn install
```

**Set up environment variables** (`.env.local`):
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

**Run frontend development server:**
```bash
npm run dev
# or
yarn dev
```
Frontend will be available at [http://localhost:3000](http://localhost:3000)

## Project Structure

```
smart_todo/
├── backend/
│   └── smartTodo/
│       ├── manage.py
│       ├── smartTodo/
│       │   ├── settings.py
│       │   ├── urls.py
│       │   └── wsgi.py
│       ├── tasks/
│       │   ├── models.py
│       │   ├── views.py
│       │   ├── serializers.py
│       │   └── urls.py
│       └── ai_service/
│           ├── views.py
│           └── utils.py
└── frontend/
    ├── pages/
    │   ├── _app.js          # App wrapper with global providers
    │   ├── _document.js     # Custom document structure
    │   └── index.js         # Main application page
    ├── components/
    │   ├── ui/              # Reusable UI components
    │   │   ├── Button.jsx
    │   │   ├── Input.jsx
    │   │   └── Modal.jsx
    │   ├── ContextForm.jsx
    │   ├── ContextHistory.jsx
    │   ├── Dashboard.jsx
    │   ├── TaskCard.jsx
    │   ├── TaskFilters.jsx
    │   ├── TaskForm.jsx
    │   └── TaskList.jsx
    ├── hooks/
    │   ├── useAI.js         # AI integration hooks
    │   ├── useCategories.js
    │   └── useTasks.js      # Task management hooks
    ├── lib/
    │   ├── api.js           # API client and endpoints
    │   ├── context.js       # React context providers
    │   └── utils.js         # Utility functions
    └── styles/
        └── globals.css      # Global styles and Tailwind imports
```

## API Documentation

### Core Endpoints

#### Task Management
- `GET/POST /api/tasks/` - Task CRUD operations
- `PUT/DELETE /api/tasks/{id}/` - Update/delete specific task
- `GET /api/tasks/statistics/` - Task statistics
- `GET /api/tasks/priority_distribution/` - Priority distribution

#### Categories & Tags
- `GET/POST /api/categories/` - Category management
- `GET /api/tags/` - Task tags

#### Context & AI
- `GET/POST /api/context-entries/` - Context data management
- `POST /api/ai/task-suggestions/` - Get AI task recommendations
- `POST /api/ai/task-prioritization/` - Bulk task prioritization

### Example API Usage

#### Create a Task
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

#### Get AI Task Suggestions
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

## Key Components

### Frontend Components
- **Dashboard** - Overview with statistics and charts
- **TaskCard** - Individual task display with actions
- **TaskForm** - Create/edit task modal with AI suggestions
- **ContextForm** - Add daily context for AI recommendations
- **TaskFilters** - Filter and sort tasks

### Backend Models
- **Task** - Core task entity with AI enhancement fields
- **Category** - Task categorization with usage tracking
- **ContextEntry** - External data sources for AI analysis
- **TaskTag** - Flexible tagging system
- **AIProcessingLog** - AI operation logging and monitoring

## AI Integration

The system uses LM Studio for local AI processing with:
- Circuit breaker pattern for reliability
- Fallback prioritization when AI is unavailable
- Comprehensive logging for AI operations
- JSON-structured prompts for consistent responses
- Real-time task enhancement and suggestions

## Development Scripts

### Frontend
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Backend
```bash
python manage.py runserver    # Start development server
python manage.py migrate      # Apply database migrations
python manage.py test         # Run tests
python manage.py collectstatic # Collect static files
```

## Environment Variables

### Frontend
| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api` |

### Backend
| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DB_NAME` | Database name | Yes |
| `DB_USER` | Database user | Yes |
| `DB_PASSWORD` | Database password | Yes |
| `DB_HOST` | Database host | Yes |
| `DB_PORT` | Database port | Yes |
| `LM_STUDIO_BASE_URL` | LM Studio API URL | Yes |
| `LM_STUDIO_MODEL` | AI model name | Yes |

## Configuration

Key backend settings:
- REST Framework pagination (20 items/page)
- CORS support for frontend integration
- Circuit breaker configuration for AI services
- Comprehensive error handling and logging

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

MIT License

## Support

For support and questions, please open an issue on the GitHub repository.

---

**Note**: Make sure to have LM Studio running with a compatible model before starting the application to enable AI features.