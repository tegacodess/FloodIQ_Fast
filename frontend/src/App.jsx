import React, { useState, useEffect } from 'react';
import Header from './components/header';
import LandingPanel from './components/landing';
import QueryForm from './components/queryform';
import ForecastResults from './components/results';
import './App.css';
import {Analytics} from '@vercel/analytics/react';
const BASE_URL = import.meta.env.VITE_API_URL || '';

// Persists a piece of state to sessionStorage, so it survives a page
// reload but clears itself when the tab/browser is closed.
function usePersistedState(key, defaultValue) {
  const [state, setState] = useState(() => {
    try {
      const stored = sessionStorage.getItem(key);
      return stored !== null ? JSON.parse(stored) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  useEffect(() => {
    try {
      if (state === null || state === undefined) {
        sessionStorage.removeItem(key);
      } else {
        sessionStorage.setItem(key, JSON.stringify(state));
      }
    } catch {
      // sessionStorage unavailable will fail silently,
      // app still works, it just won't survive a reload
    }
  }, [key, state]);

  return [state, setState];
}

export default function App() {
  // Persisted: which page + the actual prediction data
  const [page, setPage] = usePersistedState('floodiq_page', 'intro');
  const [predictionResult, setPredictionResult] = usePersistedState('floodiq_prediction', null);

  // NOT persisted: form selection and chat history reset on every reload
  const [locationData, setLocationData] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // Safety net: if a reload somehow lands on 'results' without a prediction
  // (e.g. sessionStorage was cleared but not in sync), fall back to 'form'
  // instead of rendering a blank page.
  useEffect(() => {
    if (page === 'results' && !predictionResult) {
      setPage('form');
    }
  }, []); // only check once, on mount

  const executeSimulation = async (dateInput, searchQuery, setLookupStatus) => {
    if (!locationData) return alert("Please clarify your target Lagos coordinates first.");
    setLoading(true);

    try {
      const res = await fetch(`${BASE_URL}/api/predict`, {
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
    setPredictionResult(null);
    setChatHistory([]);
    setLocationData(null);
    setPage('intro');
  };

  return (
    <div className="min-h-screen w-full bg-white text-gray-800 py-4 sm:py-8">
      <div className="w-full px-4 sm:px-8 lg:px-16">
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

        <Analytics />
      </div>
    </div>
  );
}