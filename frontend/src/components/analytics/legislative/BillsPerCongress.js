import React, { useState, useEffect } from 'react';
import BackToAnalytics from '../BackToAnalytics';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const BillsPerCongress = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  // Status colors with higher contrast and semantic meaning
  const statusColors = {
    'Became Law': 'rgba(75, 192, 192, 0.7)',        // Green - Success
    'To President': 'rgba(255, 206, 86, 0.7)',      // Yellow - Almost there
    'Resolving Differences': 'rgba(153, 102, 255, 0.7)', // Purple - Complex stage
    'Passed Chamber': 'rgba(255, 159, 64, 0.7)',    // Orange - Moving forward
    'In Committee': 'rgba(54, 162, 235, 0.7)',      // Blue - In progress
    'Failed': 'rgba(255, 99, 132, 0.7)',            // Red - Failed
    'Other': 'rgba(201, 203, 207, 0.7)'             // Grey - Other
  };

  // Sort order for status legend - follows bill progression (bottom to top)
  const statusOrder = [
    'Other',
    'Failed',
    'In Committee',
    'Passed Chamber',
    'Resolving Differences',
    'To President',
    'Became Law'
  ];

  const processData = (rawData) => {
    // Group data by congress and status
    const congressMap = new Map();
    const allStatuses = new Set();

    // First pass: collect all statuses and initialize congress data
    rawData.forEach(item => {
      allStatuses.add(item.status);
      if (!congressMap.has(item.congress)) {
        congressMap.set(item.congress, {
          total: 0,
          statuses: new Map()
        });
      }
    });

    // Second pass: populate data
    rawData.forEach(item => {
      const congressData = congressMap.get(item.congress);
      congressData.total += item.bill_count;
      congressData.statuses.set(item.status, item.bill_count);
    });

    // Convert to chart data
    const labels = Array.from(congressMap.keys()).sort((a, b) => a - b);
    const datasets = statusOrder
      .filter(status => allStatuses.has(status))
      .map(status => ({
        label: status,
        data: labels.map(congress => 
          congressMap.get(congress).statuses.get(status) || 0
        ),
        backgroundColor: statusColors[status],
        borderColor: statusColors[status].replace('0.7', '1'),
        borderWidth: 1
      }))
      .reverse(); // Reverse to show progression from bottom to top

    return {
      labels,
      datasets,
      congressMap,
      allStatuses
    };
  };

  const generateInsights = (data) => {
    if (!data || !data.congressMap) return [];

    const insights = [];
    const latestCongress = Math.max(...data.congressMap.keys());
    const latestData = data.congressMap.get(latestCongress);

    // Calculate total bills and status breakdown in latest congress
    const becameLaw = latestData.statuses.get('Became Law') || 0;
    const inCommittee = latestData.statuses.get('In Committee') || 0;
    const passedChamber = latestData.statuses.get('Passed Chamber') || 0;
    const successRate = ((becameLaw / latestData.total) * 100).toFixed(1);
    const inProgressRate = (((inCommittee + passedChamber) / latestData.total) * 100).toFixed(1);

    insights.push(`The ${latestCongress}th Congress has processed ${latestData.total} bills, with ${successRate}% becoming law.`);
    insights.push(`Currently, ${inProgressRate}% of bills are actively moving through the legislative process (${inCommittee} in committee, ${passedChamber} passed at least one chamber).`);

    // Compare with previous congress
    const prevCongress = latestCongress - 1;
    if (data.congressMap.has(prevCongress)) {
      const prevData = data.congressMap.get(prevCongress);
      const prevBecameLaw = prevData.statuses.get('Became Law') || 0;
      const prevSuccessRate = ((prevBecameLaw / prevData.total) * 100).toFixed(1);
      const successChange = (successRate - prevSuccessRate).toFixed(1);
      const direction = successChange > 0 ? 'increase' : 'decrease';
      insights.push(`This represents a ${Math.abs(successChange)}% ${direction} in successful legislation compared to the ${prevCongress}th Congress (${prevSuccessRate}%).`);
    }

    return insights;
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/analytics/bills-per-congress');
        if (!response.ok) {
          throw new Error('Failed to fetch data');
        }
        const rawData = await response.json();
        setData(processData(rawData));
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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
          <h2 className="text-2xl font-bold mb-2">Bills per Congress</h2>
          <p className="text-gray-600 dark:text-gray-400">
            Track and compare the number of bills across congressional sessions
          </p>
        </div>
      </div>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div style={{ height: '400px' }}>
          {data && (
            <Bar
              data={data}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'right',
                  labels: {
                    color: 'rgb(107, 114, 128)',
                    padding: 20,
                    font: {
                      size: 12
                    }
                  }
                },
                title: {
                  display: true,
                  text: 'Bills per Congressional Session',
                  color: 'rgb(107, 114, 128)',
                  font: {
                    size: 16,
                    weight: 'bold'
                  },
                  padding: {
                    top: 10,
                    bottom: 30
                  }
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      const total = context.chart.data.datasets.reduce((sum, dataset) => 
                        sum + (dataset.data[context.dataIndex] || 0), 0
                      );
                      const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                      return `${context.dataset.label}: ${context.parsed.y} (${percentage}%)`;
                    }
                  }
                }
              },
                scales: {
                  y: {
                    stacked: true,
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Number of Bills',
                      color: 'rgb(107, 114, 128)'
                    },
                    ticks: {
                      color: 'rgb(107, 114, 128)'
                    }
                  },
                  x: {
                    stacked: true,
                    title: {
                      display: true,
                      text: 'Congress',
                      color: 'rgb(107, 114, 128)'
                    },
                    ticks: {
                      color: 'rgb(107, 114, 128)'
                    }
                  }
                }
              }}
            />
          )}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mt-6">
        <h3 className="text-xl font-semibold mb-4">Key Insights</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400">
          {data && generateInsights(data).map((insight, index) => (
            <li key={index}>{insight}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default BillsPerCongress;
