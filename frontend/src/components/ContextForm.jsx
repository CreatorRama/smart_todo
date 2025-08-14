import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { 
  MessageSquare, 
  Mail, 
  FileText, 
  Upload,
  Plus 
} from 'lucide-react';
import { contextAPI } from '../lib/api';
import Modal from './ui/Modal';
import Button from './ui/Button';
import Input from './ui/Input';
import toast from 'react-hot-toast';

const ContextForm = ({ 
  isOpen, 
  onClose, 
  onSubmit 
}) => {
  const [contextEntries, setContextEntries] = useState([
    { source_type: 'whatsapp', content: '' }
  ]);

  const {
    handleSubmit,
    formState: { isSubmitting },
    reset
  } = useForm();

  const sourceTypeOptions = [
    { value: 'whatsapp', label: 'WhatsApp', icon: MessageSquare },
    { value: 'email', label: 'Email', icon: Mail },
    { value: 'notes', label: 'Notes', icon: FileText },
  ];

  const addContextEntry = () => {
    setContextEntries([...contextEntries, { source_type: 'whatsapp', content: '' }]);
  };

  const removeContextEntry = (index) => {
    if (contextEntries.length > 1) {
      setContextEntries(contextEntries.filter((_, i) => i !== index));
    }
  };

  const updateContextEntry = (index, field, value) => {
    const updated = [...contextEntries];
    updated[index] = { ...updated[index], [field]: value };
    setContextEntries(updated);
  };

  const onFormSubmit = async () => {
    try {
      // Filter out empty entries
      const validEntries = contextEntries.filter(entry => entry.content.trim());
      
      if (validEntries.length === 0) {
        toast.error('Please add at least one context entry');
        return;
      }

      // Submit to API
      const response = await contextAPI.bulkCreateContextEntries(validEntries);
      
      toast.success(`${validEntries.length} context entries added successfully`);
      
      // Call onSubmit callback
      if (onSubmit) {
        onSubmit(response.data.entries);
      }
      
      // Reset form
      setContextEntries([{ source_type: 'whatsapp', content: '' }]);
      onClose();
    } catch (error) {
      console.error('Failed to submit context:', error);
      toast.error('Failed to add context entries');
    }
  };

  const getSourceIcon = (sourceType) => {
    const option = sourceTypeOptions.find(opt => opt.value === sourceType);
    return option ? option.icon : FileText;
  };

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Daily Context"
      size="lg"
    >
      <div className="space-y-6">
        <p className="text-sm text-gray-600">
          Add your daily context (messages, emails, notes) to help AI provide better task suggestions.
        </p>

        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
          {contextEntries.map((entry, index) => {
            const IconComponent = getSourceIcon(entry.source_type);
            
            return (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <IconComponent className="w-5 h-5 text-gray-500" />
                    <select
                      value={entry.source_type}
                      onChange={(e) => updateContextEntry(index, 'source_type', e.target.value)}
                      className="border-none bg-transparent font-medium text-gray-900 focus:outline-none"
                    >
                      {sourceTypeOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {contextEntries.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeContextEntry(index)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      Remove
                    </button>
                  )}
                </div>
                
                <textarea
                  value={entry.content}
                  onChange={(e) => updateContextEntry(index, 'content', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  rows={4}
                  placeholder={`Paste your ${entry.source_type} content here...`}
                />
              </div>
            );
          })}

          {/* Add Another Entry Button */}
          <Button
            type="button"
            variant="outline"
            onClick={addContextEntry}
            className="w-full"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Another Entry
          </Button>

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
              Add Context
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default ContextForm;
