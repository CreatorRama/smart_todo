import { useState, useEffect } from 'react';
import { fetchCategories } from '../lib/api';

const useCategories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadCategories = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchCategories();
        setCategories(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadCategories();
  }, []);

  return {
    categories,
    loading,
    error,
    refresh: async () => {
      const data = await fetchCategories();
      setCategories(data);
    },
  };
};

export default useCategories;