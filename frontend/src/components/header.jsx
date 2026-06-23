import React from 'react';

export default function Header({ onNavigateHome }) {
  return (
    <header className="w-full text-left flex justify-start items-center pt-[3rem]">
      <button
        type="button"
        onClick={onNavigateHome}
        className="flex items-center gap-2.5 text-left cursor-pointer"
        aria-label="Go to landing page"
      >
        <img
          src="/logo.png" 
          alt="FloodIQ Logo" 
          className="w-12 h-12 sm:w-16 sm:h-16 object-contain" 
        />
        <div className="flex flex-col -space-y-1 text-left">
          {/* ⚡ Added !text-3xl and sm:!text-5xl to forcefully break out of the index.css clamp */}
          <h1 className="font-['Syne'] font-black !text-3xl sm:!text-5xl tracking-tight text-gray-900 leading-none">
            FloodIQ
          </h1>
          <p className="font-['DM_Mono'] text-[11px] sm:text-sm tracking-[0.15em] text-[#0A8F7A] uppercase mt-0 leading-none">
            Lagos Flood Prediction
          </p>
        </div>
      </button>
    </header>
  );
}