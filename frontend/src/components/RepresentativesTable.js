import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const RepresentativesTable = ({ data, filters }) => {
  const [filteredData, setFilteredData] = useState(data);
  const navigate = useNavigate();

  useEffect(() => {
    const filtered = data.filter(rep => {
      return (
        (!filters.chamber || rep.chamber === filters.chamber) &&
        (!filters.party || rep.party === filters.party) &&
        (!filters.leadership_role || rep.leadership_role === filters.leadership_role) &&
        (!filters.state || rep.state === filters.state) &&
        (!filters.district || rep.district === filters.district) &&
        (!filters.full_name || rep.full_name.toLowerCase().includes(filters.full_name.toLowerCase()))
      );
    });
    setFilteredData(filtered);
  }, [data, filters]);

  const handleRepClick = (bioguideId) => {
    navigate(`/representatives/${bioguideId}`);
  };

  return (
    <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow">
      <table className="min-w-full table-auto">
        <thead>
          <tr className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-200 text-xs uppercase">
            <th className="py-3 px-4 text-left">Full Name</th>
            <th className="py-3 px-4 text-left">Chamber</th>
            <th className="py-3 px-4 text-left">Party</th>
            <th className="py-3 px-4 text-left">Leadership Role</th>
            <th className="py-3 px-4 text-left">State</th>
            <th className="py-3 px-4 text-left">District</th>
            <th className="py-3 px-4 text-left">Total Votes</th>
            <th className="py-3 px-4 text-left">Missed Votes</th>
            <th className="py-3 px-4 text-left">Total Present</th>
          </tr>
        </thead>
        <tbody className="text-gray-600 dark:text-gray-200 text-sm">
          {filteredData.map((rep, index) => (
            <tr key={index} className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600">
              <td className="py-3 px-4">
                <button
                  onClick={() => handleRepClick(rep.bioguide_id)}
                  className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  {rep.full_name}
                </button>
              </td>
              <td className="py-3 px-4">{rep.chamber}</td>
              <td className="py-3 px-4">{rep.party}</td>
              <td className="py-3 px-4">{rep.leadership_role || 'N/A'}</td>
              <td className="py-3 px-4">{rep.state}</td>
              <td className="py-3 px-4">{rep.district || 'N/A'}</td>
              <td className="py-3 px-4">{rep.total_votes}</td>
              <td className="py-3 px-4">{rep.missed_votes}</td>
              <td className="py-3 px-4">{rep.total_present}</td>
            </tr>
          ))}
          {filteredData.length === 0 && (
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
