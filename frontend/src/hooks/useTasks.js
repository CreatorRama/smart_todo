import { useState, useEffect } from 'react';
import { tasksAPI } from '../lib/api';
import toast from 'react-hot-toast';

export const useTasks = (initialParams = {}) => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [params, setParams] = useState(initialParams);

  const fetchTasks = async (newParams = params) => {
    try {
      setLoading(true);
      setError(null);
      const response = await tasksAPI.getTasks(newParams);
      setTasks(response.data.results || response.data);
    } catch (err) {
      setError(err.message);
      toast.error('Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  };

  const createTask = async (taskData) => {
    try {
      const response = await tasksAPI.createTask(taskData);
      setTasks(prev => [response.data, ...prev]);
      toast.success('Task created successfully');
      return response.data;
    } catch (err) {
      toast.error('Failed to create task');
      throw err;
    }
  };

  const updateTask = async (id, taskData) => {
    try {
      const response = await tasksAPI.updateTask(id, taskData);
      setTasks(prev => prev.map(task => task.id === id ? response.data : task));
      toast.success('Task updated successfully');
      return response.data;
    } catch (err) {
      toast.error('Failed to update task');
      throw err;
    }
  };

  const deleteTask = async (id) => {
    try {
      await tasksAPI.deleteTask(id);
      setTasks(prev => prev.filter(task => task.id !== id));
      toast.success('Task deleted successfully');
    } catch (err) {
      toast.error('Failed to delete task');
      throw err;
    }
  };

  const updateParams = (newParams) => {
    const updatedParams = { ...params, ...newParams };
    setParams(updatedParams);
    fetchTasks(updatedParams);
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return {
    tasks,
    loading,
    error,
    createTask,
    updateTask,
    deleteTask,
    refetch: fetchTasks,
    updateParams,
    params
  };
};