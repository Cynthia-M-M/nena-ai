import React from 'react';
import { useAuth, DEMO_PERSONAS } from '../context/AuthContext';
import {
  ShieldCheck,
  Building2,
  Wifi,
  WifiOff,
  RefreshCw,
  Activity
} from 'lucide-react';

interface NavbarProps {
  activeTab: 'clinic' | 'funder' | 'audit';
  setActiveTab: (tab: 'clinic' | 'funder' | 'audit') => void;
  onOpenSyncQueue: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, onOpenSyncQueue }) => {
  const { currentUser, switchUser, isOnline, toggleOfflineSimulation, pendingSyncCount } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-[#0A3D91] text-white shadow-md border-b border-blue-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand & Logo */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('clinic')}>
            <img
              src="/nena-ai-logo.png"
              alt="Nena AI"
              className="h-10 w-10 object-contain rounded-lg bg-white p-1 shadow-sm"
              onError={(e) => {
                // Fallback to text icon if image fails
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white">Nena AI</span>
                <span className="text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-mono font-medium">
                  v0.2 Zero-Trust
                </span>
              </div>
              <p className="text-xs text-blue-200 hidden sm:block">Healthcare Subsidy Routing Ledger</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('clinic')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'clinic'
                  ? 'bg-blue-800 text-white shadow-inner'
                  : 'text-blue-100 hover:bg-blue-800/50 hover:text-white'
              }`}
            >
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Clinic Portal</span>
            </button>

            <button
              onClick={() => setActiveTab('funder')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'funder'
                  ? 'bg-blue-800 text-white shadow-inner'
                  : 'text-blue-100 hover:bg-blue-800/50 hover:text-white'
              }`}
            >
              <Building2 className="w-4 h-4 text-cyan-400" />
              <span>NGO Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'audit'
                  ? 'bg-blue-800 text-white shadow-inner'
                  : 'text-blue-100 hover:bg-blue-800/50 hover:text-white'
              }`}
            >
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span>Zero-Trust Audit</span>
            </button>
          </nav>

          {/* Right Controls: Connectivity, Offline Queue & Role Switcher */}
          <div className="flex items-center space-x-3">
            
            {/* Offline Sync Badge */}
            {pendingSyncCount > 0 && (
              <button
                onClick={onOpenSyncQueue}
                className="flex items-center space-x-1.5 bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2.5 py-1 rounded-full text-xs font-semibold animate-pulse hover:bg-amber-500/30"
                title="Pending offline encounters queued in IndexedDB"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>{pendingSyncCount} Queued</span>
              </button>
            )}

            {/* Network / Offline Simulator Toggle */}
            <button
              onClick={toggleOfflineSimulation}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                isOnline
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
                  : 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30'
              }`}
              title={isOnline ? 'Online (Click to simulate offline network drop)' : 'Simulated Offline (Click to restore network)'}
            >
              {isOnline ? <Wifi className="w-3.5 h-3.5 text-emerald-400" /> : <WifiOff className="w-3.5 h-3.5 text-amber-400" />}
              <span className="hidden md:inline">{isOnline ? 'Online' : 'Offline'}</span>
            </button>

            {/* Demo Role Switcher Dropdown */}
            <div className="relative group">
              <select
                value={currentUser.user_id}
                onChange={(e) => {
                  const selected = DEMO_PERSONAS.find(p => p.user_id === e.target.value);
                  if (selected) switchUser(selected);
                }}
                className="bg-blue-950 text-xs text-white border border-blue-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-400 font-medium cursor-pointer"
              >
                {DEMO_PERSONAS.map((persona) => (
                  <option key={persona.user_id} value={persona.user_id} className="bg-slate-900 text-white">
                    {persona.name} ({persona.organization_name.split(' ')[0]})
                  </option>
                ))}
              </select>
            </div>

          </div>

        </div>
      </div>
    </header>
  );
};
