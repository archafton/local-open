import React from 'react';
import { useNavigate } from 'react-router-dom';

const LegislativeActivity = () => {
  const navigate = useNavigate();

  const metrics = [
    {
      title: 'Bills per Congress',
      description: 'Track and compare the number of bills across congressional sessions',
      path: '/analytics/legislative/bills-per-congress'
    },
    {
      title: 'Bills by Status',
      description: 'Analyze the distribution of bills across different legislative statuses',
      path: '/analytics/legislative/bills-by-status'
    },
    {
      title: 'Introduction to Passage Time',
      description: 'Measure the time taken for bills to move through the legislative process',
      path: '/analytics/legislative/passage-time'
    },
    {
      title: 'Sponsor Activity Levels',
      description: 'Compare and track the legislative activity of bill sponsors',
      path: '/analytics/legislative/sponsor-activity'
    }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-semibold mb-4">Legislative Activity</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {metrics.map((metric, index) => (
          <div
            key={index}
            onClick={() => navigate(metric.path)}
            className="border dark:border-gray-700 rounded-lg p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <h3 className="text-lg font-medium mb-2">{metric.title}</h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              {metric.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LegislativeActivity;
