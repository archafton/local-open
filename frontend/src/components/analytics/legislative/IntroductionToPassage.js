import React, { useState, useEffect } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import BackToAnalytics from '../BackToAnalytics';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

const IntroductionToPassage = () => {
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
        if (data.length > 0) {
          setSelectedCongress(data[0]); // Set first congress as default
        }
      } catch (err) {
        console.error('Error fetching congresses:', err);
      }
    };

    fetchCongresses();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const url = selectedCongress
          ? `http://localhost:5001/api/analytics/passage-time?congress=${selectedCongress}`
          : 'http://localhost:5001/api/analytics/passage-time';
        
        const response = await fetch(url);
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to fetch data');
        }
        const result = await response.json();
        setData(result);
        setLoading(false);
        setError(null); // Clear any previous errors
      } catch (err) {
        console.error('Error fetching passage time data:', err);
        setError(err.message);
        setLoading(false);
        setData(null); // Clear any previous data
      }
    };

    if (selectedCongress) { // Only fetch if congress is selected
      fetchData();
    }
  }, [selectedCongress]);

  const getStageAnalysisChart = () => {
    if (!data?.stage_analysis) return null;

    const chartData = {
      labels: data.stage_analysis.map(stage => stage.stage_name),
      datasets: [
        {
          label: 'Average Days in Stage',
          data: data.stage_analysis.map(stage => stage.avg_days_in_stage),
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgb(54, 162, 235)',
          borderWidth: 1
        }
      ]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Average Time Spent in Each Stage'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Days'
          }
        }
      }
    };

    return <Bar data={chartData} options={options} />;
  };

  const getOutlierChart = () => {
    if (!data?.outliers) return null;

    const chartData = {
      labels: data.outliers.map(bill => bill.bill_number),
      datasets: [
        {
          label: 'Days to Process',
          data: data.outliers.map(bill => bill.days_to_process),
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.5)',
          pointStyle: 'circle',
          pointRadius: 8,
          pointHoverRadius: 10
        }
      ]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Bills with Longest Processing Times'
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const bill = data.outliers[context.dataIndex];
              return [
                `Days: ${bill.days_to_process}`,
                `Title: ${bill.bill_title.substring(0, 50)}...`,
                `Status: ${bill.status}`
              ];
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Days to Process'
          }
        }
      }
    };

    return <Line data={chartData} options={options} />;
  };

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
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold mb-2">Introduction to Passage Time</h2>
            <p className="text-gray-600 dark:text-gray-400">
              Measure the time taken for bills to move through the legislative process
            </p>
          </div>
          <div>
            <select
              value={selectedCongress}
              onChange={(e) => setSelectedCongress(e.target.value)}
              className="bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2"
            >
              <option value="">All Congresses</option>
              {congresses.map(congress => (
                <option key={congress} value={congress}>
                  {congress}th Congress
                </option>
              ))}
            </select>
          </div>
        </div>
      
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="h-80">
            {getStageAnalysisChart()}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Stage Analysis</h3>
            <div className="space-y-4">
              {data?.stage_analysis && (
                <div className="text-gray-600 dark:text-gray-400">
                  <ul className="space-y-2">
                    {data.stage_analysis.map((stage, index) => (
                      <li key={index} className="flex justify-between">
                        <span>{stage.stage_name}:</span>
                        <span className="font-semibold">{stage.avg_days_in_stage} days</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Key Insights</h3>
            {data?.overall_statistics && (
              <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400">
                <li>Average time to completion: {data.overall_statistics.avg_days} days</li>
                <li>Median time to completion: {data.overall_statistics.median_days} days</li>
                <li>Fastest bill: {data.overall_statistics.min_days} days</li>
                <li>Slowest bill: {data.overall_statistics.max_days} days</li>
                <li>Total bills analyzed: {data.overall_statistics.total_bills}</li>
              </ul>
            )}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Outlier Analysis</h3>
          <div className="space-y-4">
            <div className="h-80">
              {getOutlierChart()}
            </div>
            {data?.outliers && (
              <div className="mt-4">
                <h4 className="font-semibold mb-2">Top 10 Longest Processing Times:</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead>
                      <tr>
                        <th className="px-4 py-2 text-left">Bill</th>
                        <th className="px-4 py-2 text-left">Days</th>
                        <th className="px-4 py-2 text-left">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {data.outliers.map((bill, index) => (
                        <tr key={index}>
                          <td className="px-4 py-2">{bill.bill_number}</td>
                          <td className="px-4 py-2">{bill.days_to_process}</td>
                          <td className="px-4 py-2">{bill.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntroductionToPassage;
