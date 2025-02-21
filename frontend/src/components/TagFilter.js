import React, { useState, useEffect } from 'react';

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

  // Update state when props change
  useEffect(() => {
    setSelectedOperator(value?.operator || 'is');
    setSelectedTags(value?.tags || []);
  }, [value]);

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

  // Handle direct changes instead of using useEffect
  const handleOperatorChange = (e) => {
    const newOperator = e.target.value;
    setSelectedOperator(newOperator);
    // Clear tags if switching to single-select operator
    const newTags = (newOperator === 'is' || newOperator === 'is_not') && selectedTags.length > 1 
      ? [selectedTags[0]] 
      : selectedTags;
    setSelectedTags(newTags);
    onChange({
      operator: newOperator,
      tags: newTags
    });
  };

  const handleTagSelect = (tag) => {
    let newTags;
    if (selectedOperator === 'is' || selectedOperator === 'is_not') {
      // Single tag selection for 'is' and 'is_not' operators
      newTags = [tag];
    } else {
      // Multi-tag selection for 'is_one_of' and 'is_not_one_of' operators
      if (!selectedTags.find(t => t.id === tag.id)) {
        newTags = [...selectedTags, tag];
      } else {
        return; // Tag already selected
      }
    }
    setSelectedTags(newTags);
    onChange({
      operator: selectedOperator,
      tags: newTags
    });
  };

  const handleTagRemove = (tagId) => {
    const newTags = selectedTags.filter(tag => tag.id !== tagId);
    setSelectedTags(newTags);
    onChange({
      operator: selectedOperator,
      tags: newTags
    });
  };


  if (loading) {
    return <div>Loading tags...</div>;
  }

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex space-x-2">
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

        {/* Tag selector */}
        <select
          value=""
          onChange={(e) => {
            const tag = tags.find(t => t.id === parseInt(e.target.value));
            if (tag) handleTagSelect(tag);
          }}
          className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white flex-grow"
        >
          <option value="">Select a tag...</option>
          {tags.map(tag => (
            <option key={tag.id} value={tag.id}>
              {tag.name} ({tag.type})
            </option>
          ))}
        </select>
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
