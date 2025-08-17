import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import {
    Calendar,
    Clock,
    Tag,
    Wand2,
    Sparkles,
    ChevronDown
} from 'lucide-react';
import { categoriesAPI, tagsAPI } from '../lib/api';
import { useAI } from '../hooks/useAI';
import Modal from './ui/Modal';
import Button from './ui/Button';
import Input from './ui/Input';
import toast from 'react-hot-toast';

const TaskForm = ({
    isOpen,
    onClose,
    onSubmit,
    initialData = null,
    contextEntries = []
}) => {
    const [categories, setCategories] = useState([]);
    const [popularTags, setPopularTags] = useState([]);
    const [aiSuggestions, setAiSuggestions] = useState(null);
    const [isLoadingData, setIsLoadingData] = useState(false);
    const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);

    const { loading: aiLoading, getTaskSuggestions } = useAI();

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
        setValue,
        watch,
        reset
    } = useForm({
        defaultValues: {
            title: '',
            description: '',
            category: '',
            priority: 'medium',
            status: 'pending',
            deadline: '',
            estimated_duration: '',
            tags: []
        }
    });

    const watchedValues = watch();

    // Helper function to safely get tag name
    const getTagName = (tag) => {
        if (typeof tag === 'string') return tag;
        if (typeof tag === 'object' && tag !== null) {
            return tag.name || tag.id || 'Tag';
        }
        return 'Tag';
    };

    // Load initial data
    useEffect(() => {
        const loadData = async () => {
            setIsLoadingData(true);
            try {
                const [categoriesRes, tagsRes] = await Promise.all([
                    categoriesAPI.getCategories(),
                    tagsAPI.getPopularTags()
                ]);

                // Default categories if empty
                const loadedCategories = categoriesRes.data.length > 0
                    ? categoriesRes.data
                    : [
                        { id: 1, name: 'Work', color: '#3B82F6' },
                        { id: 2, name: 'Personal', color: '#10B981' },
                        { id: 3, name: 'Study', color: '#F59E0B' },
                        { id: 4, name: 'Health', color: '#EF4444' }
                    ];

                setCategories(loadedCategories);
                setPopularTags(tagsRes.data || []);
            } catch (error) {
                console.error('Failed to load form data:', error);
            } finally {
                setIsLoadingData(false);
            }
        };

        if (isOpen) {
            loadData();
        }
    }, [isOpen]);

    // Set initial data when editing
    useEffect(() => {
        if (initialData && isOpen) {
            reset({
                title: initialData.title || '',
                description: initialData.description || '',
                category: initialData.category?.id || initialData.category || '',
                priority: initialData.priority || 'medium',
                status: initialData.status || 'pending',
                deadline: initialData.deadline ? initialData.deadline.split('T')[0] : '',
                estimated_duration: initialData.estimated_duration || '',
                tags: initialData.tags ? initialData.tags.map(tag => getTagName(tag)) : []
            });
        } else if (isOpen) {
            reset({
                title: '',
                description: '',
                category: '',
                priority: 'medium',
                status: 'pending',
                deadline: '',
                estimated_duration: '',
                tags: []
            });
        }
    }, [initialData, isOpen, reset]);

    const handleAIEnhance = async () => {
        if (!watchedValues.title.trim()) {
            toast.error('Please enter a task title first');
            return;
        }

        const CovertToArray=(obj)=>{
            const arr=[]
            Object.entries(obj).map(([key,value])=>{
                
                if(value.id) arr.push(value.id)
            })

            console.log(arr);

            return arr
        }

        try {
            console.log(typeof(contextEntries));
            console.log(contextEntries);
            const suggestions = await getTaskSuggestions(
                {
                    title: watchedValues.title,
                    description: watchedValues.description,
                    category: watchedValues.category,
                    priority: watchedValues.priority,
                    estimated_duration: parseInt(watchedValues.estimated_duration) || null
                },
                CovertToArray(contextEntries),
                {},
                0
            );

            setAiSuggestions(suggestions);

            // Apply AI suggestions
            if (suggestions.enhanced_description && !watchedValues.description.trim()) {
                setValue('description', suggestions.enhanced_description);
            }

            if (suggestions.suggested_category && !watchedValues.category) {
                const suggestedCat = categories.find(c =>
                    c.name.toLowerCase() === suggestions.suggested_category.toLowerCase()
                );
                if (suggestedCat) {
                    setValue('category', suggestedCat.id);
                    toast.success(`AI suggested: ${suggestedCat.name}`, {
                        icon: <Tag color={suggestedCat.color} size={16} />,
                    });
                }
            }

            if (suggestions.suggested_priority) {
                setValue('priority', suggestions.suggested_priority);
            }

            if (suggestions.suggested_tags && suggestions.suggested_tags.length > 0) {
                setValue('tags', suggestions.suggested_tags.map(tag => getTagName(tag)));
            }

            if (suggestions.estimated_duration && !watchedValues.estimated_duration) {
                setValue('estimated_duration', suggestions.estimated_duration.toString());
            }

            if (suggestions.suggested_deadline && !watchedValues.deadline) {
                const deadline = new Date(suggestions.suggested_deadline);
                setValue('deadline', deadline.toISOString().split('T')[0]);
            }

            toast.success('AI suggestions applied!');
        } catch (error) {
            console.error('Failed to get AI suggestions:', error);
            toast.error('Failed to get AI suggestions');
        }
    };

    const onFormSubmit = async (data) => {
        try {
            const formattedData = {
                ...data,
                estimated_duration: data.estimated_duration ? parseInt(data.estimated_duration) : null,
                deadline: data.deadline || null,
                category: data.category ? Number(data.category) : null,
                tags: Array.isArray(data.tags) ? data.tags : data.tags.split(',').map(t => t.trim()).filter(Boolean)
            };

            await onSubmit(formattedData);
            onClose();
            reset();
            setAiSuggestions(null);
        } catch (error) {
            console.error('Failed to submit task:', error);
            toast.error('Failed to save task');
        }
    };

    const handleTagClick = (tagName) => {
        const currentTags = Array.isArray(watchedValues.tags) ? watchedValues.tags : [];
        if (!currentTags.includes(tagName)) {
            setValue('tags', [...currentTags, tagName]);
        }
    };

    const removeTag = (tagToRemove) => {
        const currentTags = Array.isArray(watchedValues.tags) ? watchedValues.tags : [];
        setValue('tags', currentTags.filter(tag => tag !== tagToRemove));
    };

    const selectCategory = (categoryId) => {
        setValue('category', categoryId);
        setShowCategoryDropdown(false);
    };

    const getCategoryColor = (categoryId) => {
        return categories.find(c => c.id === categoryId)?.color || '#6B7280';
    };

    if (!isOpen) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? 'Edit Task' : 'Create New Task'}
            size="lg"
        >
            <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
                {/* Title */}
                <div>
                    <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                        Task Title *
                    </label>
                    <Input
                        id="title"
                        {...register('title', { required: 'Task title is required' })}
                        error={!!errors.title}
                        placeholder="Enter task title..."
                    />
                    {errors.title && (
                        <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
                    )}
                </div>

                {/* AI Enhancement Button */}
                <div className="flex justify-center">
                    <Button
                        type="button"
                        onClick={handleAIEnhance}
                        loading={aiLoading}
                        variant="outline"
                        className="inline-flex items-center"
                    >
                        <Wand2 className="w-4 h-4 mr-2" />
                        Enhance with AI
                    </Button>
                </div>

                {/* AI Suggestions Display */}
                {aiSuggestions && (
                    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center mb-3">
                            <Sparkles className="w-5 h-5 text-blue-500 mr-2" />
                            <h3 className="text-sm font-medium text-blue-900">AI Suggestions Applied</h3>
                        </div>
                        {aiSuggestions.reasoning && (
                            <p className="text-sm text-blue-700 mb-2">{aiSuggestions.reasoning}</p>
                        )}
                        {aiSuggestions.context_analysis?.context_summary && (
                            <div className="text-xs text-blue-600">
                                <strong>Context Analysis:</strong> {aiSuggestions.context_analysis.context_summary}
                            </div>
                        )}
                    </div>
                )}

                {/* Description */}
                <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                        Description
                    </label>
                    <textarea
                        id="description"
                        {...register('description')}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        rows={4}
                        placeholder="Describe the task in detail..."
                    />
                </div>

                {/* Category and Priority Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Enhanced Category Selector */}
                    <div className="relative">
                        <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                            Category
                        </label>
                        <div className="relative">
                            <button
                                type="button"
                                onClick={() => setShowCategoryDropdown(!showCategoryDropdown)}
                                className="w-full flex items-center justify-between px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                            >
                                <div className="flex items-center">
                                    {watchedValues.category ? (
                                        <>
                                            <span
                                                className="w-3 h-3 rounded-full mr-2"
                                                style={{ backgroundColor: getCategoryColor(watchedValues.category) }}
                                            />
                                            <span>{categories.find(c => c.id === watchedValues.category)?.name || 'Select category'}</span>
                                        </>
                                    ) : (
                                        <span className="text-gray-400">Select category</span>
                                    )}
                                </div>
                                <ChevronDown className="h-4 w-4 text-gray-400" />
                            </button>

                            {showCategoryDropdown && (
                                <div className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md py-1 border border-gray-200 max-h-60 overflow-auto">
                                    {categories.map((category) => (
                                        <button
                                            key={category.id}
                                            type="button"
                                            onClick={() => selectCategory(category.id)}
                                            className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center"
                                        >
                                            <span
                                                className="w-3 h-3 rounded-full mr-3"
                                                style={{ backgroundColor: category.color }}
                                            />
                                            <span>{category.name}</span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <input
                            type="hidden"
                            {...register('category')}
                        />
                    </div>

                    {/* Priority Selector */}
                    <div>
                        <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
                            Priority
                        </label>
                        <select
                            id="priority"
                            {...register('priority')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                            <option value="urgent">Urgent</option>
                        </select>
                    </div>
                </div>

                {/* Deadline and Duration Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label htmlFor="deadline" className="block text-sm font-medium text-gray-700 mb-2">
                            <Calendar className="inline w-4 h-4 mr-1" />
                            Deadline
                        </label>
                        <Input
                            id="deadline"
                            type="date"
                            {...register('deadline')}
                        />
                    </div>

                    <div>
                        <label htmlFor="estimated_duration" className="block text-sm font-medium text-gray-700 mb-2">
                            <Clock className="inline w-4 h-4 mr-1" />
                            Duration (minutes)
                        </label>
                        <Input
                            id="estimated_duration"
                            type="number"
                            min="1"
                            {...register('estimated_duration')}
                            placeholder="e.g., 60"
                        />
                    </div>
                </div>

                {/* Status (only show when editing) */}
                {initialData && (
                    <div>
                        <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
                            Status
                        </label>
                        <select
                            id="status"
                            {...register('status')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                            <option value="pending">Pending</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                        </select>
                    </div>
                )}

                {/* Tags Section */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        <Tag className="inline w-4 h-4 mr-1" />
                        Tags
                    </label>

                    {/* Current Tags */}
                    {watchedValues.tags && Array.isArray(watchedValues.tags) && watchedValues.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-3">
                            {watchedValues.tags.map((tag, index) => (
                                <span
                                    key={index}
                                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                                >
                                    {getTagName(tag)}
                                    <button
                                        type="button"
                                        onClick={() => removeTag(tag)}
                                        className="ml-2 text-blue-600 hover:text-blue-800"
                                    >
                                        ×
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Popular Tags */}
                    {Array.isArray(popularTags) && popularTags.length > 0 && (
                        <div className="mb-3">
                            <p className="text-xs text-gray-500 mb-2">Popular tags:</p>
                            <div className="flex flex-wrap gap-1">
                                {popularTags.slice(0, 8).map((tag) => (
                                    <button
                                        key={tag.id}
                                        type="button"
                                        onClick={() => handleTagClick(tag.name)}
                                        className="px-2 py-1 text-xs border border-gray-300 rounded-md hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        {tag.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Tag Input */}
                    <Input
                        placeholder="Add tags (comma-separated)..."
                        onChange={(e) => {
                            const tags = e.target.value.split(',').map(t => t.trim()).filter(Boolean);
                            setValue('tags', tags);
                        }}
                    />
                </div>

                {/* Form Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                    <Button
                        type="button"
                        variant="outline"
                        onClick={onClose}
                        disabled={isSubmitting}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        loading={isSubmitting}
                    >
                        {initialData ? 'Update Task' : 'Create Task'}
                    </Button>
                </div>
            </form>
        </Modal>
    );
};

export default TaskForm;