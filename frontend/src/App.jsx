import React, { useState } from 'react';
import Header from './components/header';
import LandingPanel from './components/landing';
import QueryForm from './components/queryform';
import ForecastResults from './components/results';
import './App.css';

export default function App() {
  // 💡 State values simplified to focus exclusively on routing pages
  const [page, setPage] = useState('intro');
  const [locationData, setLocationData] = useState(null);
  const [predictionResult, setPredictionResult] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const executeSimulation = async (dateInput, searchQuery, setLookupStatus) => {
    if (!locationData) return alert("Please clarify your target Lagos coordinates first.");
    setLoading(true);

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: locationData.lat,
          lon: locationData.lon,
          location_name: locationData.name,
          target_date: dateInput || null
        })
      });
      if (!res.ok) throw new Error("Backend pipeline processing fault.");
      
      const data = await res.json();
      setPredictionResult(data);
      setPage('results');
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const restartPipeline = () => {
    setPredictionResult(null);
    setChatHistory([]);
    setLocationData(null);
    setPage('form');
  };

  const navigateHome = () => {
    setPage('intro');
  };

  return (
  // 💡 FIXED: py-4 on mobile bumps up to py-8 on desktop. Left/right margin tracking optimized.
  <div className="min-h-screen w-full bg-white text-gray-800 py-4 sm:py-8">
    <div className="w-full px-4 sm:px-8 lg:px-16">
      {/* 💡 FIXED: mb-4 on mobile reduces the huge gap before the hero card snaps in */}
      <div className="mb-4 sm:mb-10 w-full text-left">
        <Header onNavigateHome={navigateHome} />
      </div>
      
      {page === 'intro' && <LandingPanel setPage={setPage} />}
      
      {page === 'form' && (
        <QueryForm 
          setPage={setPage} 
          locationData={locationData}
          setLocationData={setLocationData}
          executeSimulation={executeSimulation}
          loading={loading}
        />
      )}
      
      {page === 'results' && predictionResult && (
        <ForecastResults 
          predictionResult={predictionResult}
          chatHistory={chatHistory}
          setChatHistory={setChatHistory}
          restartPipeline={restartPipeline}
        />
      )}
    </div>
  </div>
);
}