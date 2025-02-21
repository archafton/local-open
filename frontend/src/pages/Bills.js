import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import BillsTable from '../components/BillsTable';
import BillsFilters from '../components/BillsFilters';
import Pagination from '../components/Pagination';

const Bills = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [bills, setBills] = useState([]);
  const [totalBills, setTotalBills] = useState(0);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(parseInt(searchParams.get('page')) || 1);
  const itemsPerPage = 100;

  // Initialize filters from URL params
  const [filters, setFilters] = useState(() => {
    // Parse tags from URL
    let tags = [];
    const tagsParam = searchParams.get('tags');
    if (tagsParam) {
      try {
        tags = JSON.parse(tagsParam);
      } catch (e) {
        console.error("Failed to parse tags from URL:", e);
      }
    }

    return {
      bill_number: searchParams.get('bill_number') || '',
      bill_title: searchParams.get('bill_title') || '',
      status: searchParams.get('status') || '',
      sponsor: searchParams.get('sponsor') || '',
      congress: searchParams.get('congress') || '',
      date_from: searchParams.get('date_from') || '',
      date_to: searchParams.get('date_to') || '',
      tag_operator: searchParams.get('tag_operator') || 'is',
      tags: tags,
    };
  });

  // Update URL when filters or page changes
  useEffect(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        if (key === 'tags' && Array.isArray(value) && value.length > 0) {
          params.set(key, JSON.stringify(value));
        } else if (key !== 'tags' && value) {
          params.set(key, value);
        }
      }
    });
    if (currentPage > 1) {
      params.set('page', currentPage.toString());
    }
    setSearchParams(params);
  }, [filters, currentPage, setSearchParams]);

  useEffect(() => {
    const fetchBills = async () => {
      setLoading(true);
      try {
        // Build query parameters from filters and pagination
        const queryParams = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
          if (value) {
            if (key === 'tags') {
              if (Array.isArray(value) && value.length > 0) {
                queryParams.append(key, JSON.stringify(value));
              }
            } else {
              queryParams.append(key, value);
            }
          }
        });
        queryParams.append('page', currentPage.toString());
        queryParams.append('per_page', itemsPerPage.toString());

        const response = await fetch(`http://localhost:5001/api/bills?${queryParams}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setBills(data.bills);
        setTotalBills(data.total);
      } catch (error) {
        console.error("Could not fetch bills:", error);
      } finally {
        setLoading(false);
      }
    };

    // Debounce the fetch to avoid too many requests while typing
    const timeoutId = setTimeout(() => {
      fetchBills();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [filters, currentPage]); // Re-fetch when filters or page changes

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo(0, 0);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-800 dark:text-white">Bills</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-2">
        <BillsFilters 
          filters={filters} 
          setFilters={(newFilters) => {
            setFilters(newFilters);
            setCurrentPage(1); // Reset to first page when filters change
          }} 
        />
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {totalBills} {totalBills === 1 ? 'result' : 'results'} found
            {totalBills > 0 && `, displaying results ${((currentPage - 1) * itemsPerPage) + 1} - ${Math.min(currentPage * itemsPerPage, totalBills)}`}
          </div>
          {totalBills > itemsPerPage && (
            <Pagination
              currentPage={currentPage}
              totalPages={Math.ceil(totalBills / itemsPerPage)}
              onPageChange={handlePageChange}
            />
          )}
        </div>
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 dark:border-white"></div>
          </div>
        ) : (
          <>
            <BillsTable 
              data={bills} 
              filters={filters}
            />
            {totalBills > itemsPerPage && (
              <div className="flex justify-center items-center p-4 border-t border-gray-200 dark:border-gray-700">
                <Pagination
                  currentPage={currentPage}
                  totalPages={Math.ceil(totalBills / itemsPerPage)}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Bills;
