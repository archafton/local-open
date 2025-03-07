import React from 'react';
import { useNavigate } from 'react-router-dom';

const RepresentativesTable = ({ data, sortConfig, onSort }) => {
  const navigate = useNavigate();

  const requestSort = (key) => {
    const direction = 
      sortConfig.key === key && sortConfig.direction === 'asc' 
        ? 'desc' 
        : 'asc';
    onSort(key, direction);
  };

  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <span className="text-gray-400">↕</span>;
    }
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  const handleRepClick = (bioguideId) => {
    navigate(`/representatives/${bioguideId}`);
  };

  return (
    <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow">
      <table className="w-full table-auto">
        <thead>
          <tr className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-200 text-xs uppercase">
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('full_name')}
            >
              Full Name {getSortIcon('full_name')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('chamber')}
            >
              Chamber {getSortIcon('chamber')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('party')}
            >
              Party {getSortIcon('party')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('leadership_role')}
            >
              Leadership Role {getSortIcon('leadership_role')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('state')}
            >
              State {getSortIcon('state')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('district')}
            >
              District {getSortIcon('district')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('total_votes')}
            >
              Total Votes {getSortIcon('total_votes')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('missed_votes')}
            >
              Missed Votes {getSortIcon('missed_votes')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('total_present')}
            >
              Total Present {getSortIcon('total_present')}
            </th>
          </tr>
        </thead>
        <tbody className="text-gray-600 dark:text-gray-200 text-sm">
          {data.map((rep, index) => (
            <tr 
              key={rep.bioguide_id || index} 
              className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              <td className="py-3 px-4 w-[15%]">
                <button
                  onClick={() => handleRepClick(rep.bioguide_id)}
                  className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  {rep.full_name}
                </button>
              </td>
              <td className="py-3 px-4 w-[10%] capitalize">{rep.chamber}</td>
              <td className="py-3 px-4 w-[10%]">{rep.party}</td>
              <td className="py-3 px-4 w-[15%]">{rep.leadership_role || 'N/A'}</td>
              <td className="py-3 px-4 w-[10%]">{rep.state}</td>
              <td className="py-3 px-4 w-[10%]">{rep.district || 'N/A'}</td>
              <td className="py-3 px-4 w-[10%]">{rep.total_votes}</td>
              <td className="py-3 px-4 w-[10%]">{rep.missed_votes}</td>
              <td className="py-3 px-4 w-[10%]">{rep.total_present}</td>
            </tr>
          ))}
          {data.length === 0 && (
            <tr>
              <td colSpan="9" className="py-4 text-center text-gray-500 dark:text-gray-400">
                No representatives found matching the current filters
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default RepresentativesTable;
