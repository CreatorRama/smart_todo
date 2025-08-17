import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Filter,
  Search,
  SortAsc,
  Tag,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  X
} from 'lucide-react';
import { categoriesAPI, tagsAPI } from '../lib/api';
import Button from './ui/Button';
import Input from './ui/Input';

const TaskFilters = ({
  onFiltersChange,
  currentFilters = {},
  className = '',
  isLoading = false
}) => {
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [error, setError] = useState(null);
  const [searchDebounceTimer, setSearchDebounceTimer] = useState(null);

  // Default filters with better structure
  const defaultFilters = useMemo(() => ({
    search: '',
    category: '',
    priority: '',
    status: '',
    tag: '',
    ordering: '-priority_score'
  }), []);

  const [filters, setFilters] = useState({
    ...defaultFilters,
    ...currentFilters
  });

  // Priority options
  const priorityOptions = useMemo(() => [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'urgent', label: 'Urgent' }
  ], []);

  // Status options
  const statusOptions = useMemo(() => [
    { value: 'pending', label: 'Pending' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' }
  ], []);

  // Sort options
  const sortOptions = useMemo(() => [
    { value: '-priority_score', label: 'Priority Score (High to Low)' },
    { value: 'priority_score', label: 'Priority Score (Low to High)' },
    { value: '-created_at', label: 'Newest First' },
    { value: 'created_at', label: 'Oldest First' },
    { value: 'deadline', label: 'Deadline (Earliest First)' },
    { value: '-deadline', label: 'Deadline (Latest First)' },
    { value: 'title', label: 'Title (A-Z)' },
    { value: '-title', label: 'Title (Z-A)' }
  ], []);

  // Helper function to safely extract array data from API response
  const extractArrayData = useCallback((data, dataType) => {
    if (Array.isArray(data)) {
      return data;
    } else if (data && Array.isArray(data.results)) {
      return data.results;
    } else if (data && data.data && Array.isArray(data.data)) {
      return data.data;
    } else {
      console.warn(`${dataType} data is not in expected format:`, data);
      return [];
    }
  }, []);

  // Load filter data with better error handling
  useEffect(() => {
    let isMounted = true;

    const loadFilterData = async () => {
      setIsLoadingData(true);
      setError(null);

      try {
        const [categoriesRes, tagsRes] = await Promise.all([
          categoriesAPI.getCategories().catch(err => ({ data: [], error: err })),
          tagsAPI.getTags().catch(err => ({ data: [], error: err }))
        ]);

        if (!isMounted) return;

        // Handle categories
        if (categoriesRes.error) {
          console.warn('Failed to load categories:', categoriesRes.error);
        } else {
          const categoriesData = extractArrayData(categoriesRes.data, 'Categories');
          setCategories(categoriesData);
        }

        // Handle tags
        if (tagsRes.error) {
          console.warn('Failed to load tags:', tagsRes.error);
        } else {
          const tagsData = extractArrayData(tagsRes.data, 'Tags');
          setTags(tagsData);
        }

      } catch (error) {
        if (isMounted) {
          console.error('Failed to load filter data:', error);
          setError('Failed to load filter options. Some filters may not be available.');
          setCategories([]);
          setTags([]);
        }
      } finally {
        if (isMounted) {
          setIsLoadingData(false);
        }
      }
    };

    loadFilterData();

    return () => {
      isMounted = false;
    };
  }, [extractArrayData]);

  // Debounced search handler
  const handleSearchChange = useCallback((value) => {
    setFilters(prev => ({ ...prev, search: value }));

    // Clear existing timer
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }

    // Set new timer
    const timer = setTimeout(() => {
      const newFilters = { ...filters, search: value };
      const cleanFilters = Object.fromEntries(
        Object.entries(newFilters).filter(([_, v]) => v !== '')
      );
      onFiltersChange(cleanFilters);
    }, 300);

    setSearchDebounceTimer(timer);
  }, [searchDebounceTimer, filters, onFiltersChange]);

  // Generic filter change handler
  const handleFilterChange = useCallback((key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);

    // Remove empty filters
    const cleanFilters = Object.fromEntries(
      Object.entries(newFilters).filter(([_, v]) => v !== '')
    );

    onFiltersChange(cleanFilters);
  }, [filters, onFiltersChange]);

  // Reset filters
  const resetFilters = useCallback(() => {
    setFilters(defaultFilters);
    onFiltersChange({ ordering: '-priority_score' });

    // Clear search debounce timer
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
      setSearchDebounceTimer(null);
    }
  }, [defaultFilters, onFiltersChange, searchDebounceTimer]);

  // Clear individual filter
  const clearFilter = useCallback((key) => {
    handleFilterChange(key, '');
  }, [handleFilterChange]);

  // Check if there are active filters
  const hasActiveFilters = useMemo(() =>
    Object.entries(filters).some(([key, value]) =>
      value !== '' && value !== defaultFilters[key]
    ), [filters, defaultFilters]);

  // Count active filters
  const activeFilterCount = useMemo(() =>
    Object.entries(filters).filter(([key, value]) =>
      value !== '' && value !== defaultFilters[key]
    ).length, [filters, defaultFilters]);

  // Safe tag/category name extraction
  const getDisplayName = useCallback((item) => {
    if (typeof item === 'string') return item;
    if (typeof item === 'object' && item) {
      return item.name || item.title || item.label || item.id || 'Unknown';
    }
    return 'Unknown';
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
      }
    };
  }, [searchDebounceTimer]);

  return (
    <div className={`bg-white rounded-lg shadow-sm border transition-all duration-200 ${className} ${isLoading ? 'opacity-50' : ''}`}>
      {/* Error Banner */}
      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded-t-lg">
          <p className="text-sm text-yellow-700">{error}</p>
        </div>
      )}

      <div className="p-4">
        {/* Search and Toggle */}
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="text"
              placeholder="Search tasks..."
              value={filters.search}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10 pr-8"
              disabled={isLoading}
              aria-label="Search tasks"
            />
            {filters.search && (
              <button
                onClick={() => handleSearchChange('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <Button
            variant="outline"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center whitespace-nowrap"
            disabled={isLoading}
            aria-expanded={isExpanded}
            aria-controls="filter-panel"
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
            {activeFilterCount > 0 && (
              <span className="ml-2 bg-primary-500 text-white text-xs rounded-full px-2 py-0.5 min-w-[20px] text-center">
                {activeFilterCount}
              </span>
            )}
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 ml-2" />
            ) : (
              <ChevronDown className="w-4 h-4 ml-2" />
            )}
          </Button>
        </div>

        {/* Active Filter Tags */}
        {hasActiveFilters && (
          <div className="mb-4 flex flex-wrap gap-2">
            {Object.entries(filters).map(([key, value]) => {
              if (!value || value === defaultFilters[key]) return null;

              let displayValue = value;
              if (key === 'category') {
                const category = categories.find(c => c.id?.toString() === value?.toString());
                displayValue = category ? getDisplayName(category) : value;
              } else if (key === 'priority' || key === 'status') {
                const option = [...priorityOptions, ...statusOptions].find(opt => opt.value === value);
                displayValue = option?.label || value;
              } else if (key === 'ordering') {
                const option = sortOptions.find(opt => opt.value === value);
                displayValue = option?.label || value;
              }

              return (
                <span
                  key={key}
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                >
                  <span className="capitalize font-medium mr-1">{key.replace('_', ' ')}:</span>
                  <span className="truncate max-w-24">{displayValue}</span>
                  <button
                    onClick={() => clearFilter(key)}
                    className="ml-2 text-primary-600 hover:text-primary-800 transition-colors"
                    aria-label={`Remove ${key} filter`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              );
            })}
          </div>
        )}

        {/* Expanded Filters */}
        {isExpanded && (
          <div id="filter-panel" className="space-y-4 pt-4 border-t animate-slide-down">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Category Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category
                </label>
                <select
                  value={filters.category}
                  onChange={(e) => handleFilterChange('category', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                  disabled={isLoading || isLoadingData}
                  aria-label="Filter by category"
                >
                  <option value="">All Categories</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {getDisplayName(category)}
                    </option>
                  ))}
                </select>
                {isLoadingData && (
                  <p className="text-xs text-gray-500 mt-1">Loading categories...</p>
                )}
              </div>

              {/* Priority Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <select
                  value={filters.priority}
                  onChange={(e) => handleFilterChange('priority', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                  disabled={isLoading}
                  aria-label="Filter by priority"
                >
                  <option value="">All Priorities</option>
                  {priorityOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                  disabled={isLoading}
                  aria-label="Filter by status"
                >
                  <option value="">All Statuses</option>
                  {statusOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Sort Order */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <SortAsc className="inline w-4 h-4 mr-1" />
                  Sort By
                </label>
                <select
                  value={filters.ordering}
                  onChange={(e) => handleFilterChange('ordering', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                  disabled={isLoading}
                  aria-label="Sort tasks by"
                >
                  {sortOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Tags Filter */}
            {tags.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Tag className="inline w-4 h-4 mr-1" />
                  Tags
                </label>
                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                  <button
                    onClick={() => handleFilterChange('tag', '')}
                    disabled={isLoading}
                    className={`px-3 py-1 text-sm rounded-full border transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${filters.tag === ''
                      ? 'bg-primary-500 text-white border-primary-500'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    aria-pressed={filters.tag === ''}
                  >
                    All Tags
                  </button>
                  {tags.slice(0, 15).map(tag => {
                    const tagName = getDisplayName(tag);
                    const tagValue = typeof tag === 'string' ? tag : tag.name || tag.id;

                    return (
                      <button
                        key={tag.id || tagName}
                        onClick={() => handleFilterChange('tag', tagValue)}
                        disabled={isLoading}
                        className={`px-3 py-1 text-sm rounded-full border transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed truncate max-w-32 ${filters.tag === tagValue
                          ? 'bg-primary-500 text-white border-primary-500'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                          }`}
                        title={tagName}
                        aria-pressed={filters.tag === tagValue}
                      >
                        {tagName}
                      </button>
                    );
                  })}
                  {tags.length > 15 && (
                    <span className="text-xs text-gray-500 px-3 py-1">
                      +{tags.length - 15} more
                    </span>
                  )}
                </div>
                {isLoadingData && (
                  <p className="text-xs text-gray-500 mt-2">Loading tags...</p>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-between items-center pt-2">
              <div className="text-sm text-gray-500">
                {activeFilterCount > 0 && `${activeFilterCount} filter${activeFilterCount !== 1 ? 's' : ''} active`}
              </div>

              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  onClick={resetFilters}
                  disabled={isLoading}
                  className="text-sm"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset All Filters
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskFilters;