import React, { useState, useEffect } from 'react';
import BackToAnalytics from '../BackToAnalytics';

const SponsorActivity = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // TODO: Implement API call using Representative Activity Score query from Implementation Guide:
        // SELECT 
        //   m.full_name,
        //   COUNT(DISTINCT b.id) as sponsored_bills,
        //   COUNT(DISTINCT bc.bill_number) as cosponsored_bills,
        //   m.total_votes - m.missed_votes as votes_participated
        // FROM members m
        // LEFT JOIN bills b ON m.bioguide_id = b.sponsor_id
        // LEFT JOIN bill_cosponsors bc ON m.bioguide_id = bc.cosponsor_id
        // WHERE m.current_member = true
        // GROUP BY m.id, m.full_name
        // ORDER BY sponsored_bills DESC;
        
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
        <h2 className="text-2xl font-bold mb-2">Sponsor Activity Levels</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Compare and track the legislative activity of bill sponsors
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        {/* TODO: Implement bar chart for top active sponsors */}
        <div className="text-center text-gray-600 dark:text-gray-400">
          Chart will be implemented here showing sponsor activity levels
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Activity Metrics</h3>
          <div className="space-y-4">
            {/* TODO: Implement activity metrics breakdown */}
            <div className="text-gray-600 dark:text-gray-400">
              <ul className="space-y-2">
                <li>Total Bills Sponsored: Placeholder</li>
                <li>Average Bills per Sponsor: Placeholder</li>
                <li>Most Active Committee: Placeholder</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Key Insights</h3>
          <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400">
            <li>Placeholder for top sponsor analysis</li>
            <li>Placeholder for party distribution</li>
            <li>Placeholder for committee leadership impact</li>
          </ul>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Top Sponsors Leaderboard</h3>
        <div className="space-y-4">
          {/* TODO: Implement leaderboard table */}
          <div className="text-gray-600 dark:text-gray-400">
            <p>Detailed sponsor rankings and metrics will be shown here</p>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
};

export default SponsorActivity;
