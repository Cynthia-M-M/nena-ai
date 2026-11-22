import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { ClinicPortal } from './components/ClinicPortal';
import { FunderDashboard } from './components/FunderDashboard';
import { AuditConsole } from './components/AuditConsole';
import { Database, Lock, Activity, HeartHandshake } from 'lucide-react';

const MainLayout: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'clinic' | 'funder' | 'audit'>('clinic');
  const [openOfflineQueueTrigger, setOpenOfflineQueueTrigger] = useState<number>(0);
  const { currentUser } = useAuth();

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-800 flex flex-col font-sans">
      {/* Top Sticky Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenSyncQueue={() => {
          setActiveTab('clinic');
          setOpenOfflineQueueTrigger((prev) => prev + 1);
        }}
      />

      {/* Hero Sub-header / Status Bar */}
      <div className="bg-white border-b border-slate-200 py-2.5 px-4 sm:px-6 lg:px-8 text-xs">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div className="flex items-center space-x-2 text-slate-600">
            <span className="font-semibold text-slate-900">Current Role:</span>
            <span className="font-mono bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200">
              {currentUser.role}
            </span>
            <span>•</span>
            <span className="text-slate-700 font-medium">{currentUser.organization_name}</span>
          </div>

          <div className="flex items-center space-x-4 text-slate-500 text-[11px]">
            <span className="flex items-center space-x-1">
              <Lock className="w-3.5 h-3.5 text-emerald-600" />
              <span>Zero-Trust 4-Stage Engine</span>
            </span>
            <span className="flex items-center space-x-1">
              <Database className="w-3.5 h-3.5 text-blue-600" />
              <span>SHA-256 Chained Ledger</span>
            </span>
            <span className="flex items-center space-x-1">
              <Activity className="w-3.5 h-3.5 text-cyan-600" />
              <span>M-Pesa Daraja Payouts</span>
            </span>
          </div>
        </div>
      </div>

      {/* Main Content Pane */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'clinic' && <ClinicPortal key={openOfflineQueueTrigger} />}
        {activeTab === 'funder' && <FunderDashboard />}
        {activeTab === 'audit' && <AuditConsole />}
      </main>

      {/* Institutional Platform Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 px-4 sm:px-6 lg:px-8 text-xs text-slate-500 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <img
              src="/nena-ai-logo.png"
              alt="Nena AI"
              className="h-6 w-6 object-contain rounded"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <div>
              <p className="font-bold text-slate-800">Nena AI Healthcare Subsidy Exchange</p>
              <p className="text-[11px] text-slate-400">
                Direct Clinic-to-Funder Zero-Trust Settlement Platform • Republic of Kenya
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-[11px]">
            <span className="inline-flex items-center text-emerald-700 font-semibold">
              <HeartHandshake className="w-3.5 h-3.5 mr-1" />
              Patient Copay: KES 0 Guaranteed
            </span>
            <span>•</span>
            <span>HMAC PII Pseudonymization</span>
            <span>•</span>
            <span>Append-Only PostgREST Ledger</span>
            <span>•</span>
            <span>RFC-7519 JWT RBAC</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}
