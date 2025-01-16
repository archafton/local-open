import React, { useState, useEffect } from 'react';
import BillsTable from '../components/BillsTable';
import BillsFilters from '../components/BillsFilters';

const Bills = () => {
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    bill_number: '',
    bill_title: '',
    status: '',
    sponsor: '',
    subject: '',
    congress: '',
  });

  useEffect(() => {
    const fetchBills = async () => {
      setLoading(true);
      try {
        const response = await fetch('http://localhost:5001/api/bills');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setBills(data);
      } catch (error) {
        console.error("Could not fetch bills:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchBills();
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-800 dark:text-white">Bills</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <BillsFilters filters={filters} setFilters={setFilters} />
      </div>
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 dark:border-white"></div>
        </div>
      ) : (
        <BillsTable data={bills} filters={filters} />
      )}
    </div>
  );
};

export default Bills;
