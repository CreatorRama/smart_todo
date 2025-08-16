import { useState, useEffect } from 'react';
import {
    MessageSquare,
    Mail,
    FileText,
    Brain,
    Trash2
} from 'lucide-react';
import { contextAPI } from '../lib/api';
import { formatDateTime, truncateText } from '../lib/helpers';
import Button from './ui/Button';
import toast from 'react-hot-toast';

const ContextEntry = ({ entry, onDelete }) => {
    const getSourceIcon = (sourceType) => {
        const icons = {
            whatsapp: MessageSquare,
            email: Mail,
            notes: FileText
        };
        return icons[sourceType] || FileText;
    };

    const getSourceColor = (sourceType) => {
        const colors = {
            whatsapp: 'text-green-600 bg-green-100',
            email: 'text-blue-600 bg-blue-100',
            notes: 'text-purple-600 bg-purple-100'
        };
        return colors[sourceType] || 'text-gray-600 bg-gray-100';
    };

    const IconComponent = getSourceIcon(entry.source_type);

    return (
        <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow duration-200">
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSourceColor(entry.source_type)}`}>
                        <IconComponent className="w-3 h-3 mr-1" />
                        {entry.source_type.charAt(0).toUpperCase() + entry.source_type.slice(1)}
                    </span>
                    <span className="text-sm text-gray-500">
                        {formatDateTime(entry.timestamp)}
                    </span>
                </div>

                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(entry.id)}
                    className="p-1 text-red-500 hover:text-red-700"
                >
                    <Trash2 className="w-4 h-4" />
                </Button>
            </div>

            <div className="space-y-3">
                <p className="text-sm text-gray-800">
                    {truncateText(entry.content, 200)}
                </p>

                {entry.processed_insights && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                        <div className="flex items-center mb-2">
                            <Brain className="w-4 h-4 text-blue-600 mr-2" />
                            <span className="text-sm font-medium text-blue-900">AI Insights</span>
                        </div>

                        {entry.processed_insights.context_summary && (
                            <p className="text-sm text-blue-700 mb-2">
                                <strong>Summary:</strong> {entry.processed_insights.context_summary}
                            </p>
                        )}

                        {entry.processed_insights.extracted_tasks && entry.processed_insights.extracted_tasks.length > 0 && (
                            <div className="text-sm text-blue-700">
                                <strong>Extracted Tasks:</strong>
                                <ul className="list-disc list-inside mt-1 ml-2">
                                    {entry.processed_insights.extracted_tasks.slice(0, 3).map((task, index) => (
                                        <li key={index}>{truncateText(task, 60)}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {entry.processed_insights.urgency_indicators && entry.processed_insights.urgency_indicators.length > 0 && (
                            <div className="text-sm text-blue-700 mt-2">
                                <strong>Urgency Indicators:</strong> {entry.processed_insights.urgency_indicators.slice(0, 3).join(', ')}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const ContextHistory = ({ className = '', onContextSelect }) => {
    const [contextEntries, setContextEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);

    const loadContextEntries = async (pageNum = 1, reset = false) => {
        try {
            setLoading(true);
            const response = await contextAPI.getContextEntries({
                page: pageNum,
                page_size: 10
            });

            const newEntries = response.data.results || response.data;

            if (reset) {
                setContextEntries(newEntries);
            } else {
                setContextEntries(prev => [...prev, ...newEntries]);
            }

            setHasMore(newEntries.length === 10);
            setPage(pageNum);
        } catch (error) {
            console.error('Failed to load context entries:', error);
            toast.error('Failed to load context history');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (entryId) => {
        try {
            await contextAPI.deleteContextEntry({entryId});
            setContextEntries(prev => prev.filter(entry => entry.id !== entryId));
            toast.success('Context entry deleted');
        } catch (error) {
            console.error('Failed to delete context entry:', error);
            toast.error('Failed to delete context entry');
        }
    };

    const loadMore = () => {
        if (!loading && hasMore) {
            loadContextEntries(page + 1, false);
        }
    };

    useEffect(() => {
        loadContextEntries(1, true);
    }, []);

    return (
        <div className={`space-y-4 ${className}`}>
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Context History</h3>
                <span className="text-sm text-gray-500">
                    {contextEntries.length} entries
                </span>
            </div>

            {loading && contextEntries.length === 0 ? (
                <div className="space-y-4">
                    {[...Array(3)].map((_, i) => (
                        <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 animate-pulse">
                            <div className="flex items-center space-x-2 mb-3">
                                <div className="w-16 h-6 bg-gray-200 rounded-full"></div>
                                <div className="w-24 h-4 bg-gray-200 rounded"></div>
                            </div>
                            <div className="space-y-2">
                                <div className="h-4 bg-gray-200 rounded w-full"></div>
                                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : contextEntries.length === 0 ? (
                <div className="text-center py-8">
                    <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 mb-2">No Context Entries</h4>
                    <p className="text-gray-600">
                        Add your daily context to get AI-powered task suggestions.
                    </p>
                </div>
            ) : (
                <>
                    <div className="space-y-4">
                        {contextEntries.map(entry => (
                            <ContextEntry
                                key={entry.id}
                                entry={entry}
                                onDelete={handleDelete}
                            />
                        ))}
                    </div>

                    {hasMore && (
                        <div className="flex justify-center pt-4">
                            <Button
                                variant="outline"
                                onClick={loadMore}
                                loading={loading}
                            >
                                Load More
                            </Button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default ContextHistory;