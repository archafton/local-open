import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const BillDetails = () => {
  const { billNumber } = useParams();
  const navigate = useNavigate();
  const [bill, setBill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBillDetails = async () => {
      setLoading(true);
      try {
        const response = await fetch(`http://localhost:5001/api/bills/${billNumber}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Bill data:', data); // Debug log
        setBill(data);
      } catch (error) {
        console.error("Could not fetch bill details:", error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchBillDetails();
  }, [billNumber]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const calculateLifespan = (introducedDate, latestDate) => {
    if (!introducedDate || !latestDate) return 'N/A';
    const start = new Date(introducedDate);
    const end = new Date(latestDate);
    const days = Math.floor((end - start) / (1000 * 60 * 60 * 24));
    return `${days} days`;
  };

  const handleRepClick = (bioguideId) => {
    if (bioguideId) {
      navigate(`/representatives/${bioguideId}`);
    }
  };

  // Safely get the latest summary
  const getLatestSummary = () => {
    if (!bill?.summary || !Array.isArray(bill.summary) || bill.summary.length === 0) {
      return null;
    }
    return bill.summary[bill.summary.length - 1];
  };

  // Get the initial and latest text versions
  const getDisplayTextVersions = () => {
    if (!bill?.text_versions || !Array.isArray(bill.text_versions) || bill.text_versions.length === 0) {
      return [];
    }

    const versions = [...bill.text_versions];
    const initialVersion = versions.find(v => v.is_initial_version);
    const latestVersion = versions.reduce((latest, current) => {
      if (!latest || !latest.date) return current;
      if (!current.date) return latest;
      return new Date(current.date) > new Date(latest.date) ? current : latest;
    }, null);

    // Return both versions if they're different, otherwise just return the latest
    if (initialVersion && latestVersion && initialVersion !== latestVersion) {
      return [initialVersion, latestVersion];
    }
    return [latestVersion];
  };

  // Match text versions with actions based on type and date
  const getTextVersionsForAction = (action) => {
    if (!bill?.text_versions || !Array.isArray(bill.text_versions)) {
      return [];
    }

    // Define action type to text version type mapping
    const actionTypeMap = {
      'President': ['Public Law', 'Enrolled Bill'],
      'Floor': ['Engrossed in Senate', 'Engrossed in House', 'Placed on Calendar Senate', 'Placed on Calendar House']
    };

    // Get the expected version types for this action
    const expectedTypes = actionTypeMap[action.action_type] || [];

    // Find matching versions based on date and type
    return bill.text_versions.filter(version => {
      // Skip if no date match
      if (!version.date || !action.action_date) return false;
      
      // Compare dates (ignoring time)
      const versionDate = new Date(version.date).toISOString().split('T')[0];
      const actionDate = new Date(action.action_date).toISOString().split('T')[0];
      if (versionDate !== actionDate) return false;

      // Check if version type matches expected types for this action
      return expectedTypes.includes(version.type);
    });
  };

  // Format the version type for display
  const formatVersionType = (version) => {
    if (version.is_initial_version) {
      return 'Initial Version';
    }
    return version.type;
  };

  // Render format links with proper display names
  const renderFormatLinks = (formats) => {
    return formats.map((format, idx) => (
      <a
        key={idx}
        href={format.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center px-2.5 py-1.5 text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 mr-2"
      >
        {format.display_type || format.type}
      </a>
    ));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 dark:border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 text-center p-4">
        Error loading bill details: {error}
      </div>
    );
  }

  if (!bill) {
    return (
      <div className="text-center p-4">
        Bill not found
      </div>
    );
  }

  const latestSummary = getLatestSummary();
  const displayTextVersions = getDisplayTextVersions();

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2 text-gray-800 dark:text-white">
              {bill.bill_number}
            </h1>
            <h2 className="text-xl mb-4 text-gray-600 dark:text-gray-300">
              {bill.bill_title}
            </h2>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p>Congress: {bill.congress}</p>
              <p>Introduced: {formatDate(bill.introduced_date)}</p>
              <p>Status: {bill.status}</p>
              {displayTextVersions.map((version, idx) => (
                <div key={idx} className="mt-2">
                  <p className="font-semibold mb-1">
                    {formatVersionType(version)}
                    {version.date && ` (${formatDate(version.date)})`}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {version.formats && renderFormatLinks(version.formats)}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="md:text-right">
            <div className="mb-4">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300">Sponsor</h3>
              {bill.sponsor_id ? (
                <button
                  onClick={() => handleRepClick(bill.sponsor_id)}
                  className="text-blue-600 dark:text-blue-400 hover:underline text-lg"
                >
                  {bill.sponsor_name}
                </button>
              ) : (
                <p className="text-lg">{bill.sponsor_name}</p>
              )}
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {bill.sponsor_party} - {bill.sponsor_chamber}
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 dark:text-gray-300">Tags</h3>
              <div className="flex flex-wrap justify-end gap-2 mt-2">
                {bill.tags && bill.tags.map((tag, index) => (
                  <span key={index} className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Associated Representatives Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">Associated Representatives</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full table-auto">
            <thead>
              <tr className="bg-gray-100 dark:bg-gray-700">
                <th className="px-4 py-2 text-left">Name</th>
                <th className="px-4 py-2 text-left">Party</th>
                <th className="px-4 py-2 text-left">Chamber</th>
                <th className="px-4 py-2 text-left">Role</th>
              </tr>
            </thead>
            <tbody>
              {/* Sponsor Row */}
              <tr className="border-b dark:border-gray-700">
                <td className="px-4 py-2">
                  {bill.sponsor_id ? (
                    <button
                      onClick={() => handleRepClick(bill.sponsor_id)}
                      className="text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {bill.sponsor_name}
                    </button>
                  ) : (
                    bill.sponsor_name
                  )}
                </td>
                <td className="px-4 py-2">{bill.sponsor_party}</td>
                <td className="px-4 py-2">{bill.sponsor_chamber}</td>
                <td className="px-4 py-2">
                  <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                    Sponsor
                  </span>
                </td>
              </tr>
              {/* Cosponsor Rows */}
              {bill.cosponsors && bill.cosponsors.map((cosponsor, index) => (
                <tr key={index} className="border-b dark:border-gray-700">
                  <td className="px-4 py-2">
                    {cosponsor.cosponsor_id ? (
                      <button
                        onClick={() => handleRepClick(cosponsor.cosponsor_id)}
                        className="text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        {cosponsor.full_name}
                      </button>
                    ) : (
                      cosponsor.full_name
                    )}
                  </td>
                  <td className="px-4 py-2">{cosponsor.party}</td>
                  <td className="px-4 py-2">{cosponsor.chamber}</td>
                  <td className="px-4 py-2">
                    <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      Cosponsor
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Section */}
      {latestSummary && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">Bill Summary</h2>
          <div className="prose dark:prose-invert max-w-none">
            <div dangerouslySetInnerHTML={{ __html: latestSummary.text }} />
          </div>
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            <p>Last Updated: {formatDate(latestSummary.action_date)}</p>
            <p>Version: {latestSummary.action_desc}</p>
          </div>
        </div>
      )}

      {/* Timeline Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">Bill Timeline</h2>
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700"></div>
          {bill.actions && bill.actions.map((action, index) => {
            const textVersions = getTextVersionsForAction(action);
            
            return (
              <div key={index} className="relative pl-8 pb-6">
                <div className="absolute left-2 w-4 h-4 bg-blue-500 rounded-full -ml-2"></div>
                <div className="text-sm">
                  <div className="font-semibold text-gray-800 dark:text-white">
                    {formatDate(action.action_date)}
                  </div>
                  <div className="mt-1 text-gray-600 dark:text-gray-400">
                    {action.action_text}
                  </div>
                  {textVersions.map((version, vIdx) => (
                    <div key={vIdx} className="mt-2">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {formatVersionType(version)}:
                      </p>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {version.formats && renderFormatLinks(version.formats)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        <div className="mt-4 text-right text-sm text-gray-600 dark:text-gray-400">
          Bill Lifespan: {calculateLifespan(bill.introduced_date, bill.latest_action_date)}
        </div>
      </div>
    </div>
  );
};

export default BillDetails;
