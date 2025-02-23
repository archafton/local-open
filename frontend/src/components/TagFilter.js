import React, { useState, useEffect, useRef } from 'react';

const OPERATORS = [
  { value: 'is', label: 'is' },
  { value: 'is_not', label: 'is not' },
  { value: 'is_one_of', label: 'is one of' },
  { value: 'is_not_one_of', label: 'is not one of' }
];

const TagFilter = ({ value, onChange }) => {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  // Initialize state from props
  const [selectedOperator, setSelectedOperator] = useState(value?.operator || 'is');
  const [selectedTags, setSelectedTags] = useState(value?.tags || []); 
  const [isOpen, setIsOpen] = useState(false);
  const [tempSelectedTags, setTempSelectedTags] = useState([]);
  const dropdownRef = useRef(null);

  // Update state when props change
  useEffect(() => {
    setSelectedOperator(value?.operator || 'is');
    setSelectedTags(value?.tags || []);
    setTempSelectedTags(value?.tags || []);
  }, [value]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        handleDone();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, tempSelectedTags]);

  // Fetch available tags from the API
  useEffect(() => {
    const fetchTags = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/tags');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setTags(data.tags);
      } catch (error) {
        console.error("Could not fetch tags:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTags();
  }, []);

  const handleOperatorChange = (e) => {
    const newOperator = e.target.value;
    setSelectedOperator(newOperator);
    
    // Clear tags if switching to single-select operator
    const newTags = (newOperator === 'is' || newOperator === 'is_not') && selectedTags.length > 1 
      ? [selectedTags[0]] 
      : selectedTags;
      
    setSelectedTags(newTags);
    setTempSelectedTags(newTags);
    onChange({
      operator: newOperator,
      tags: newTags
    });
  };

  const handleTagToggle = (tag) => {
    let newTempTags;
    if (selectedOperator === 'is' || selectedOperator === 'is_not') {
      // Single tag selection
      newTempTags = [tag];
    } else {
      // Multi-tag selection
      const exists = tempSelectedTags.find(t => t.id === tag.id);
      if (exists) {
        newTempTags = tempSelectedTags.filter(t => t.id !== tag.id);
      } else {
        newTempTags = [...tempSelectedTags, tag];
      }
    }
    setTempSelectedTags(newTempTags);
  };

  const handleDone = () => {
    setIsOpen(false);
    setSelectedTags(tempSelectedTags);
    onChange({
      operator: selectedOperator,
      tags: tempSelectedTags
    });
  };

  const handleTagRemove = (tagId) => {
    const newTags = selectedTags.filter(tag => tag.id !== tagId);
    setSelectedTags(newTags);
    setTempSelectedTags(newTags);
    onChange({
      operator: selectedOperator,
      tags: newTags
    });
  };

  const isTagSelected = (tagId) => {
    return tempSelectedTags.some(tag => tag.id === tagId);
  };


  if (loading) {
    return <div>Loading tags...</div>;
  }

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex space-x-2" ref={dropdownRef}>
        {/* Operator selector */}
        <select
          value={selectedOperator}
          onChange={handleOperatorChange}
          className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          {OPERATORS.map(op => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>

        {/* Custom tag dropdown */}
        <div className="relative flex-grow">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white text-left"
          >
            Select tags...
          </button>

          {isOpen && (
            <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border rounded shadow-lg max-h-60 overflow-y-auto">
              <div className="p-2 space-y-2">
                {tags.map(tag => (
                  <div key={tag.id} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`tag-${tag.id}`}
                      checked={isTagSelected(tag.id)}
                      onChange={() => handleTagToggle(tag)}
                      className="rounded dark:bg-gray-700"
                    />
                    <label htmlFor={`tag-${tag.id}`} className="dark:text-white">
                      {tag.name} ({tag.type})
                    </label>
                  </div>
                ))}
                <div className="pt-2 border-t">
                  <button
                    onClick={handleDone}
                    className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Done
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Selected tags */}
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedTags.map(tag => (
            <div
              key={tag.id}
              className="flex items-center gap-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded"
            >
              <span>{tag.name} ({tag.type})</span>
              <button
                onClick={() => handleTagRemove(tag.id)}
                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TagFilter;
