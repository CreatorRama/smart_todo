import { useState } from 'react';
import { 
  Calendar, 
  Clock, 
  Edit2, 
  Trash2, 
  CheckCircle2, 
  Circle,
  Tag,
  AlertCircle
} from 'lucide-react';
import { formatDate, getPriorityColor, getStatusColor, getPriorityBorderColor, isOverdue, truncateText } from '../lib/helpers';
import Button from './ui/Button';

const TaskCard = ({ 
  task, 
  onEdit, 
  onDelete, 
  onStatusChange,
  className = '' 
}) => {
  const [isUpdating, setIsUpdating] = useState(false);

  const handleStatusToggle = async () => {
    if (isUpdating) return;
    
    setIsUpdating(true);
    try {
      const newStatus = task.status === 'completed' ? 'pending' : 'completed';
      await onStatusChange(task.id, { status: newStatus });
    } catch (error) {
      console.error('Failed to update status:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const isTaskOverdue = isOverdue(task.deadline);

  // Helper function to safely get category name
  const getCategoryName = (category) => {
    if (!category) return null;
    if (typeof category === 'string') return category;
    if (typeof category === 'object' && category !== null) {
      return category.name || category.title || category.label || null;
    }
    return null;
  };

  // Helper function to safely get tag name
  const getTagName = (tag) => {
    if (typeof tag === 'string') return tag;
    if (typeof tag === 'object' && tag !== null) {
      return tag.name || tag.title || tag.label || tag.id || 'Tag';
    }
    return 'Tag';
  };

  // Helper function to safely render any value as string
  const safeString = (value) => {
    if (value === null || value === undefined) return '';
    if (typeof value === 'string') return value;
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'boolean') return value.toString();
    if (typeof value === 'object') {
      // If it's an object, try to extract a meaningful string representation
      if (value.name) return value.name;
      if (value.title) return value.title;
      if (value.label) return value.label;
      if (value.id) return value.id.toString();
      return 'Object';
    }
    return String(value);
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border-l-4 p-4 hover:shadow-md transition-all duration-200 animate-fade-in ${getPriorityBorderColor(task.priority)} ${className}`}>
      {/* Task Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3 flex-1">
          <button
            onClick={handleStatusToggle}
            disabled={isUpdating}
            className="mt-1 text-gray-400 hover:text-primary-500 transition-colors duration-200 disabled:opacity-50"
          >
            {task.status === 'completed' ? (
              <CheckCircle2 className="w-5 h-5 text-green-500" />
            ) : (
              <Circle className="w-5 h-5" />
            )}
          </button>
          
          <div className="flex-1">
            <h3 className={`font-medium text-gray-900 mb-1 ${task.status === 'completed' ? 'line-through text-gray-500' : ''}`}>
              {safeString(task.title)}
            </h3>
            
            {task.description && (
              <p className="text-sm text-gray-600 mb-2">
                {truncateText(safeString(task.description), 120)}
              </p>
            )}
            
            {/* Tags */}
            {task.tags && Array.isArray(task.tags) && task.tags.length > 0 && (
  <div className="flex flex-wrap gap-1 mb-2">
    {task.tags.slice(0, 3).map((tag, index) => (
      <span
        key={index}
        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
      >
        <Tag className="w-3 h-3 mr-1" />
        {typeof tag === 'string' ? tag : tag.name || tag.id}
      </span>
    ))}
    {task.tags.length > 3 && (
      <span className="text-xs text-gray-500">
        +{task.tags.length - 3} more
      </span>
    )}
  </div>
)}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(task)}
            className="p-2"
          >
            <Edit2 className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(task.id)}
            className="p-2 text-red-500 hover:text-red-700"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
      
      {/* Task Metadata */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center space-x-4">
          {/* Priority */}
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
            {safeString(task.priority).charAt(0).toUpperCase() + safeString(task.priority).slice(1)}
          </span>
          
          {/* Status */}
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
            {safeString(task.status).replace('_', ' ').charAt(0).toUpperCase() + safeString(task.status).replace('_', ' ').slice(1)}
          </span>
          
          {/* Category - Now completely safe */}
          {getCategoryName(task.category) && (
            <span className="text-gray-500">
              {getCategoryName(task.category)}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-3 text-gray-500">
          {/* Duration */}
          {task.estimated_duration && (
            <span className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              {safeString(task.estimated_duration)}m
            </span>
          )}
          
          {/* Deadline */}
          {task.deadline && (
            <span className={`flex items-center ${isTaskOverdue ? 'text-red-500' : ''}`}>
              {isTaskOverdue && <AlertCircle className="w-4 h-4 mr-1" />}
              <Calendar className="w-4 h-4 mr-1" />
              {formatDate(task.deadline)}
            </span>
          )}
        </div>
      </div>
      
      {/* AI Insights */}
      {task.ai_suggestions && task.ai_suggestions.reasoning && (
        <div className="mt-3 p-3 bg-blue-50 rounded-md">
          <p className="text-xs text-blue-700">
            <span className="font-medium">AI Insight:</span> {truncateText(safeString(task.ai_suggestions.reasoning), 100)}
          </p>
        </div>
      )}
      
      {/* Priority Score */}
      {task.priority_score && task.priority_score !== 0.5 && (
        <div className="mt-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>AI Priority Score</span>
            <span>{(Number(task.priority_score) * 100).toFixed(0)}%</span>
          </div>
          <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
            <div 
              className="bg-primary-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${Number(task.priority_score) * 100}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskCard;