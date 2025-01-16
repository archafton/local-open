import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Tab } from '@headlessui/react';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

const RepresentativeDetails = () => {
  const { bioguideId } = useParams();
  const [representative, setRepresentative] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [biography, setBiography] = useState('');
  const [bioLoading, setBioLoading] = useState(true);

  useEffect(() => {
    const fetchRepresentative = async () => {
      try {
        const response = await fetch(`http://localhost:5001/api/representatives/${bioguideId}`);
        if (!response.ok) throw new Error('Representative not found');
        const data = await response.json();
        setRepresentative(data);
      } catch (error) {
        console.error('Error fetching representative:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRepresentative();
  }, [bioguideId]);

  const loadBioguideScript = useCallback((bioguideId) => {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      const callbackName = `bioguide_${bioguideId}_callback`;

      // Define the callback function
      window[callbackName] = (data) => {
        delete window[callbackName]; // Clean up
        document.head.removeChild(script); // Remove the script tag
        resolve(data);
      };

      script.src = `https://bioguide.congress.gov/search/bio/${bioguideId}.json?callback=${callbackName}`;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }, []);

  useEffect(() => {
    const fetchBiography = async () => {
      try {
        setBioLoading(true);
        const data = await loadBioguideScript(bioguideId);
        if (data && data.profileText) {
          setBiography(data.profileText);
        } else {
          // Fallback to database profile text if available
          setBiography(representative?.profile_text || 'Biography not available');
        }
      } catch (error) {
        console.error('Error fetching biography:', error);
        // Fallback to database profile text if available
        setBiography(representative?.profile_text || 'Biography not available');
      } finally {
        setBioLoading(false);
      }
    };

    if (bioguideId) {
      fetchBiography();
    }
  }, [bioguideId, loadBioguideScript, representative]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!representative) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900">Representative not found</h2>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Title Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Profile Image */}
          <div className="w-48 h-48 flex-shrink-0">
            {representative.photo_url ? (
              <img
                src={representative.photo_url}
                alt={representative.full_name}
                className="w-full h-full object-cover rounded-lg"
              />
            ) : (
              <div className="w-full h-full bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                <span className="text-gray-500 dark:text-gray-400">No Image</span>
              </div>
            )}
          </div>

          {/* Representative Info */}
          <div className="flex-grow">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              {representative.honorific_name} {representative.direct_order_name || representative.full_name}
            </h1>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-gray-600 dark:text-gray-300">
                  <span className="font-semibold">Chamber:</span> {representative.chamber}
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  <span className="font-semibold">Party:</span> {representative.party}
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  <span className="font-semibold">State:</span> {representative.state}
                  {representative.district && ` - District ${representative.district}`}
                </p>
                {representative.birth_year && (
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-semibold">Birth Year:</span> {representative.birth_year}
                  </p>
                )}
              </div>
              <div>
                {representative.leadership_role && (
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-semibold">Current Leadership:</span> {representative.leadership_role}
                  </p>
                )}
              </div>
            </div>
            
            {/* Committee Tags */}
            <div className="flex flex-wrap gap-2">
              {representative.committees?.map((committee, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded-full text-sm"
                >
                  {committee}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
        <Tab.Group onChange={setActiveTab}>
          <Tab.List className="flex space-x-1 rounded-t-lg bg-gray-100 dark:bg-gray-700 p-1">
            {['Overview', 'Voting Record', 'Sponsored Bills'].map((category, idx) => (
              <Tab
                key={idx}
                className={({ selected }) =>
                  classNames(
                    'w-full py-2.5 text-sm font-medium leading-5',
                    'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                    selected
                      ? 'bg-white dark:bg-gray-800 shadow text-blue-700 dark:text-blue-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-white/[0.12] hover:text-blue-700'
                  )
                }
              >
                {category}
              </Tab>
            ))}
          </Tab.List>
          <Tab.Panels className="p-4">
            {/* Overview Panel */}
            <Tab.Panel>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Leadership History */}
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-4">Leadership History</h3>
                  {representative.leadership_history?.length > 0 ? (
                    <ul className="space-y-2">
                      {representative.leadership_history.map((leadership, index) => (
                        <li key={index} className="text-gray-600 dark:text-gray-300">
                          {leadership.type} - {leadership.congress}th Congress
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-300">No leadership positions found</p>
                  )}
                </div>

                {/* Party History */}
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-4">Party History</h3>
                  {representative.party_history?.length > 0 ? (
                    <ul className="space-y-2">
                      {representative.party_history.map((party, index) => (
                        <li key={index} className="text-gray-600 dark:text-gray-300">
                          {party.party_name} ({party.party_code}) - Since {party.start_year}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-300">No party history found</p>
                  )}
                </div>

                {/* Biography */}
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg md:col-span-2">
                  <h3 className="text-lg font-semibold mb-4">Biography</h3>
                  {bioLoading ? (
                    <div className="flex justify-center py-4">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                    </div>
                  ) : (
                    <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300">
                      {biography}
                    </div>
                  )}
                </div>

                {/* Contact Information */}
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg md:col-span-2">
                  <h3 className="text-lg font-semibold mb-4">Contact Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-gray-600 dark:text-gray-300">
                        <span className="font-semibold">Office:</span> {representative.office_address || 'N/A'}
                      </p>
                      <p className="text-gray-600 dark:text-gray-300">
                        <span className="font-semibold">Phone:</span> {representative.phone || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 dark:text-gray-300">
                        <span className="font-semibold">Website:</span>{' '}
                        {representative.url ? (
                          <a href={representative.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            Official Website
                          </a>
                        ) : (
                          'N/A'
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Tab.Panel>

            {/* Voting Record Panel */}
            <Tab.Panel>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">Voting Record</h3>
                <p className="text-gray-600 dark:text-gray-300">Coming soon...</p>
              </div>
            </Tab.Panel>

            {/* Sponsored Bills Panel */}
            <Tab.Panel>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">Sponsored and Co-sponsored Bills</h3>
                {representative.sponsored_bills?.length > 0 ? (
                  <ul className="space-y-2">
                    {representative.sponsored_bills.map((bill, index) => (
                      <li key={index}>
                        <a
                          href={`/bills/${bill.bill_number}`}
                          className="text-blue-600 hover:underline"
                        >
                          {bill.bill_number}
                        </a>
                        <span className="text-gray-600 dark:text-gray-300 ml-2">
                          - {bill.bill_title}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-600 dark:text-gray-300">No bills found</p>
                )}
              </div>
            </Tab.Panel>
          </Tab.Panels>
        </Tab.Group>
      </div>
    </div>
  );
};

export default RepresentativeDetails;
