import React from 'react';
import { Home, Building2, Users, MapPin, CloudRain, BarChart2 } from 'lucide-react';

const steps = [
  { Icon: MapPin,    title: 'Pick a location & date',      desc: 'Choose any neighbourhood across Lagos.' },
  { Icon: CloudRain, title: 'We pull the weather data',     desc: 'Live forecasts, archives, or seasonal estimates obtained automatically.' },
  { Icon: BarChart2, title: 'You find out if it floods',      desc: 'A 3-day flood outlook with AI-guided next steps.' },
];

const audiences = [
  { Icon: Home,      label: 'Homeowners & residents', body: "Know your street's risk before you leave home, move a vehicle, or decide where to store valuables." },
  { Icon: Building2, label: 'Real estate & property', body: "Screen a site's flood exposure before you list, acquire, or lease any property." },
  { Icon: Users,     label: 'Employers & teams',      body: 'Prioritize team safety and plan proactive outreach to your local customers.' }
];

export default function Landing({ setPage }) {
  return (
    <div className="w-full flex flex-col gap-10 animate-fadeIn text-gray-600">

      {/* ── HERO BANNER SECTION ── */}
      <div className="mt-6 border border-gray-200/80 bg-[#F2F8FF] rounded-2xl shadow-sm py-4 px-5 sm:py-5 sm:px-7 flex flex-col gap-8 w-full">
        
        {/* Core Header Text Elements */}
        <div>
          <h2 className="font-['Syne'] font-black text-3xl sm:text-4xl md:text-5xl text-gray-900 tracking-tight leading-tight mb-4">
            The intelligent tool you need.
          </h2>
          <p className="font-['DM_Mono'] text-sm sm:text-base leading-relaxed max-w-2xl text-gray-500">
            FloodIQ gives you a clear low, moderate, or high flood risk outlook for any Lagos location, so you act before water does.
          </p>
        </div>

        {/* ⚡ RESPONSIVE: Stacks on mobile, splits into 3 columns on tablets/desktops */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-gray-300/40">
          {steps.map(({ Icon, title, desc }) => (
            <div key={title} className="flex gap-4 items-start w-full">
              <div className="w-10 h-10 rounded-xl bg-[#0A8F7A]/10 flex items-center justify-center shrink-0">
                <Icon size={16} className="text-[#0A8F7A]" strokeWidth={2.5} />
              </div>
              <div className="w-full">
                <p className="font-['Syne'] text-gray-800 text-sm sm:text-base font-bold mb-0.5">{title}</p>
                <p className="font-['DM_Mono'] text-xs leading-relaxed font-medium text-gray-500/90">{desc}</p>
              </div>
            </div>
          ))}
        </div>

      </div>

      {/* ── TARGETED USER AUDIENCES GRID SECTION ── */}
      <div className="w-full">
        <p className="font-['Syne'] text-[10px] tracking-widest text-[#0A8F7A] font-bold uppercase mb-3 px-1">
          Built for
        </p>
        {/* ⚡ RESPONSIVE: Single column on small screens, 3 columns on medium screens and up */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
          {audiences.map(({ Icon, label, body }) => (
            <div
              key={label}
              className="border border-gray-200/80 bg-[#F2F8FF] rounded-2xl p-6 flex flex-col gap-3 shadow-sm hover:border-[#0A8F7A]/30 transition-colors w-full"
            >
              <div className="w-10 h-10 rounded-xl bg-[#0A8F7A]/10 flex items-center justify-center shrink-0">
                <Icon size={17} className="text-[#0A8F7A]" strokeWidth={2} />
              </div>
              <p className="font-['Syne'] text-gray-900 text-sm font-black tracking-tight">{label}</p>
              <p className="font-['DM_Mono'] text-xs font-medium leading-relaxed text-gray-500">{body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── CTA BUTTON ── */}
      <div className="w-full flex justify-center pt-2">
        <button
          type="button"
          onClick={() => setPage('form')}
          className="font-['DM_Mono'] w-full sm:w-auto sm:min-w-[360px] bg-[#0A8F7A] hover:bg-[#087363] text-white font-bold py-4 px-8 rounded-xl text-center text-sm shadow-md active:scale-[0.99] transition-all duration-150"
        >
          Try FloodIQ Now
        </button>
      </div>

    </div>
  );
}