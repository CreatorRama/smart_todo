import { createContext, useContext, useState } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [selectedTasks, setSelectedTasks] = useState([]);
  const [aiSuggestions, setAiSuggestions] = useState(null);

  const toggleTaskSelection = (taskId) => {
    setSelectedTasks((prev) =>
      prev.includes(taskId)
        ? prev.filter((id) => id !== taskId)
        : [...prev, taskId]
    );
  };

  const clearSelectedTasks = () => {
    setSelectedTasks([]);
  };

  return (
    <AppContext.Provider
      value={{
        selectedTasks,
        toggleTaskSelection,
        clearSelectedTasks,
        aiSuggestions,
        setAiSuggestions,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => useContext(AppContext);