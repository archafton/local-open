import React from 'react';

const Home = () => {
  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold mb-4">Welcome to Tacitus</h1>
      <p className="text-xl mb-8">Your gateway to legislative data and analysis</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold mb-2">Bills</h2>
          <p>Search and view legislative bills</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold mb-2">Representatives</h2>
          <p>Explore information about congressional members</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold mb-2">Analytics</h2>
          <p>Dive into pre-built dashboards and insights</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
