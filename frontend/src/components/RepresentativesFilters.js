import React from 'react';

const RepresentativesFilters = ({ filters, setFilters }) => {
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters(prevFilters => ({ ...prevFilters, [name]: value }));
  };

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Name</label>
          <input
            type="text"
            name="full_name"
            placeholder="Search by name"
            value={filters.full_name}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Chamber</label>
          <select
            name="chamber"
            value={filters.chamber}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="">All Chambers</option>
            <option value="senate">Senate</option>
            <option value="house">House</option>
          </select>
        </div>
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Party</label>
          <select
            name="party"
            value={filters.party}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="">All Parties</option>
            <option value="D">Democratic</option>
            <option value="R">Republican</option>
            <option value="I">Independent</option>
          </select>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Leadership Role</label>
          <input
            type="text"
            name="leadership_role"
            placeholder="Search by role"
            value={filters.leadership_role}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">State</label>
          <input
            type="text"
            name="state"
            placeholder="e.g., CA"
            value={filters.state}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">District</label>
          <input
            type="text"
            name="district"
            placeholder="District number"
            value={filters.district}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
      </div>
    </div>
  );
};

export default RepresentativesFilters;
