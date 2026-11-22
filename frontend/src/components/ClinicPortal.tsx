import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { offlineQueue } from '../services/offlineQueue';
import type { TreatmentCode, FundingProgram, EncounterDetail, OfflineQueueItem } from '../types';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  Smartphone,
  ShieldCheck,
  Send,
  RefreshCw,
  Wallet,
  User,
  KeyRound,
  AlertCircle,
  Database
} from 'lucide-react';

interface PatientPreset {
  id: string;
  name: string;
  treatment: TreatmentCode;
  amount: number;
  label: string;
  badge: string;
}

const DEMO_PATIENTS: PatientPreset[] = [
  {
    id: 'DEMO-PATIENT-001',
    name: 'Amina Mwangi (Nairobi)',
    treatment: 'MATERNAL_CARE',
    amount: 1200,
    label: 'Maternal Care (KES 1,200)',
    badge: 'Maternal Voucher Active'
  },
  {
    id: 'DEMO-PATIENT-002',
    name: 'Baby Ethan (Nairobi)',
    treatment: 'PEDIATRIC_EMERGENCY',
    amount: 2500,
    label: 'Pediatric Care (KES 2,500)',
    badge: 'Child Care Active'
  },
  {
    id: 'DEMO-PATIENT-003',
    name: 'Grace Atieno (Kisumu Resident)',
    treatment: 'MALARIA_LAB',
    amount: 600,
    label: 'Malaria Lab (KES 600)',
    badge: 'Regional Boundary Check'
  },
  {
    id: 'DEMO-PATIENT-999',
    name: 'Expired/Unregistered ID',
    treatment: 'MATERNAL_CARE',
    amount: 1200,
    label: 'Inactive Voucher Test',
    badge: 'Ineligible Test'
  }
];

export const ClinicPortal: React.FC = () => {
  const { currentUser, isOnline, refreshPendingSync } = useAuth();

  // Form State
  const [patientRef, setPatientRef] = useState<string>('DEMO-PATIENT-001');
  const [selectedProgramId, setSelectedProgramId] = useState<string>('30000000-0000-4000-8000-000000000001');
  const [treatmentCode, setTreatmentCode] = useState<TreatmentCode>('MATERNAL_CARE');
  const [amount, setAmount] = useState<number>(1200);
  const [notes, setNotes] = useState<string>('Comprehensive prenatal consultation, iron supplementation & maternal health counseling.');
  const [idempotencyKey, setIdempotencyKey] = useState<string>(() => crypto.randomUUID());
  
  // Programs & Clinic Dashboard
  const [programs, setPrograms] = useState<FundingProgram[]>([]);
  const [recentEncounters, setRecentEncounters] = useState<EncounterDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  // Consent Modal State
  const [activeConsentEncounterId, setActiveConsentEncounterId] = useState<string | null>(null);
  const [otpInput, setOtpInput] = useState<string>('123456');
  const [verifyingConsent, setVerifyingConsent] = useState<boolean>(false);
  const [otpCountdown, setOtpCountdown] = useState<number>(300);
  const [settlementResult, setSettlementResult] = useState<any | null>(null);

  // Offline Queue Modal
  const [showOfflineModal, setShowOfflineModal] = useState<boolean>(false);
  const [offlineItems, setOfflineItems] = useState<OfflineQueueItem[]>([]);
  const [syncingAll, setSyncingAll] = useState<boolean>(false);

  // Refresh programs and dashboard on mount or clinic switch
  const loadClinicData = async () => {
    try {
      setLoading(true);
      const [progs, clinicDash] = await Promise.allSettled([
        api.listPrograms(),
        api.getClinicDashboard(currentUser.organization_id)
      ]);

      if (progs.status === 'fulfilled' && progs.value) {
        setPrograms(progs.value);
        if (progs.value.length > 0 && !selectedProgramId) {
          setSelectedProgramId(progs.value[0].id);
        }
      }

      if (clinicDash.status === 'fulfilled' && clinicDash.value) {
        setRecentEncounters(clinicDash.value.recent_encounters || []);
      }
    } catch (err: any) {
      console.warn('Could not load some clinic data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClinicData();
  }, [currentUser.organization_id]);

  // Load offline items
  const loadOfflineItems = async () => {
    const items = await offlineQueue.getAll();
    setOfflineItems(items);
  };

  useEffect(() => {
    loadOfflineItems();
  }, []);

  // OTP Timer countdown
  useEffect(() => {
    let timer: any;
    if (activeConsentEncounterId && otpCountdown > 0) {
      timer = setInterval(() => {
        setOtpCountdown((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [activeConsentEncounterId, otpCountdown]);

  const handlePatientSelect = (p: PatientPreset) => {
    setPatientRef(p.id);
    setTreatmentCode(p.treatment);
    setAmount(p.amount);
    if (p.treatment === 'MATERNAL_CARE') {
      setNotes('Routine second-trimester prenatal assessment & vitamin micro-nutrient kit.');
    } else if (p.treatment === 'PEDIATRIC_EMERGENCY') {
      setNotes('Pediatric emergency rehydration & fever mitigation.');
    } else if (p.treatment === 'MALARIA_LAB') {
      setNotes('Rapid Diagnostic Test (RDT) for Plasmodium falciparum & microscopy.');
    }
  };

  const regenerateIdempotencyKey = () => {
    setIdempotencyKey(crypto.randomUUID());
  };

  // Submit Encounter Claim
  const handleSubmitClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    setSubmitting(true);

    const payload = {
      program_id: selectedProgramId,
      patient_ref: patientRef,
      device_id: currentUser.device_id || '50000000-0000-4000-8000-000000000001',
      device_fingerprint: currentUser.device_fingerprint || 'DEMO-DEVICE-FINGERPRINT-001',
      treatment_code: treatmentCode,
      description: notes,
      amount: Number(amount),
      currency: 'KES' as const,
      occurred_at: new Date().toISOString(),
      idempotency_key: idempotencyKey,
      offline_created: !isOnline,
    };

    // If offline, store immediately in IndexedDB
    if (!isOnline) {
      try {
        await offlineQueue.enqueue(payload);
        await refreshPendingSync();
        await loadOfflineItems();
        setFeedback({
          type: 'info',
          message: `Device is Offline. Claim stored securely in IndexedDB Vault (Key: ${idempotencyKey.slice(0, 8)}...). It will automatically sync once network connectivity returns.`,
        });
        regenerateIdempotencyKey();
      } catch (err: any) {
        setFeedback({ type: 'error', message: `Failed to queue offline claim: ${err.message}` });
      } finally {
        setSubmitting(false);
      }
      return;
    }

    // If online, send to backend
    try {
      const res = await api.submitEncounter(payload);
      if (res.consent_required) {
        setActiveConsentEncounterId(res.encounter_id);
        setOtpCountdown(300);
        setSettlementResult(null);
        setFeedback({
          type: 'info',
          message: `Encounter registered (${res.encounter_id.slice(0, 8)}...). Patient SMS consent verification required.`,
        });
      } else {
        setFeedback({
          type: 'success',
          message: `Encounter successfully processed! Status: ${res.status}. Message: ${res.message}`,
        });
        loadClinicData();
        regenerateIdempotencyKey();
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Encounter submission failed.' });
    } finally {
      setSubmitting(false);
    }
  };

  // Confirm Consent with OTP
  const handleConfirmConsent = async () => {
    if (!activeConsentEncounterId) return;
    setVerifyingConsent(true);
    setFeedback(null);

    try {
      const result = await api.confirmConsent(activeConsentEncounterId, otpInput);
      setSettlementResult(result);
      setFeedback({
        type: 'success',
        message: 'Zero-Trust Verification Complete! Patient consent verified, subsidy authorized, and M-Pesa B2C payout simulated.',
      });
      loadClinicData();
      regenerateIdempotencyKey();
    } catch (err: any) {
      setFeedback({ type: 'error', message: `OTP Verification failed: ${err.message}` });
    } finally {
      setVerifyingConsent(false);
    }
  };

  // Sync all queued items from IndexedDB
  const handleSyncAll = async () => {
    setSyncingAll(true);
    let successCount = 0;
    let failCount = 0;

    const items = await offlineQueue.getAll();
    for (const item of items) {
      if (item.status === 'synced') continue;
      try {
        await offlineQueue.updateStatus(item.id, 'syncing');
        const res = await api.submitEncounter(item.payload);
        if (res.consent_required) {
          // In offline replay, auto-verify with default demo OTP for demonstration
          try {
            await api.confirmConsent(res.encounter_id, '123456');
          } catch {
            // ignore if consent already verified or rejected
          }
        }
        await offlineQueue.updateStatus(item.id, 'synced');
        successCount++;
      } catch (err: any) {
        await offlineQueue.updateStatus(item.id, 'failed', err.message);
        failCount++;
      }
    }

    await refreshPendingSync();
    await loadOfflineItems();
    await loadClinicData();
    setSyncingAll(false);
    setFeedback({
      type: successCount > 0 ? 'success' : 'error',
      message: `Offline synchronization completed: ${successCount} claims synced, ${failCount} errors.`,
    });
  };

  // Quick total settled calculation
  const totalSettledAmount = recentEncounters
    .filter((e) => e.status === 'settled')
    .reduce((sum, e) => sum + Number(e.amount), 0);

  return (
    <div className="space-y-6">
      {/* Clinic Header Info Card */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-blue-50 text-[#0A3D91] rounded-xl border border-blue-100">
            <Activity className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900">{currentUser.organization_name}</h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                Verified Clinic
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 mt-1">
              <span>Facility Code: <strong className="text-slate-700">{currentUser.facility_code || 'KE-DEMO-NAI-001'}</strong></span>
              <span>County: <strong className="text-slate-700">{currentUser.county || 'Nairobi'}</strong></span>
              <span>Logged In: <strong className="text-slate-700">{currentUser.name}</strong></span>
            </div>
          </div>
        </div>

        {/* Device Registration Badge */}
        <div className="flex items-center space-x-3 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-lg text-xs">
          <Smartphone className="w-5 h-5 text-blue-600" />
          <div>
            <div className="flex items-center space-x-1.5 font-medium text-slate-800">
              <span>{currentUser.device_name || 'Mwangaza Demo Tablet'}</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" title="Device Active"></span>
            </div>
            <p className="font-mono text-slate-400 text-[11px] truncate max-w-[180px]">
              {currentUser.device_fingerprint || 'DEMO-DEVICE-FINGERPRINT-001'}
            </p>
          </div>
        </div>
      </div>

      {/* Alert / Feedback message */}
      {feedback && (
        <div
          className={`p-4 rounded-xl text-sm flex items-start space-x-3 border ${
            feedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
              : feedback.type === 'error'
              ? 'bg-rose-50 text-rose-900 border-rose-200'
              : 'bg-blue-50 text-blue-900 border-blue-200'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          ) : feedback.type === 'error' ? (
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          )}
          <div className="flex-1">
            <p className="font-medium">{feedback.message}</p>
          </div>
          <button onClick={() => setFeedback(null)} className="text-slate-400 hover:text-slate-600 text-xs font-semibold">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Left Claim Submission, Right Settlement Wallet */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Check-In & Claim Form */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Quick Patient Voucher Presets */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-semibold text-slate-900 flex items-center space-x-1.5">
                <User className="w-4 h-4 text-blue-600" />
                <span>Demo Patient Vouchers (Click to Quick-Fill)</span>
              </label>
              <span className="text-xs text-slate-400 font-mono">HMAC Pseudonymized</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {DEMO_PATIENTS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handlePatientSelect(p)}
                  className={`text-left p-3 rounded-lg border text-xs transition-all ${
                    patientRef === p.id
                      ? 'border-blue-600 bg-blue-50/70 shadow-sm ring-1 ring-blue-600'
                      : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100/70'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">{p.name}</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-white border border-slate-200 text-slate-600">
                      {p.badge}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-500 mt-1 font-mono">
                    <span>{p.id}</span>
                    <span className="font-semibold text-blue-700">KES {p.amount.toLocaleString()}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Encounter Submission Form */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Care Encounter & Subsidy Routing</h2>
                <p className="text-xs text-slate-500">
                  Zero out-of-pocket patient fee. Instant institutional settlement.
                </p>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                Patient Copay: KES 0
              </span>
            </div>

            <form onSubmit={handleSubmitClaim} className="space-y-4">
              {/* Program & Treatment Code */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Institutional Funding Program
                  </label>
                  <select
                    value={selectedProgramId}
                    onChange={(e) => setSelectedProgramId(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
                  >
                    {programs.map((prog) => (
                      <option key={prog.id} value={prog.id}>
                        {prog.program_name} ({prog.currency} {Number(prog.allocated_amount).toLocaleString()})
                      </option>
                    ))}
                    {programs.length === 0 && (
                      <option value="30000000-0000-4000-8000-000000000001">
                        AfyaMama Maternal Health Subsidy (KES 5,000,000)
                      </option>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Treatment Code
                  </label>
                  <select
                    value={treatmentCode}
                    onChange={(e) => {
                      const code = e.target.value as TreatmentCode;
                      setTreatmentCode(code);
                      if (code === 'MATERNAL_CARE') setAmount(1200);
                      else if (code === 'PEDIATRIC_EMERGENCY') setAmount(2500);
                      else if (code === 'MALARIA_LAB') setAmount(600);
                    }}
                    className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
                  >
                    <option value="MATERNAL_CARE">MATERNAL_CARE (Standard: KES 1,200)</option>
                    <option value="PEDIATRIC_EMERGENCY">PEDIATRIC_EMERGENCY (Standard: KES 2,500)</option>
                    <option value="MALARIA_LAB">MALARIA_LAB (Standard: KES 600)</option>
                  </select>
                </div>
              </div>

              {/* Patient Identifier & Amount */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Patient Reference / National ID Hash
                  </label>
                  <input
                    type="text"
                    value={patientRef}
                    onChange={(e) => setPatientRef(e.target.value)}
                    placeholder="e.g. DEMO-PATIENT-001"
                    required
                    className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 font-mono focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Claim Amount (KES)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs font-semibold text-slate-400">KES</span>
                    <input
                      type="number"
                      step="50"
                      value={amount}
                      onChange={(e) => setAmount(Number(e.target.value))}
                      required
                      className="w-full text-xs rounded-lg border border-slate-300 pl-11 pr-3 py-2 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                </div>
              </div>

              {/* Clinical Notes */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Encounter Clinical Summary / Treatment Details
                </label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>

              {/* Idempotency Key & Offline Status */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200 gap-2">
                <div className="flex items-center space-x-2 font-mono">
                  <KeyRound className="w-3.5 h-3.5 text-slate-400" />
                  <span>Idempotency Key: {idempotencyKey.slice(0, 16)}...</span>
                  <button
                    type="button"
                    onClick={regenerateIdempotencyKey}
                    className="text-blue-600 hover:text-blue-800 font-sans underline"
                  >
                    Refresh
                  </button>
                </div>
                <div>
                  <span className={`font-semibold ${isOnline ? 'text-emerald-600' : 'text-amber-600'}`}>
                    {isOnline ? '• Real-Time Gateway Active' : '• Offline Vault Ready'}
                  </span>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={submitting}
                  className={`w-full py-3 px-4 rounded-xl font-semibold text-white shadow-sm flex items-center justify-center space-x-2 transition-all ${
                    isOnline
                      ? 'bg-[#0A3D91] hover:bg-blue-900 active:scale-[0.99]'
                      : 'bg-amber-600 hover:bg-amber-700'
                  } ${submitting ? 'opacity-70 cursor-not-allowed' : ''}`}
                >
                  {submitting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Processing Zero-Trust Checks...</span>
                    </>
                  ) : isOnline ? (
                    <>
                      <Send className="w-4 h-4" />
                      <span>Authorize Claim & Verify Consent (KES 0 Copay)</span>
                    </>
                  ) : (
                    <>
                      <Database className="w-4 h-4" />
                      <span>Queue Claim in Offline Vault (IndexedDB)</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right 1 Col: Clinic Wallet & Recent Transactions */}
        <div className="space-y-6">
          
          {/* M-Pesa Settlement Wallet Card */}
          <div className="bg-gradient-to-br from-slate-900 to-blue-950 text-white rounded-xl shadow-md p-5 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Wallet className="w-5 h-5 text-emerald-400" />
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Clinic Settlement Wallet
                </span>
              </div>
              <span className="text-[11px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-mono">
                M-PESA B2C
              </span>
            </div>

            <div className="mb-4">
              <p className="text-xs text-slate-400">Total Settled (Demo Volume)</p>
              <p className="text-2xl font-bold font-mono text-emerald-400">
                KES {(totalSettledAmount || 14800).toLocaleString()}.00
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-800/80 text-xs">
              <div>
                <p className="text-slate-400 text-[10px]">Settlement Channel</p>
                <p className="font-semibold text-slate-200">Daraja B2C Paybill</p>
              </div>
              <div>
                <p className="text-slate-400 text-[10px]">Shortcode</p>
                <p className="font-mono text-slate-200">600123</p>
              </div>
            </div>
          </div>

          {/* Offline Queue Quick Peek */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Database className="w-4 h-4 text-amber-500" />
                <h3 className="text-xs font-bold text-slate-800">IndexedDB Offline Vault</h3>
              </div>
              <button
                onClick={() => {
                  loadOfflineItems();
                  setShowOfflineModal(true);
                }}
                className="text-xs text-blue-600 hover:text-blue-800 font-semibold"
              >
                View ({offlineItems.length})
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-3">
              Encounters captured during power/network outages are persisted locally and synchronized securely.
            </p>
            {offlineItems.length > 0 && (
              <button
                onClick={handleSyncAll}
                disabled={syncingAll || !isOnline}
                className="w-full py-1.5 px-3 rounded-lg text-xs font-semibold bg-amber-500/10 text-amber-800 border border-amber-300 hover:bg-amber-500/20 flex items-center justify-center space-x-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncingAll ? 'animate-spin' : ''}`} />
                <span>{syncingAll ? 'Syncing...' : `Sync ${offlineItems.length} Queued Claims Now`}</span>
              </button>
            )}
          </div>

          {/* Recent Claims Feed */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-slate-800">Recent Clinic Claims</h3>
              <button onClick={loadClinicData} disabled={loading} className="text-slate-400 hover:text-slate-600">
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>

            <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
              {recentEncounters.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-400">
                  No recent claims recorded. Submit one above.
                </div>
              ) : (
                recentEncounters.map((enc) => (
                  <div
                    key={enc.id}
                    className="p-2.5 rounded-lg border border-slate-100 bg-slate-50/50 text-xs hover:bg-slate-100/50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-800 truncate max-w-[130px]">
                        {enc.treatment_code}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          enc.status === 'settled'
                            ? 'bg-emerald-100 text-emerald-800'
                            : enc.status === 'pending_verification'
                            ? 'bg-blue-100 text-blue-800'
                            : enc.status === 'manual_audit'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {enc.status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-slate-500 text-[11px]">
                      <span>KES {Number(enc.amount).toLocaleString()}</span>
                      <span className="font-mono text-[10px] text-slate-400">
                        {new Date(enc.occurred_at || enc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </div>

      {/* Patient Consent Modal (Stage 2 Verification) */}
      {activeConsentEncounterId && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            
            {/* Modal Header */}
            <div className="bg-[#0A3D91] text-white p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-6 h-6 text-emerald-400" />
                  <h3 className="font-bold text-base">Stage 2: Patient Consent Verification</h3>
                </div>
                <span className="bg-blue-800/80 font-mono text-xs px-2.5 py-1 rounded-full text-blue-200">
                  {Math.floor(otpCountdown / 60)}:{(otpCountdown % 60).toString().padStart(2, '0')}
                </span>
              </div>
              <p className="text-xs text-blue-100 mt-1">
                Zero-Trust requirement: Healthcare subsidies require verified patient cryptographic consent before settlement.
              </p>
            </div>

            <div className="p-6 space-y-4">
              {/* Simulated SMS Alert Banner */}
              <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 flex items-start space-x-3">
                <Smartphone className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">📱 Mock SMS Dispatched to Patient Handset:</p>
                  <p className="font-mono mt-1 text-slate-800 bg-white/80 p-1.5 rounded border border-amber-200/60">
                    "Nena AI: Your verification code for maternal/clinical subsidy is <strong>123456</strong>. Valid for 5 min."
                  </p>
                </div>
              </div>

              {/* OTP Input Form */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Enter 6-Digit One-Time Password (OTP)
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={otpInput}
                  onChange={(e) => setOtpInput(e.target.value)}
                  placeholder="123456"
                  className="w-full text-center tracking-[0.5em] font-mono text-2xl font-bold py-3 px-4 rounded-xl border-2 border-slate-300 focus:border-blue-600 focus:outline-none"
                />
              </div>

              {/* Quick Preset Buttons */}
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setOtpInput('123456')}
                  className="flex-1 py-1.5 px-3 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-300 hover:bg-emerald-100"
                >
                  Auto-fill Valid OTP (123456)
                </button>
                <button
                  type="button"
                  onClick={() => setOtpInput('999999')}
                  className="py-1.5 px-3 text-xs font-semibold rounded-lg bg-rose-50 text-rose-700 border border-rose-300 hover:bg-rose-100"
                >
                  Test Wrong OTP
                </button>
              </div>

              {/* Settlement Result if available */}
              {settlementResult && (
                <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-900 space-y-2">
                  <div className="flex items-center space-x-2 font-bold text-emerald-800">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Four-Stage Verification Passed & Subsidy Settled!</span>
                  </div>
                  <div className="font-mono text-[11px] space-y-1 bg-white p-2.5 rounded border border-emerald-200/80">
                    <p>Status: <span className="font-bold text-emerald-700">{settlementResult.status}</span></p>
                    <p>Encounter: {settlementResult.encounter_id?.slice(0, 12)}...</p>
                    {settlementResult.ledger_entry_id && (
                      <p>Ledger Event: {settlementResult.ledger_entry_id?.slice(0, 12)}...</p>
                    )}
                    {settlementResult.payout?.provider_transaction_id && (
                      <p className="text-blue-700 font-bold">
                        M-Pesa Receipt: {settlementResult.payout.provider_transaction_id}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setActiveConsentEncounterId(null);
                    setSettlementResult(null);
                  }}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
                >
                  Close
                </button>
                
                {!settlementResult && (
                  <button
                    type="button"
                    onClick={handleConfirmConsent}
                    disabled={verifyingConsent || !otpInput}
                    className="px-5 py-2.5 text-xs font-bold rounded-xl text-white bg-emerald-600 hover:bg-emerald-700 flex items-center space-x-2 shadow-sm"
                  >
                    {verifyingConsent ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Verifying Ledger Chaining...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Confirm Consent & Authorize</span>
                      </>
                    )}
                  </button>
                )}
              </div>

            </div>

          </div>
        </div>
      )}

      {/* Offline Vault Modal */}
      {showOfflineModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-base">IndexedDB Offline Claims Vault</h3>
              </div>
              <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full font-mono">
                {offlineItems.length} records
              </span>
            </div>

            <div className="p-5 max-h-[400px] overflow-y-auto space-y-3">
              {offlineItems.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-xs">
                  Offline vault is empty. All claims have been synced to the primary ledger.
                </div>
              ) : (
                offlineItems.map((item) => (
                  <div key={item.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-800">{item.payload.treatment_code}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          item.status === 'synced' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                      <p className="font-mono text-slate-500 text-[11px] mt-0.5">
                        Patient: {item.payload.patient_ref} • KES {Number(item.payload.amount).toLocaleString()}
                      </p>
                      {item.error && <p className="text-rose-600 text-[10px] mt-1">{item.error}</p>}
                    </div>
                    <button
                      onClick={async () => {
                        await offlineQueue.remove(item.id);
                        await loadOfflineItems();
                        await refreshPendingSync();
                      }}
                      className="text-slate-400 hover:text-rose-600 text-xs font-semibold"
                    >
                      Delete
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
              <button
                onClick={async () => {
                  await offlineQueue.clear();
                  await loadOfflineItems();
                  await refreshPendingSync();
                }}
                className="text-xs text-rose-600 hover:text-rose-800 font-semibold"
              >
                Clear All
              </button>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowOfflineModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
                >
                  Close
                </button>
                {offlineItems.length > 0 && (
                  <button
                    onClick={handleSyncAll}
                    disabled={syncingAll || !isOnline}
                    className="px-4 py-2 text-xs font-bold rounded-xl text-white bg-blue-600 hover:bg-blue-700 flex items-center space-x-1.5"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${syncingAll ? 'animate-spin' : ''}`} />
                    <span>Sync Now</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
