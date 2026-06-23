import React, { useState, useRef, useEffect } from 'react';
import { Send, CloudRain, Thermometer, Droplets, MapPin, Mountain, RotateCw } from 'lucide-react';

export default function Results({ predictionResult, chatHistory = [], setChatHistory, restartPipeline }) {
  const [chatInput, setChatInput] = useState('');
  const chatContainerRef = useRef(null);
  const hasBootstrappedRef = useRef(false);

  useEffect(() => {
    if (!predictionResult || chatHistory.length > 0 || hasBootstrappedRef.current) return;

    const bootstrapChat = async () => {
      hasBootstrappedRef.current = true;
      const hiddenPrompt = `Explain the flood forecast for ${predictionResult.location_name || 'in plain English'}. What should residents know and do? Be concise and practical.`;

      try {
        const res = await fetch('/api/chat/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prediction_context: predictionResult?.prediction_context,
            chat_history: [],
            user_message: hiddenPrompt
          })
        });
        const data = await res.json();
        setChatHistory([{ role: 'assistant', content: data.response }]);
      } catch (err) {
        setChatHistory([{ 
          role: 'assistant', 
          content: `For ${predictionResult?.location_name || 'this location'}, the flood probability is low for the next 3 days. Residents should still monitor drainage, avoid dumping waste in drains, and stay alert for weather updates.`
        }]);
      }
    };

    bootstrapChat();
  }, [chatHistory.length, predictionResult, setChatHistory]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory]);

  // Dynamic style helpers based on individual day probability thresholds
  const getRiskStyle = (prob) => {
    const pct = Math.round((prob || 0) * 100);
    if (pct > 85) {
      return {
        cardBg: 'bg-rose-100/60 border-rose-200', // ⚡ Soft pastel red card canvas
        badge: 'text-rose-800 bg-rose-200/80 border-rose-300',
        progressBar: 'bg-rose-600',
        label: 'High'
      };
    }
    if (pct > 50) {
      return {
        cardBg: 'bg-amber-100/70 border-amber-200', // ⚡ Soft pastel yellow card canvas
        badge: 'text-amber-800 bg-amber-200 border-amber-300',
        progressBar: 'bg-amber-500',
        label: 'Moderate'
      };
    }
    return {
      cardBg: 'bg-white border-blue-100', // Default clean white look for safe parameters
      badge: 'text-emerald-700 bg-emerald-50 border-emerald-200/60',
      progressBar: 'bg-emerald-500',
      label: 'Normal'
    };
  };

  const getBannerStatus = (maxProb) => {
    if (maxProb === undefined || maxProb === null) return { text: 'ALL CLEAR', color: 'bg-emerald-500/10 border-emerald-500 text-emerald-700' };
    if (maxProb > 0.85) return { text: 'CRITICAL FLOOD ALERT', color: 'bg-rose-500/10 text-rose-700 border-rose-500 border' };
    if (maxProb > 0.50) return { text: 'WATCH ', color: 'bg-amber-500/10 text-amber-700 border-amber-600 border' };
    return { text: 'ALL CLEAR', color: 'bg-emerald-500/10 border-emerald-500 text-emerald-700' };
  };
  
  const getBannerSubText = (maxProb) => {
    if (maxProb === undefined || maxProb === null) return {text: ' No immediate risk detected', color: 'bg-emerald-500/10 border-emerald-500 text-emerald-700'};
    if (maxProb > 0.85) return { text: 'Chances of Severe Risk ', color: 'bg-rose-500/10 text-rose-700 border-rose-500 border' };
    if (maxProb > 0.50) return { text: 'Moderate Flood Risk ', color: 'bg-amber-500/10 text-amber-700 border-amber-600 border' };
    return { text: 'No immediate risk detected', color: 'bg-emerald-500/10 border-emerald-500 text-emerald-700' };
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    const userMessage = chatInput.trim();
    setChatInput('');
    
    const baseHistory = [...chatHistory, { role: 'user', content: userMessage }];
    setChatHistory(baseHistory);

    try {
      const res = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prediction_context: predictionResult?.prediction_context,
          chat_history: chatHistory,
          user_message: userMessage
        })
      });
      const data = await res.json();
      setChatHistory([...baseHistory, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setChatHistory([...baseHistory, { role: 'assistant', content: 'Gateway connection tracking failure.' }]);
    }
  };

  return (
    <div className="w-full space-y-6 animate-fadeIn text-gray-600 px-2 sm:px-0 overflow-x-hidden">
      <div className="flex flex-row items-center justify-between gap-2 sm:gap-3 pt-2">
        <div className="min-w-0">
          <p className="font-['DM_Mono'] text-[10px] sm:text-xs uppercase tracking-[0.35em] text-blue-400 whitespace-nowrap">
            3-DAY FLOOD FORECAST
          </p>
        </div>

        <button 
          type="button" 
          onClick={restartPipeline} 
          className="shrink-0 whitespace-nowrap px-2.5 sm:px-5 py-2 sm:py-2.5 rounded-xl font-bold border border-[#0A8F7A] bg-[#0A8F7A] text-white hover:bg-[#087363] transition-colors shadow-sm text-xs sm:text-sm inline-flex items-center gap-1.5 sm:gap-2"
        >
          <RotateCw className="h-3 w-3 sm:hidden" aria-hidden="true" />
          <span className="hidden sm:inline">New Prediction</span>
          <span className="sm:hidden">New</span>
        </button>
      </div>
      
      {/* Meta Indicators */}
      <div className="flex flex-wrap gap-2 mt-6 sm:mt-8 mb-4">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-['DM_Mono'] rounded-full bg-blue-500/10 text-blue-600 border border-blue-500/20">
          <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
          <span>{predictionResult?.location_name}</span>
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-['DM_Mono'] rounded-full bg-amber-500/10 text-amber-600 border border-amber-500/20">
          <Mountain className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Elev: {predictionResult?.elevation}m</span>
        </span>
      </div>

      {/* Dynamic Severity Banner Alert */}
      <div className={`p-5 rounded-xl border-l-4 font-bold transition-all duration-300 ${getBannerStatus(predictionResult?.max_probability).color}`}>
        <p className="mb-1">{getBannerStatus(predictionResult?.max_probability).text}</p>
        <p className="mb-1">{getBannerSubText(predictionResult?.max_probability).text}</p>
      </div>

      {/* ── 3-DAY CARDS ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {predictionResult?.days?.map((day, idx) => {
          const pct = Math.round((day.flood_prob || 0) * 100);
          const currentRiskStyle = getRiskStyle(day.flood_prob);

          return (
            <div 
              key={idx} 
              className={`border rounded-3xl p-5 flex flex-col justify-between shadow-sm min-h-[225px] transition-colors duration-300 ${currentRiskStyle.cardBg}`}
            >
              <div>
                <div className="flex justify-between items-center mb-3">
                  <p className="font-['DM_Mono'] text-xs text-gray-400 font-bold uppercase tracking-wider">{day.date}</p>
                  
                  {/* Dynamic Risk Level Badge */}
                  <span className={`inline-flex items-center px-3.5 py-1 text-[11px] sm:text-xs font-black tracking-wider rounded-full border uppercase ${currentRiskStyle.badge}`}>
                    {day.risk_level || currentRiskStyle.label}
                  </span>
                </div>

                <h4 className="text-2xl font-black text-gray-900 tracking-tight mb-0.5 font-['Syne']">
                  {day.flood_predicted ? 'Flood Danger' : 'All Clear'}
                </h4>
                <p className="text-xs text-gray-400 italic mb-4">
                  {day.flood_predicted ? 'Action advised' : 'No immediate concerns'}
                </p>
              </div>

              {/* Flood Probability Row */}
              <div className="w-full space-y-1 mb-3">
                <div className="flex justify-between font-medium text-xs text-gray-500">
                  <span>Flood probability</span>
                  <span className="font-bold">{pct}%</span>
                </div>
                <div className="w-full h-1 bg-gray-900/5 rounded-full overflow-hidden">
                  <div className={`h-full ${currentRiskStyle.progressBar}`} style={{ width: `${pct}%` }}></div>
                </div>
              </div>

              {/* Weather parameters */}
              <div className="flex flex-wrap items-center justify-start gap-x-4 gap-y-2 pt-2.5 border-t border-gray-900/5 text-[10px] sm:text-[11px] font-semibold text-gray-600 font-['DM_Mono']">
                <div className="flex items-center gap-1.5 whitespace-nowrap">
                  <CloudRain className="h-3.5 w-3.5 text-sky-500" aria-hidden="true" />
                  <span>{day.tp_mm?.toFixed(1)}mm</span>
                </div>
                <div className="flex items-center gap-1.5 whitespace-nowrap">
                  <Thermometer className="h-3.5 w-3.5 text-amber-500" aria-hidden="true" />
                  <span>{day.temp_c?.toFixed(1)}°C</span>
                </div>
                <div className="flex items-center gap-1.5 whitespace-nowrap">
                  <Droplets className="h-3.5 w-3.5 text-cyan-500" aria-hidden="true" />
                  <span>{day.swvl1?.toFixed(2)} m³/m³</span>
                </div>
              </div>

            </div>
          );
        })}
      </div>

      {/* ── CHAT AREA ── */}
      <div className="w-full pt-4 flex flex-col items-start">
        <h3 className="text-3xl font-black text-gray-900 tracking-tight mb-6 font-['Syne']">
          Ask FloodIQ AI
        </h3>

        <div className="w-full lg:w-[95%] mx-auto">
          <div ref={chatContainerRef} className="w-full overflow-y-auto mb-4 space-y-4 max-h-[450px] flex flex-col">
            {chatHistory.map((chat, idx) => (
              <div key={idx} className={`flex ${chat.role === 'user' ? 'justify-end' : 'justify-start'} w-full`}>
                <div className={`max-w-[90%] sm:max-w-[80%] lg:max-w-[650px] px-5 py-4 text-sm rounded-2xl leading-relaxed shadow-sm ${
                  chat.role === 'user' 
                    ? 'bg-[#0A8F7A] text-white rounded-br-none' 
                    : 'bg-[#F2F8FF] border border-blue-100/70 text-gray-800 rounded-bl-none whitespace-pre-line'
                }`}>
                  {chat.content?.split('\n').map((line, lIdx) => (
                    <p key={lIdx} className={lIdx > 0 ? "mt-1.5" : ""}>
                      {line.split(/(\*\*.*?\*\*)/g).map((part, pIdx) => {
                        if (part.startsWith('**') && part.endsWith('**')) {
                          return <strong key={pIdx} className="font-bold text-inherit">{part.slice(2, -2)}</strong>;
                        }
                        return part.replace(/\*/g, ''); 
                      })}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2 w-full max-w-3xl ml-auto px-2 sm:px-0">
            <input 
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendChatMessage()}
              placeholder="Ask about flood risk, safety tips, evacuation routes..."
              className="flex-1 p-3.5 rounded-xl border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#0A8F7A] shadow-sm text-gray-800"
            />
            <button 
              type="button" 
              onClick={sendChatMessage} 
              aria-label="Send message"
              className="bg-[#0A8F7A] hover:bg-[#087363] text-white px-5 rounded-xl font-bold text-sm transition-colors shadow-sm inline-flex items-center justify-center"
            >
              <Send className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}