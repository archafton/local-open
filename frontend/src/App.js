import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Bills from './pages/Bills';
import BillDetails from './pages/BillDetails';
import Representatives from './pages/Representatives';
import RepresentativeDetails from './pages/RepresentativeDetails';
import Analytics from './pages/Analytics';
import Profile from './pages/Profile';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/bills" element={<Bills />} />
        <Route path="/bills/:billNumber" element={<BillDetails />} />
        <Route path="/representatives" element={<Representatives />} />
        <Route path="/representatives/:bioguideId" element={<RepresentativeDetails />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Layout>
  );
}

export default App;
