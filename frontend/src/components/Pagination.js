import React from 'react';

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  // Calculate the range of page numbers to show
  const getPageRange = () => {
    const range = [];
    let start;
    
    if (currentPage <= 3) {
      // At the start, show first 4 pages
      start = 1;
    } else if (currentPage >= totalPages - 2) {
      // Near the end, show last 4 pages
      start = Math.max(totalPages - 3, 1);
    } else {
      // In the middle, show current page and 3 after it
      start = currentPage - 1;
    }

    // Generate array of page numbers
    for (let i = 0; i < 4 && start + i <= totalPages; i++) {
      range.push(start + i);
    }

    return range;
  };

  const pageRange = getPageRange();

  return (
    <div className="flex items-center space-x-2 text-sm">
      {currentPage > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            First
          </button>
          <button
            onClick={() => onPageChange(currentPage - 1)}
            className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Previous
          </button>
        </>
      )}
      
      {pageRange.map(page => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`px-3 py-1 rounded ${
            currentPage === page
              ? 'bg-blue-800 text-white'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {page}
        </button>
      ))}

      {currentPage < totalPages && (
        <>
          <button
            onClick={() => onPageChange(currentPage + 1)}
            className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Next
          </button>
          <button
            onClick={() => onPageChange(totalPages)}
            className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Last
          </button>
        </>
      )}
    </div>
  );
};

export default Pagination;
