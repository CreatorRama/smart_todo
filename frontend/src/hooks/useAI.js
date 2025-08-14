import { useState } from 'react';
import { aiAPI } from '../lib/api';
import toast from 'react-hot-toast';

export const useAI = () => {
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(null);

  const getTaskSuggestions = async (taskData, contextEntries = [], userPreferences = {}, currentTaskLoad = 0) => {
    try {
      setLoading(true);
      const response = await aiAPI.getTaskSuggestions({
        task_data: taskData,
        context_entries: contextEntries,
        user_preferences: userPreferences,
        current_task_load: currentTaskLoad
      });
      setSuggestions(response.data);
      return response.data;
    } catch (err) {
      toast.error('Failed to get AI suggestions');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const prioritizeTasks = async (taskIds, contextEntries = [], userPreferences = {}) => {
    try {
      setLoading(true);
      const response = await aiAPI.prioritizeTasks({
        task_ids: taskIds,
        context_entries: contextEntries,
        user_preferences: userPreferences
      });
      toast.success('Tasks prioritized successfully');
      return response.data;
    } catch (err) {
      toast.error('Failed to prioritize tasks');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    suggestions,
    getTaskSuggestions,
    prioritizeTasks,
  };
};
