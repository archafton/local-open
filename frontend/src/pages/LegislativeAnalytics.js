import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import BillsPerCongress from '../components/analytics/legislative/BillsPerCongress';
import BillsByStatus from '../components/analytics/legislative/BillsByStatus';
import IntroductionToPassage from '../components/analytics/legislative/IntroductionToPassage';
import SponsorActivity from '../components/analytics/legislative/SponsorActivity';

const LegislativeAnalytics = () => {
  return (
    <Routes>
      <Route path="bills-per-congress" element={<BillsPerCongress />} />
      <Route path="bills-by-status" element={<BillsByStatus />} />
      <Route path="passage-time" element={<IntroductionToPassage />} />
      <Route path="sponsor-activity" element={<SponsorActivity />} />
      <Route path="/" element={<Navigate to="bills-per-congress" replace />} />
    </Routes>
  );
};

export default LegislativeAnalytics;
