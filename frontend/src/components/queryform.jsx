import React, { useState } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || '';

export default function QueryForm({ setPage, locationData, setLocationData, executeSimulation, loading }) {
  const [dateInput, setDateInput] = useState(new Date().toISOString().split('T')[0]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('area'); // Options: 'area', 'auto'
  const [lookupStatus, setLookupStatus] = useState({ text: '', type: '' });
  const [isDetecting, setIsDetecting] = useState(false);

  const handleAutoLocation = () => {
    if (!navigator.geolocation) {
      setLookupStatus({ text: 'Geolocation is not supported by your browser.', type: 'error' });
      return;
    }

    setIsDetecting(true);
    setLookupStatus({ text: 'Searching...', type: 'info' });

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        
        
        try {
          const res = await fetch(`${BASE_URL}/api/reverse-geocode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: latitude, lon: longitude })
          });
          const data = await res.json();
          const resolvedName = data.found ? (data.display_name || 'Unknown Location') : 'Unknown Location';
          
          setLocationData({ lat: latitude, lon: longitude, name: resolvedName });
          setSearchQuery(resolvedName);
          setLookupStatus({ 
            text: data.found ? `${resolvedName} (${latitude.toFixed(3)} , ${longitude.toFixed(3)})` : "GPS linked, but failed to identify area name", 
            type: data.found ? 'success' : 'error' 
          });
        } catch (err) {
          setLocationData({ lat: latitude, lon: longitude, name: "Current Location" });
          setSearchQuery("Current Location");
          setLookupStatus({ text: 'GPS linked, but network reverse geocoding failed.', type: 'error' });
        } finally {
          setIsDetecting(false);
        }
      },
      () => {
        setLookupStatus({ text: 'Unable to retrieve location settings from device.', type: 'error' });
        setIsDetecting(false);
      }
    ); 
  };

  // Triggers when switching tabs
  const handleTabSwitch = (tab) => {
    setActiveTab(tab);
    // Clear out residual states unless it's an active success match
    if (lookupStatus.type !== 'success') {
      setLookupStatus({ text: '', type: '' });
    }
    
    // If the user clicks Auto Detect, immediately fire the GPS pipeline!
    if (tab === 'auto') {
      handleAutoLocation();
    }
  };

  const handleAreaLookup = async () => {
    if (!searchQuery.trim()) return;
    try {
      const res = await fetch(`${BASE_URL}/api/area-lookup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery })
      });
      if (!res.ok) {
        const text = await res.text().catch(() => res.statusText || 'Server error');
        throw new Error(`Server returned ${res.status}: ${text}`);
      }
      const data = await res.json();
      if (data.found) {
        setLocationData({ lat: data.lat, lon: data.lon, name: data.display_name });
        const display = data.display_name || searchQuery;
        setLookupStatus({ text: `${display} (${data.lat.toFixed(3)} , ${data.lon.toFixed(3)})`, type: 'success' });
      } else {
        setLocationData(null);
        setLookupStatus({ text: 'Location index not found. Try: Yaba, Ikeja, Lekki...', type: 'error' });
      }
    } catch (err) {
      setLookupStatus({ text: err.message || 'Connection timeout matching area grid maps.', type: 'error' });
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto border border-gray-200 bg-[#F2F8FF] p-5 sm:p-8 rounded-2xl shadow-sm animate-fadeIn mt-10 sm:mt-12 lg:mt-14">
      
      {/* Target Date Input Container */}
      <div className="mb-6">
        <label className="block font-['DM_Mono'] text-xs text-gray-400 uppercase mb-2 tracking-wider">Enter Date</label>
        <input 
          type="date" 
          value={dateInput}
          onChange={(e) => setDateInput(e.target.value)}
          className="w-full p-3.5 rounded-xl border border-gray-300 bg-white font-medium text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#0A8F7A] transition-shadow shadow-sm"
        />
      </div>

      {/* ── RESPONSIVE NAVIGATION SLIDE TABS AREA ── */}
      <div className="mb-6 w-full">
        <label className="block font-['DM_Mono'] text-xs text-gray-400 uppercase mb-3 tracking-wider">User Location</label>
        
        {/* Tab Row Element Switcher */}
        <div className="flex border-b border-gray-200 text-sm font-medium mb-4">
          <button
            type="button"
            onClick={() => handleTabSwitch('area')}
            className={`pb-2.5 px-4 font-semibold border-b-2 transition-all ${activeTab === 'area' ? 'border-[#0A8F7A] text-[#0A8F7A] font-black' : 'border-transparent text-gray-400 hover:text-gray-600'}`}
          >
            Area Name
          </button>
          <button
            type="button"
            onClick={() => handleTabSwitch('auto')}
            className={`pb-2.5 px-4 font-semibold border-b-2 transition-all ${activeTab === 'auto' ? 'border-[#0A8F7A] text-[#0A8F7A] font-black' : 'border-transparent text-gray-400 hover:text-gray-600'}`}
          >
            Auto Detect
          </button>
        </div>

        {/* ── TAB LAYOUT CHANNELS ── */}
        <div className="w-full min-h-[60px]">
          
          {/* TAB 1: Area Text Box Query Input */}
          {activeTab === 'area' && (
            <form 
              onSubmit={(e) => { e.preventDefault(); handleAreaLookup(); }}
              className="flex gap-2 w-full animate-fadeIn"
            >
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ikeja, Lekki, VI, Surulere, Yaba..."
                className="flex-1 min-w-0 p-3.5 rounded-xl border border-gray-300 bg-white font-medium text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#0A8F7A] shadow-sm"
              />
              <button 
                type="submit" 
                className="bg-[#0A8F7A]/10 text-[#0A8F7A] hover:bg-[#0A8F7A]/20 px-5 rounded-xl font-bold border border-[#0A8F7A]/20 transition-colors shrink-0"
              >
                Match
              </button>
            </form>
          )}

          {/* TAB 2: Instant GPS Panel (No secondary button needed!) */}
          {activeTab === 'auto' && (
            <div className="w-full animate-fadeIn py-2">
              {isDetecting ? (
                <div className="flex items-center gap-3 text-[#0A8F7A] font-medium text-sm animate-pulse">
                  <span className="w-4 h-4 rounded-full border-2 border-[#0A8F7A] border-t-transparent animate-spin"></span>
                  Contacting device location system...
                </div>
              ) : !lookupStatus.text ? (
                <p className="text-xs text-gray-400 font-medium italic">Clicking this tab initializes direct browser geolocation pings.</p>
              ) : null}
            </div>
          )}

        </div>

        {/* Unified Status Notifications Container (Themed Colors matched perfectly) */}
        {lookupStatus.text && lookupStatus.type !== 'info' && (
          <div className={`mt-3 p-3.5 rounded-xl text-sm font-semibold tracking-wide ${
            lookupStatus.type === 'success' 
              ? 'bg-[#0A8F7A]/10 text-[#0A8F7A]' // Theme Teal accent palette match!
              : 'bg-rose-500/10 text-rose-600'
          }`}>
            {lookupStatus.text}
          </div>
        )}
      </div>

      {/* Bottom Main Navigation Action Rows */}
      <div className="flex flex-col-reverse sm:flex-row gap-3 w-full pt-4 border-t border-gray-200/50">
        <button 
          type="button" 
          onClick={() => setPage('intro')} 
          className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold bg-white border border-gray-300 text-gray-700 hover:bg-gray-100/50 transition-colors text-sm"
        >
          ← Back
        </button>
        <div className="flex-1 w-full">
          <button 
            type="button"
            onClick={() => executeSimulation(dateInput, searchQuery, setLookupStatus)}
            disabled={loading || !locationData}
            className="w-full bg-[#0A8F7A] hover:bg-[#087363] text-white font-black py-3.5 px-6 rounded-xl disabled:opacity-40 shadow-sm transition-colors text-center text-sm tracking-wide font-['Syne']"
          >
            Predict
          </button>
          {loading && lookupStatus.type === 'info' && (
            <p className="mt-2 text-xs font-medium text-[#0A8F7A]">
              {lookupStatus.text || 'Fetching weather data...'}
            </p>
          )}
        </div>
      </div>

    </div>
  );
}