import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const STATUS_MAP = {
  'Introduced': ['Introduced', 'Introduction'],
  'In Committee': ['Committee', 'Referred to'],
  'Reported': ['Reported'],
  'Passed House': ['Passed House', 'House passage'],
  'Passed Senate': ['Passed Senate', 'Senate passage'],
  'Enacted': ['Enacted', 'Became Public Law'],
  'Became Law': ['Became Law', 'Became Public Law']
};

const BillsTable = ({ data, filters }) => {
  const [filteredData, setFilteredData] = useState(data);
  const navigate = useNavigate();

  useEffect(() => {
    const filtered = data.filter(bill => {
      const statusMatch = !filters.status || 
        (bill.status && STATUS_MAP[filters.status]?.some(term => 
          bill.status.toLowerCase().includes(term.toLowerCase())
        ));

      return (
        (!filters.bill_number || bill.bill_number.toLowerCase().includes(filters.bill_number.toLowerCase())) &&
        (!filters.bill_title || bill.bill_title.toLowerCase().includes(filters.bill_title.toLowerCase())) &&
        (!filters.sponsor || 
          (bill.sponsor_id && bill.sponsor_id.toLowerCase().includes(filters.sponsor.toLowerCase())) ||
          (bill.sponsor_name && bill.sponsor_name.toLowerCase().includes(filters.sponsor.toLowerCase()))
        ) &&
        (!filters.subject || (bill.tags && bill.tags.some(tag => tag.toLowerCase().includes(filters.subject.toLowerCase())))) &&
        (!filters.congress || bill.congress === parseInt(filters.congress)) &&
        statusMatch
      );
    });
    setFilteredData(filtered);
  }, [data, filters]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const formatTags = (tags) => {
    if (!tags || tags.length === 0) return 'N/A';
    return tags.join(', ');
  };

  const handleBillClick = (billNumber) => {
    navigate(`/bills/${billNumber}`);
  };

  const handleSponsorClick = (sponsorId) => {
    if (sponsorId) {
      navigate(`/representatives/${sponsorId}`);
    }
  };

  const getStatusBadgeColor = (status) => {
    if (!status) return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    
    const statusLower = status.toLowerCase();
    if (statusLower.includes('law') || statusLower.includes('enacted')) 
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    if (statusLower.includes('passed')) 
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    if (statusLower.includes('committee') || statusLower.includes('referred')) 
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    if (statusLower.includes('introduced') || statusLower.includes('introduction')) 
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
  };

  return (
    <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow">
      <table className="min-w-full table-auto">
        <thead>
          <tr className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-200 text-xs uppercase">
            <th className="py-3 px-4 text-left">Bill Number</th>
            <th className="py-3 px-4 text-left">Title</th>
            <th className="py-3 px-4 text-left">Sponsor</th>
            <th className="py-3 px-4 text-left">Introduced</th>
            <th className="py-3 px-4 text-left">Status</th>
            <th className="py-3 px-4 text-left">Tags</th>
            <th className="py-3 px-4 text-left">Congress</th>
          </tr>
        </thead>
        <tbody className="text-gray-600 dark:text-gray-200 text-sm">
          {filteredData.map((bill, index) => (
            <tr 
              key={bill.id || index} 
              className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              <td className="py-3 px-4">
                <button
                  onClick={() => handleBillClick(bill.bill_number)}
                  className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  {bill.bill_number}
                </button>
              </td>
              <td className="py-3 px-4">
                <div className="max-w-md overflow-hidden text-ellipsis">
                  {bill.bill_title}
                </div>
              </td>
              <td className="py-3 px-4">
                <div>
                  {bill.sponsor_id ? (
                    <button
                      onClick={() => handleSponsorClick(bill.sponsor_id)}
                      className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                    >
                      {bill.sponsor_name || 'N/A'}
                    </button>
                  ) : (
                    <span>{bill.sponsor_name || 'N/A'}</span>
                  )}
                  <div className="text-xs text-gray-500 dark:text-gray-400">{bill.sponsor_id}</div>
                </div>
              </td>
              <td className="py-3 px-4">{formatDate(bill.introduced_date)}</td>
              <td className="py-3 px-4">
                <span className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeColor(bill.status)}`}>
                  {bill.status || 'N/A'}
                </span>
              </td>
              <td className="py-3 px-4">
                <div className="max-w-xs overflow-hidden text-ellipsis">
                  {formatTags(bill.tags)}
                </div>
              </td>
              <td className="py-3 px-4">{bill.congress || 'N/A'}</td>
            </tr>
          ))}
          {filteredData.length === 0 && (
            <tr>
              <td colSpan="7" className="py-4 text-center text-gray-500 dark:text-gray-400">
                No bills found matching the current filters
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default BillsTable;
