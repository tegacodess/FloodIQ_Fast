import React from 'react';

export default function Header({ onNavigateHome }) {
  return (
    //  Text-left and justify-start completely pins the branding block to the left boundary edge
    <header className="w-full text-left flex justify-start items-center pt-[3rem]">
      <button
        type="button"
        onClick={onNavigateHome}
        className="flex items-center gap-3 text-left cursor-pointer"
        aria-label="Go to landing page"
      >
        <img
          src="/logo.png" 
          alt="FloodIQ Logo" 
          className="w-10 h-10 sm:w-12 sm:h-12" 
        />
        <div className="text-left">
          <h1 className="font-['Syne'] font-black text-2xl sm:text-4xl tracking-tight text-gray-900 leading-none">
            FloodIQ
          </h1>
          <p className="font-['DM_Mono'] text-[10px] sm:text-xs tracking-widest text-[#0A8F7A] uppercase mt-1 leading-none">
            Lagos Flood Prediction
          </p>
        </div>
      </button>
    </header>
  );
}