import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import TagFilter from './TagFilter';
import 'react-datepicker/dist/react-datepicker.css';

const STATUS_OPTIONS = [
  { value: 'Introduced', label: 'Introduced' },
  { value: 'In Committee', label: 'In Committee' },
  { value: 'Reported', label: 'Reported' },
  { value: 'Passed House', label: 'Passed House' },
  { value: 'Passed Senate', label: 'Passed Senate' },
  { value: 'Enacted', label: 'Enacted' },
  { value: 'Became Law', label: 'Became Law' }
];

const BillsFilters = ({ filters, setFilters }) => {
  const [congresses, setCongresses] = useState([]);

  useEffect(() => {
    const fetchCongresses = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/bills/congresses');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setCongresses(data);
      } catch (error) {
        console.error("Could not fetch congresses:", error);
      }
    };

    fetchCongresses();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters(prevFilters => ({ ...prevFilters, [name]: value }));
  };

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
      <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Congress</label>
          <select
            name="congress"
            value={filters.congress}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="">All Congresses</option>
            {congresses.map(congress => (
              <option key={congress} value={congress}>
                {congress}th Congress
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Status</label>
          <select
            name="status"
            value={filters.status}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="">All Statuses</option>
            {STATUS_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Bill Number</label>
          <input
            type="text"
            name="bill_number"
            placeholder="e.g., HR8823"
            value={filters.bill_number}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Title</label>
          <input
            type="text"
            name="bill_title"
            placeholder="Search by title"
            value={filters.bill_title}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Sponsor</label>
          <input
            type="text"
            name="sponsor"
            placeholder="Search by name or ID"
            value={filters.sponsor}
            onChange={handleChange}
            className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div className="flex flex-col">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Date Introduced</label>
          <div className="flex space-x-2">
            <DatePicker
              selected={filters.date_from ? new Date(filters.date_from) : null}
              onChange={(date) => {
                setFilters(prevFilters => ({
                  ...prevFilters,
                  date_from: date ? date.toISOString().split('T')[0] : ''
                }));
              }}
              selectsStart
              startDate={filters.date_from ? new Date(filters.date_from) : null}
              endDate={filters.date_to ? new Date(filters.date_to) : null}
              dateFormat="yyyy-MM-dd"
              isClearable
              placeholderText="From date"
              className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white w-full"
            />
            <DatePicker
              selected={filters.date_to ? new Date(filters.date_to) : null}
              onChange={(date) => {
                setFilters(prevFilters => ({
                  ...prevFilters,
                  date_to: date ? date.toISOString().split('T')[0] : ''
                }));
              }}
              selectsEnd
              startDate={filters.date_from ? new Date(filters.date_from) : null}
              endDate={filters.date_to ? new Date(filters.date_to) : null}
              minDate={filters.date_from ? new Date(filters.date_from) : null}
              dateFormat="yyyy-MM-dd"
              isClearable
              placeholderText="To date"
              className="p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white w-full"
            />
          </div>
        </div>
        <div className="flex flex-col col-span-3">
          <label className="mb-1 text-sm text-gray-600 dark:text-gray-400">Tags</label>
          <TagFilter
            value={{
              operator: filters.tag_operator,
              tags: filters.tags
            }}
            onChange={({ operator, tags }) => {
              const newFilters = {
                ...filters,
                tag_operator: operator,
                tags: tags
              };
              setFilters(newFilters);
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default BillsFilters;
