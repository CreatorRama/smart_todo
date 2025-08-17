import { useState, useEffect } from 'react';
import Head from 'next/head';
import {
  Plus,
  LayoutDashboard,
  CheckSquare,
  MessageCircle,
  Settings,
  Menu,
  X,
  Sparkles,
  Wand2
} from 'lucide-react';
import { useTasks } from '../hooks/useTasks';
import { useAI } from '../hooks/useAI';
import { contextAPI } from '../lib/api';
import TaskCard from '../components/TaskCard';
import TaskForm from '../components/TaskForm';
import ContextForm from '../components/ContextForm';
import TaskFilters from '../components/TaskFilters';
import Dashboard from '../components/Dashboard';
import ContextHistory from '../components/ContextHistory';
import Button from '../components/ui/Button';
import toast from 'react-hot-toast';
import ErrorBoundary from '../components/ErrorBoundary';

export default function Home() {
  // State management
  const [currentView, setCurrentView] = useState('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isTaskFormOpen, setIsTaskFormOpen] = useState(false);
  const [isContextFormOpen, setIsContextFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [contextEntries, setContextEntries] = useState([]);
  const [selectedTasks, setSelectedTasks] = useState([]);

  // Custom hooks
  const {
    tasks,
    loading: tasksLoading,
    createTask,
    updateTask,
    deleteTask,
    refetch: refetchTasks,
    updateParams: updateTaskFilters
  } = useTasks();

  const { loading: aiLoading, prioritizeTasks } = useAI();

  // Load context entries
  useEffect(() => {
    const loadContextEntries = async () => {
      try {
        const response = await contextAPI.getContextEntries({ page_size: 10 });
        // Ensure we're always working with an array
        const entries = Array.isArray(response.data)
          ? response.data
          : (response.data.results || []);
        setContextEntries(entries);
      } catch (error) {
        console.error('Failed to load context entries:', error);
      }
    };

    loadContextEntries();
  }, []);

  // Navigation items
  const navigation = [
    {
      id: 'dashboard',
      name: 'Dashboard',
      icon: LayoutDashboard,
      count: null
    },
    {
      id: 'tasks',
      name: 'Tasks',
      icon: CheckSquare,
      count: tasks.length
    },
    {
      id: 'context',
      name: 'Context',
      icon: MessageCircle,
      count: contextEntries.length
    },
  ];

  // Event handlers
  const handleTaskCreate = async (taskData) => {
    await createTask(taskData);
    setIsTaskFormOpen(false);
  };

  const handleTaskUpdate = async (taskData) => {
    await updateTask(editingTask.id, taskData);
    setEditingTask(null);
  };

  const handleTaskEdit = (task) => {
    setEditingTask(task);
    setIsTaskFormOpen(true);
  };

  const handleTaskDelete = async (taskId) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      await deleteTask(taskId);
    }
  };

  const handleTaskStatusChange = async (taskId, statusData) => {
    await updateTask(taskId, statusData);
  };

  const handleContextSubmit = (newEntries) => {
    setContextEntries(prev => [...newEntries, ...prev]);
    toast.success('Context added successfully');
  };

  const handleBulkPrioritize = async () => {
    if (selectedTasks.length === 0) {
      toast.error('Please select tasks to prioritize');
      return;
    }

    try {
      await prioritizeTasks(
        selectedTasks,
        contextEntries.slice(0, 10).map(entry => entry.id)
      );
      await refetchTasks();
      setSelectedTasks([]);
      toast.success('Tasks prioritized successfully');
    } catch (error) {
      console.error('Bulk prioritization failed:', error);
    }
  };

  const toggleTaskSelection = (taskId) => {
    setSelectedTasks(prev =>
      prev.includes(taskId)
        ? prev.filter(id => id !== taskId)
        : [...prev, taskId]
    );
  };

  // Render navigation
  const renderNavigation = () => (
    <nav className="space-y-1">
      {navigation.map((item) => {
        const isActive = currentView === item.id;
        return (
          <button
            key={item.id}
            onClick={() => {
              setCurrentView(item.id);
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${isActive
              ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-500'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
          >
            <item.icon className="w-5 h-5 mr-3" />
            {item.name}
            {item.count !== null && (
              <span className={`ml-auto px-2 py-1 text-xs rounded-full ${isActive
                ? 'bg-primary-200 text-primary-800'
                : 'bg-gray-200 text-gray-600'
                }`}>
                {item.count}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );

  // Render main content based on current view
  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;

      case 'tasks':
        return (
          <div className="space-y-6">
            {/* Task Actions */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center space-x-4">
                <Button
                  onClick={() => {
                    setEditingTask(null);
                    setIsTaskFormOpen(true);
                  }}
                  className="inline-flex items-center"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Task
                </Button>

                {selectedTasks.length > 0 && (
                  <Button
                    onClick={handleBulkPrioritize}
                    loading={aiLoading}
                    variant="outline"
                    className="inline-flex items-center"
                  >
                    <Wand2 className="w-4 h-4 mr-2" />
                    AI Prioritize ({selectedTasks.length})
                  </Button>
                )}
              </div>

              {selectedTasks.length > 0 && (
                <button
                  onClick={() => setSelectedTasks([])}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear selection
                </button>
              )}
            </div>

            {/* Task Filters */}
            <TaskFilters onFiltersChange={updateTaskFilters} />

            {/* Task List */}
            {tasksLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="bg-white rounded-lg shadow-sm border p-4 animate-pulse">
                    <div className="space-y-3">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                      <div className="flex space-x-2">
                        <div className="h-6 bg-gray-200 rounded-full w-16"></div>
                        <div className="h-6 bg-gray-200 rounded-full w-20"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : tasks.length === 0 ? (
              <div className="text-center py-12">
                <CheckSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks yet</h3>
                <p className="text-gray-600 mb-4">
                  Create your first task to get started with AI-powered task management.
                </p>
                <Button
                  onClick={() => {
                    setEditingTask(null);
                    setIsTaskFormOpen(true);
                  }}
                  className="inline-flex items-center"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Task
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {tasks.map(task => (
                  <div key={task.id} className="relative">
                    {/* Selection checkbox */}
                    <input
                      type="checkbox"
                      checked={selectedTasks.includes(task.id)}
                      onChange={() => toggleTaskSelection(task.id)}
                      className="absolute top-2 left-2 z-10 w-4 h-4 text-primary-600 bg-white border-gray-300 rounded focus:ring-primary-500"
                    />

                    <TaskCard
                      task={task}
                      onEdit={handleTaskEdit}
                      onDelete={handleTaskDelete}
                      onStatusChange={handleTaskStatusChange}
                      className={selectedTasks.includes(task.id) ? 'ring-2 ring-primary-500 ring-opacity-50' : ''}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case 'context':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Daily Context</h2>
                <p className="text-gray-600">Add your daily context to get AI-powered task suggestions.</p>
              </div>

              <Button
                onClick={() => setIsContextFormOpen(true)}
                className="inline-flex items-center"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Context
              </Button>
            </div>

            <ErrorBoundary>
              <ContextHistory />
            </ErrorBoundary>
          </div>
        );

      default:
        return <Dashboard />;
    }
  };

  return (
    <>
      <Head>
        <title>Smart Todo List - AI-Powered Task Management</title>
        <meta name="description" content="Intelligent task management with AI-powered prioritization, deadline suggestions, and context-aware recommendations." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Mobile menu button */}
        <div className="lg:hidden">
          <div className="bg-white border-b px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-8 h-8 text-primary-500" />
                <h1 className="text-xl font-bold text-gray-900">Smart Todo</h1>
              </div>
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2 text-gray-600 hover:text-gray-900"
              >
                {isMobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="lg:flex">
          {/* Sidebar */}
          <div className={`
            lg:w-64 lg:flex-shrink-0
            ${isMobileMenuOpen ? 'block' : 'hidden lg:block'}
          `}>
            <div className="h-full lg:h-screen bg-white border-r border-gray-200 lg:sticky lg:top-0">
              <div className="p-6">
                {/* Logo */}
                <div className="hidden lg:flex items-center space-x-2 mb-8">
                  <Sparkles className="w-8 h-8 text-primary-500" />
                  <h1 className="text-xl font-bold text-gray-900">Smart Todo</h1>
                </div>

                {/* Navigation */}
                {renderNavigation()}

                {/* AI Status */}
                <div className="mt-8 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                  <div className="flex items-center mb-2">
                    <Sparkles className="w-4 h-4 text-blue-500 mr-2" />
                    <span className="text-sm font-medium text-blue-900">AI Assistant</span>
                  </div>
                  <p className="text-xs text-blue-700">
                    Ready to help with task prioritization and smart suggestions.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 lg:max-w-none">
            <div className="p-6 lg:p-8">
              {renderContent()}
            </div>
          </div>
        </div>

        {/* Modals */}
        <TaskForm
          isOpen={isTaskFormOpen}
          onClose={() => {
            setIsTaskFormOpen(false);
            setEditingTask(null);
          }}
          onSubmit={editingTask ? handleTaskUpdate : handleTaskCreate}
          initialData={editingTask}
          contextEntries={contextEntries.slice(0, 10)}
        />

        <ContextForm
          isOpen={isContextFormOpen}
          onClose={() => setIsContextFormOpen(false)}
          onSubmit={handleContextSubmit}
        />
      </div>
    </>
  );
}