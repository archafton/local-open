import React from 'react';
import { Link } from 'react-router-dom';

const BackToAnalytics = () => {
  return (
    <Link
      to="/analytics"
      className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline mb-6"
    >
      <svg
        className="w-4 h-4 mr-2"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 19l-7-7 7-7"
        />
      </svg>
      Back to Analytics Dashboard
    </Link>
  );
};

export default BackToAnalytics;
