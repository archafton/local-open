import React, { useState, useEffect } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import BackToAnalytics from '../BackToAnalytics';

ChartJS.register(ArcElement, Tooltip, Legend);

const statusColors = {
  'In Committee': '#4299E1', // blue-500
  'Passed Chamber': '#48BB78', // green-500
  'Resolving Differences': '#ECC94B', // yellow-500
  'To President': '#ED8936', // orange-500
  'Became Law': '#38A169', // green-600
  'Failed': '#E53E3E', // red-600
  'Other': '#718096', // gray-600
};

const BillsByStatus = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const [selectedCongress, setSelectedCongress] = useState('');
  const [congresses, setCongresses] = useState([]);

  useEffect(() => {
    const fetchCongresses = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/bills/congresses');
        const data = await response.json();
        setCongresses(data);
      } catch (err) {
        console.error('Error fetching congresses:', err);
      }
    };

    fetchCongresses();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const url = new URL('http://localhost:5001/api/analytics/bills-by-status');
        if (selectedCongress) {
          url.searchParams.append('congress', selectedCongress);
        }
        
        const response = await fetch(url);
        const data = await response.json();
        setData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedCongress]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-600 dark:text-red-400">Error: {error}</div>
      </div>
    );
  }

  return (
    <div>
      <BackToAnalytics />
      <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Bills by Status</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Analyze the distribution of bills across different legislative statuses
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="mb-4">
          <label htmlFor="congress" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Select Congress:
          </label>
          <select
            id="congress"
            value={selectedCongress}
            onChange={(e) => setSelectedCongress(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="">All Congresses</option>
            {congresses.map((congress) => (
              <option key={congress} value={congress}>
                {congress}th Congress
              </option>
            ))}
          </select>
        </div>
        
        {data && data.length > 0 && (
          <div className="relative" style={{ height: '400px' }}>
            <Pie
              data={{
                labels: data.map(item => item.status),
                datasets: [{
                  data: data.map(item => item.count),
                  backgroundColor: data.map(item => statusColors[item.status] || statusColors.Other),
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'right',
                    labels: {
                      color: document.documentElement.classList.contains('dark') ? '#E5E7EB' : '#374151',
                    }
                  },
                  tooltip: {
                    callbacks: {
                      label: (context) => {
                        const item = data[context.dataIndex];
                        return `${item.status}: ${item.count} bills (${item.percentage}%)`;
                      }
                    }
                  }
                }
              }}
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Status Breakdown</h3>
          <div className="space-y-4">
            {data && data.map((item) => (
              <div key={item.status} className="flex justify-between items-center">
                <div className="flex items-center">
                  <div 
                    className="w-4 h-4 rounded-full mr-2" 
                    style={{ backgroundColor: statusColors[item.status] || statusColors.Other }}
                  />
                  <span className="text-gray-700 dark:text-gray-300">{item.status}</span>
                </div>
                <div className="text-gray-600 dark:text-gray-400">
                  {item.count} bills ({item.percentage}%)
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Key Insights</h3>
          <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400">
            {data && data.length > 0 && (
              <>
                <li>Most bills are in "{data[0].status}" status ({data[0].percentage}%)</li>
                <li>
                  Success rate: {
                    ((data.find(item => item.status === 'Became Law')?.count || 0) / 
                    data.reduce((sum, item) => sum + item.count, 0) * 100).toFixed(1)
                  }% of bills became law
                </li>
                <li>
                  {data.find(item => item.status === 'In Committee')?.percentage}% of bills are currently in committee,
                  indicating potential bottlenecks in the legislative process
                </li>
              </>
            )}
          </ul>
        </div>
      </div>
      </div>
    </div>
  );
};

export default BillsByStatus;
