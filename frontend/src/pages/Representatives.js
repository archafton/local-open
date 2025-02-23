import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import RepresentativesTable from '../components/RepresentativesTable';
import RepresentativesFilters from '../components/RepresentativesFilters';
import Pagination from '../components/Pagination';

const Representatives = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [representatives, setRepresentatives] = useState([]);
  const [totalRepresentatives, setTotalRepresentatives] = useState(0);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(parseInt(searchParams.get('page')) || 1);
  const [sortConfig, setSortConfig] = useState({
    key: searchParams.get('sort_key') || 'full_name',
    direction: searchParams.get('sort_direction') || 'asc'
  });
  const itemsPerPage = 100;

  // Initialize filters from URL params
  const [filters, setFilters] = useState({
    full_name: searchParams.get('full_name') || '',
    chamber: searchParams.get('chamber') || '',
    party: searchParams.get('party') || '',
    leadership_role: searchParams.get('leadership_role') || '',
    state: searchParams.get('state') || '',
    district: searchParams.get('district') || '',
  });

  // Update state when URL params change (e.g., browser back/forward)
  useEffect(() => {
    const page = parseInt(searchParams.get('page')) || 1;
    setCurrentPage(page);
    
    setFilters({
      full_name: searchParams.get('full_name') || '',
      chamber: searchParams.get('chamber') || '',
      party: searchParams.get('party') || '',
      leadership_role: searchParams.get('leadership_role') || '',
      state: searchParams.get('state') || '',
      district: searchParams.get('district') || '',
    });
  }, [searchParams]);

  // Update URL when filters, page, or sort changes
  useEffect(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    if (currentPage > 1) {
      params.set('page', currentPage.toString());
    }
    params.set('sort_key', sortConfig.key);
    params.set('sort_direction', sortConfig.direction);
    setSearchParams(params);
  }, [filters, currentPage, sortConfig, setSearchParams]);

  useEffect(() => {
    const fetchRepresentatives = async () => {
      setLoading(true);
      try {
        // Build query parameters from filters and pagination
        const queryParams = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
          if (value) queryParams.append(key, value);
        });
        queryParams.append('page', currentPage.toString());
        queryParams.append('per_page', itemsPerPage.toString());
        queryParams.append('sort_key', sortConfig.key);
        queryParams.append('sort_direction', sortConfig.direction);

        const response = await fetch(`http://localhost:5001/api/representatives?${queryParams}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setRepresentatives(data.representatives);
        setTotalRepresentatives(data.total);
      } catch (error) {
        console.error("Could not fetch representatives:", error);
      } finally {
        setLoading(false);
      }
    };

    // Debounce the fetch to avoid too many requests while typing
    const timeoutId = setTimeout(() => {
      fetchRepresentatives();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [filters, currentPage, sortConfig]); // Re-fetch when filters, page, or sort changes

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo(0, 0);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-800 dark:text-white">Representatives</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-2">
        <RepresentativesFilters 
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
            {totalRepresentatives} {totalRepresentatives === 1 ? 'result' : 'results'} found
            {totalRepresentatives > 0 && `, displaying results ${((currentPage - 1) * itemsPerPage) + 1} - ${Math.min(currentPage * itemsPerPage, totalRepresentatives)}`}
          </div>
          {totalRepresentatives > itemsPerPage && (
            <Pagination
              currentPage={currentPage}
              totalPages={Math.ceil(totalRepresentatives / itemsPerPage)}
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
            <RepresentativesTable 
              data={representatives}
              filters={filters}
              sortConfig={sortConfig}
              onSort={(key, direction) => {
                setSortConfig({ key, direction });
                setCurrentPage(1); // Reset to first page when sort changes
              }}
            />
            {totalRepresentatives > itemsPerPage && (
              <div className="flex justify-center items-center p-4 border-t border-gray-200 dark:border-gray-700">
                <Pagination
                  currentPage={currentPage}
                  totalPages={Math.ceil(totalRepresentatives / itemsPerPage)}
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

export default Representatives;
