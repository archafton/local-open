import React from 'react';
import LegislativeActivity from '../components/analytics/LegislativeActivity';

const Analytics = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Explore legislative data through interactive visualizations and insights
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Legislative Activity Section */}
        <section>
          <LegislativeActivity />
        </section>

        {/* Placeholder for future analytics categories */}
        <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 opacity-50">
          <h2 className="text-2xl font-semibold mb-4">Policy Focus Analysis</h2>
          <p className="text-gray-600 dark:text-gray-400">
            Coming soon: Analyze policy trends and topic distributions
          </p>
        </section>

        <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 opacity-50">
          <h2 className="text-2xl font-semibold mb-4">Representative Analysis</h2>
          <p className="text-gray-600 dark:text-gray-400">
            Coming soon: Track representative activity and collaboration patterns
          </p>
        </section>
      </div>
    </div>
  );
};

export default Analytics;
