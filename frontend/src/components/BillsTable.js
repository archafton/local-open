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

const Modal = ({ title, content, onClose }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full shadow-xl">
      <div className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">{title}</div>
      <div className="text-gray-600 dark:text-gray-300 mb-6 whitespace-pre-wrap">{content}</div>
      <button
        onClick={onClose}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
      >
        Close
      </button>
    </div>
  </div>
);

const BillsTable = ({ data, sortConfig, onSort }) => {
  const navigate = useNavigate();
  const [selectedTitle, setSelectedTitle] = useState(null);
  const [selectedStatus, setSelectedStatus] = useState(null);

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
    <>
    <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow">
      <table className="w-full table-auto">
          <thead>
          <tr className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-200 text-xs uppercase">
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('bill_number')}
            >
              Bill Number {getSortIcon('bill_number')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('bill_title')}
            >
              Title {getSortIcon('bill_title')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('sponsor')}
            >
              Sponsor {getSortIcon('sponsor')}
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('introduced_date')}
            >
              Introduced {getSortIcon('introduced_date')}
            </th>
            <th className="py-3 px-4 text-left">Status</th>
            <th className="py-3 px-4 text-left">
              Tags
            </th>
            <th 
              className="py-3 px-4 text-left cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600"
              onClick={() => requestSort('congress')}
            >
              Congress {getSortIcon('congress')}
            </th>
          </tr>
        </thead>
        <tbody className="text-gray-600 dark:text-gray-200 text-sm">
          {data.map((bill, index) => (
            <tr 
              key={bill.id || index} 
              className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              <td className="py-3 px-4 w-[12%]">
                <button
                  onClick={() => handleBillClick(bill.bill_number)}
                  className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  {bill.bill_number}
                </button>
              </td>
              <td className="py-3 px-4 w-[30%]">
                <div className="min-h-[4.5rem] flex flex-col justify-between">
                  <div 
                    className="text-sm leading-5 line-clamp-3 mb-1"
                    title={bill.bill_title}
                  >
                    {bill.bill_title}
                  </div>
                  {bill.bill_title && bill.bill_title.length > 100 && (
                    <button
                      onClick={() => setSelectedTitle(bill.bill_title)}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-auto flex items-center gap-1"
                    >
                      <span>View full title</span>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                  )}
                </div>
              </td>
              <td className="py-3 px-4 w-[13%]">
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
              <td className="py-3 px-4 w-[12%]">{formatDate(bill.introduced_date)}</td>
              <td className="py-3 px-4 w-[13%]">
                <div className="min-h-[4.5rem] flex flex-col justify-between">
                  <div 
                    className={`text-sm leading-5 line-clamp-3 mb-1 px-2 py-1 text-xs font-semibold rounded-lg ${getStatusBadgeColor(bill.status)}`}
                    title={bill.status}
                  >
                    {bill.status || 'N/A'}
                  </div>
                  {bill.status && bill.status.length > 50 && (
                    <button
                      onClick={() => setSelectedStatus(bill.status)}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-auto flex items-center gap-1"
                    >
                      <span>View full status</span>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                  )}
                </div>
              </td>
              <td className="py-3 px-4 w-[10%]">
                <div className="max-w-xs overflow-hidden text-ellipsis">
                  {formatTags(bill.tags)}
                </div>
              </td>
              <td className="py-3 px-4 w-[10%]">{bill.congress || 'N/A'}</td>
            </tr>
          ))}
          {data.length === 0 && (
            <tr>
              <td colSpan="7" className="py-4 text-center text-gray-500 dark:text-gray-400">
                No bills found matching the current filters
              </td>
            </tr>
          )}
          </tbody>
        </table>
      </div>
      {selectedTitle && (
        <Modal
          title="Bill Title"
          content={selectedTitle}
          onClose={() => setSelectedTitle(null)}
        />
      )}
      {selectedStatus && (
        <Modal
          title="Bill Status"
          content={selectedStatus}
          onClose={() => setSelectedStatus(null)}
        />
      )}
    </>
  );
};

export default BillsTable;
