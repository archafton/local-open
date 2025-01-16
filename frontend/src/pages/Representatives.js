import React, { useState, useEffect } from 'react';
import RepresentativesTable from '../components/RepresentativesTable';
import RepresentativesFilters from '../components/RepresentativesFilters';

const Representatives = () => {
  const [representatives, setRepresentatives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    full_name: '',
    chamber: '',
    party: '',
    leadership_role: '',
    state: '',
    district: '',
  });

  useEffect(() => {
    const fetchRepresentatives = async () => {
      setLoading(true);
      try {
        const response = await fetch('http://localhost:5001/api/representatives');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setRepresentatives(data);
      } catch (error) {
        console.error("Could not fetch representatives:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchRepresentatives();
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-800 dark:text-white">Representatives</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <RepresentativesFilters filters={filters} setFilters={setFilters} />
      </div>
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 dark:border-white"></div>
        </div>
      ) : (
        <RepresentativesTable data={representatives} filters={filters} />
      )}
    </div>
  );
};

export default Representatives;
