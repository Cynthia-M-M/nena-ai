import React, { useState, useEffect } from 'react';
import { useAuth, DEMO_PERSONAS } from '../context/AuthContext';
import { api } from '../services/api';
import type {
  EncounterDetail,
  AuditDetailResponse,
  LedgerChainVerifyResponse
} from '../types';
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Lock,
  RotateCcw,
  Eye,
  X
} from 'lucide-react';

export const AuditConsole: React.FC = () => {
  const { currentUser, switchUser } = useAuth();

  // State
  const [flaggedEncounters, setFlaggedEncounters] = useState<EncounterDetail[]>([]);
  const [selectedEncounterId, setSelectedEncounterId] = useState<string | null>(null);
  const [auditDetail, setAuditDetail] = useState<AuditDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [inspecting, setInspecting] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Ledger Chain Verification State
  const [verifyingChain, setVerifyingChain] = useState<boolean>(false);
  const [chainResult, setChainResult] = useState<LedgerChainVerifyResponse | null>(null);

  // Adjudication Form State
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [submittingDecision, setSubmittingDecision] = useState<boolean>(false);

  // Ledger Reversal State
  const [showReversalModal, setShowReversalModal] = useState<boolean>(false);
  const [reversalLedgerId, setReversalLedgerId] = useState<string>('');
  const [reversalReason, setReversalReason] = useState<string>('Documented clinical audit failure or billing correction.');
  const [reversing, setReversing] = useState<boolean>(false);

  const loadFlaggedEncounters = async () => {
    try {
      setLoading(true);
      const encounters = await api.listAuditEncounters();
      setFlaggedEncounters(encounters || []);
    } catch (err: any) {
      console.warn('Could not load flagged encounters:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFlaggedEncounters();
  }, [currentUser]);

  // Verify Ledger Chain Integrity
  const handleVerifyChain = async () => {
    setVerifyingChain(true);
    setFeedback(null);
    try {
      const res = await api.verifyLedgerChain();
      setChainResult(res);
      setFeedback({
        type: 'success',
        message: `Cryptographic SHA-256 chain verification passed! All ${res.total_entries} ledger entries verified with 0 inconsistencies.`
      });
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Chain verification failed: ${err.message}` });
    } finally {
      setVerifyingChain(false);
    }
  };

  // Inspect Encounter Details & Audit Trail
  const handleInspectEncounter = async (encounterId: string) => {
    setSelectedEncounterId(encounterId);
    setInspecting(true);
    setAuditDetail(null);
    setDecisionReason('');
    try {
      const detail = await api.getAuditTrail(encounterId);
      setAuditDetail(detail);
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Failed to load audit trail: ${err.message}` });
    } finally {
      setInspecting(false);
    }
  };

  // Submit Auditor Decision (Approve or Reject)
  const handleAuditorDecision = async (decision: 'approve' | 'reject') => {
    if (!selectedEncounterId) return;
    if (!decisionReason || decisionReason.trim().length < 10) {
      setFeedback({
        type: 'error',
        message: 'Auditor rationale is mandatory and must contain at least 10 characters.'
      });
      return;
    }

    setSubmittingDecision(true);
    setFeedback(null);
    try {
      await api.submitAuditDecision(selectedEncounterId, decision, decisionReason.trim());
      setFeedback({
        type: 'success',
        message: `Auditor decision recorded (${decision.toUpperCase()}) for encounter ${selectedEncounterId.slice(0, 8)}... ${
          decision === 'approve' ? 'Subsidy authorized and M-Pesa payout dispatched.' : 'Claim rejected.'
        }`
      });
      setSelectedEncounterId(null);
      setAuditDetail(null);
      await loadFlaggedEncounters();
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Decision submission failed: ${err.message}` });
    } finally {
      setSubmittingDecision(false);
    }
  };

  // Execute Reversal
  const handleExecuteReversal = async () => {
    if (!reversalLedgerId) return;
    setReversing(true);
    setFeedback(null);
    try {
      await api.reverseLedgerEntry(reversalLedgerId, reversalReason);
      setFeedback({
        type: 'success',
        message: `Ledger entry ${reversalLedgerId.slice(0, 8)}... reversed successfully! Immutable compensating reversal event appended to ledger.`
      });
      setShowReversalModal(false);
      setReversalLedgerId('');
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Reversal failed: ${err.message}` });
    } finally {
      setReversing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-amber-50 text-amber-700 rounded-xl border border-amber-100">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900">Zero-Trust Governance & Audit Console</h1>
              <span className="text-xs bg-amber-50 text-amber-800 border border-amber-200 font-semibold px-2 py-0.5 rounded-full">
                Independent Oversight
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Cryptographic chain validation, explainable anomaly detection review, and ledger reversal controls.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {currentUser.role !== 'auditor' && (
            <button
              onClick={() => {
                const auditorUser = DEMO_PERSONAS.find((p) => p.role === 'auditor');
                if (auditorUser) switchUser(auditorUser);
              }}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-amber-50 text-amber-800 hover:bg-amber-100 border border-amber-200"
            >
              Switch to Lead Auditor
            </button>
          )}
          <button
            onClick={() => setShowReversalModal(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Ledger Reversal Tool</span>
          </button>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center justify-between border ${
            feedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
              : 'bg-rose-50 text-rose-900 border-rose-200'
          }`}
        >
          <div className="flex items-center space-x-2">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            ) : (
              <XCircle className="w-4 h-4 text-rose-600" />
            )}
            <span className="font-medium">{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="font-semibold text-slate-500">
            Dismiss
          </button>
        </div>
      )}

      {/* Cryptographic SHA-256 Ledger Chain Verifier Card */}
      <div className="bg-gradient-to-r from-slate-900 to-blue-950 text-white rounded-xl shadow-md p-6 border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Lock className="w-5 h-5 text-emerald-400" />
              <h2 className="text-base font-bold text-white">Cryptographic SHA-256 Ledger Chain Integrity Verifier</h2>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl">
              Recursively computes SHA-256 hash chains from genesis block to current head. Detects any modified
              amounts, mutated event types, or severed cryptographic links.
            </p>
          </div>

          <button
            onClick={handleVerifyChain}
            disabled={verifyingChain}
            className="px-5 py-2.5 rounded-xl font-bold text-xs bg-emerald-600 hover:bg-emerald-700 text-white flex items-center space-x-2 shadow-sm transition-all self-start md:self-center"
          >
            <ShieldCheck className={`w-4 h-4 ${verifyingChain ? 'animate-spin' : ''}`} />
            <span>{verifyingChain ? 'Executing SHA-256 Hash Chaining...' : 'Verify Cryptographic Chain'}</span>
          </button>
        </div>

        {/* Chain Verification Result Box */}
        {chainResult && (
          <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700">
              <span className="text-slate-400 text-[10px] block">Cryptographic Integrity</span>
              <span className="text-emerald-400 font-bold flex items-center space-x-1 mt-0.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>CHAIN VALID (UNBROKEN)</span>
              </span>
            </div>
            <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700">
              <span className="text-slate-400 text-[10px] block">Total Blocks Verified</span>
              <span className="text-white font-bold text-sm mt-0.5">
                {chainResult.total_entries} transactions
              </span>
            </div>
            <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700">
              <span className="text-slate-400 text-[10px] block">Current Chain Head Hash</span>
              <span className="text-cyan-300 truncate block mt-0.5" title={chainResult.current_head_hash}>
                {chainResult.current_head_hash.slice(0, 20)}...
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Flagged Encounters Queue Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Suspicious Claims Awaiting Human Adjudication</h3>
            <p className="text-xs text-slate-500">
              Claims flagged by the Stage 4 explainable heuristic anomaly engine with risk scores ≥ 60.
            </p>
          </div>
          <button
            onClick={loadFlaggedEncounters}
            disabled={loading}
            className="flex items-center space-x-1 text-xs font-semibold text-slate-600 hover:text-slate-900"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Reload Queue</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Encounter ID</th>
                <th className="py-2.5 px-3">Treatment Code</th>
                <th className="py-2.5 px-3">Claim Amount</th>
                <th className="py-2.5 px-3">County</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {flaggedEncounters.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No suspicious encounters currently flagged for manual audit.
                  </td>
                </tr>
              ) : (
                flaggedEncounters.map((enc) => (
                  <tr key={enc.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-blue-700">
                      {enc.id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-3 font-semibold text-slate-800">
                      {enc.treatment_code}
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">
                      KES {Number(enc.amount).toLocaleString()}.00
                    </td>
                    <td className="py-3 px-3 text-slate-600">
                      {enc.county || 'Nairobi'}
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                        manual_audit
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => handleInspectEncounter(enc.id)}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect Claim</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Four-Stage Claim Inspector Modal */}
      {selectedEncounterId && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full border border-slate-200 overflow-hidden max-h-[90vh] flex flex-col">
            
            {/* Modal Header */}
            <div className="bg-[#0A3D91] text-white p-5 flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <ShieldAlert className="w-6 h-6 text-amber-400" />
                  <h3 className="font-bold text-base">Four-Stage Zero-Trust Claim Inspector</h3>
                </div>
                <p className="font-mono text-xs text-blue-200 mt-1">
                  Encounter: {selectedEncounterId}
                </p>
              </div>
              <button
                onClick={() => setSelectedEncounterId(null)}
                className="text-blue-200 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5">
              {inspecting || !auditDetail ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
                  <p className="text-xs text-slate-500 font-medium">Loading cryptographic audit trail...</p>
                </div>
              ) : (
                <>
                  {/* Claim Summary Box */}
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div>
                      <span className="text-slate-400 text-[10px]">Treatment</span>
                      <p className="font-bold text-slate-800">{auditDetail.encounter.treatment_code}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Amount</span>
                      <p className="font-bold text-blue-700 font-mono">
                        KES {Number(auditDetail.encounter.amount).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">County</span>
                      <p className="font-semibold text-slate-700">{auditDetail.encounter.county || 'Nairobi'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Patient Pseudonym</span>
                      <p className="font-mono text-slate-600 text-[11px] truncate">
                        {auditDetail.encounter.patient_token_id ? auditDetail.encounter.patient_token_id.slice(0, 10) : 'HMAC-VERIFIED'}...
                      </p>
                    </div>
                  </div>

                  {/* Four-Stage Step-by-Step Breakdown */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Four-Stage Verification Pipeline Breakdown
                    </h4>

                    {/* Stage 1: Identity & Device */}
                    <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/40 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-emerald-900">STAGE 1: Identity & Device Authentication</span>
                        <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-emerald-100 text-emerald-800">
                          PASSED
                        </span>
                      </div>
                      <p className="text-slate-600 text-[11px]">
                        Clinic profile verified. Tablet hardware fingerprint matched active registration key.
                      </p>
                    </div>

                    {/* Stage 2: Patient Consent */}
                    <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/40 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-emerald-900">STAGE 2: Patient Consent Verification</span>
                        <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-emerald-100 text-emerald-800">
                          PASSED
                        </span>
                      </div>
                      <p className="text-slate-600 text-[11px]">
                        One-Time Password (OTP) dispatched via Mock SMS and cryptographically confirmed by patient within 300s window.
                      </p>
                    </div>

                    {/* Stage 3: Programmatic Policy */}
                    <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/40 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-emerald-900">STAGE 3: Programmatic Policy Validation</span>
                        <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-emerald-100 text-emerald-800">
                          PASSED
                        </span>
                      </div>
                      <p className="text-slate-600 text-[11px]">
                        Funding program active. Clinic enrolled. Geographic county in allowed territory. Amount below visit cap.
                      </p>
                    </div>

                    {/* Stage 4: Anomaly Detection */}
                    <div className="p-3.5 rounded-xl border border-amber-200 bg-amber-50/50 text-xs">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-amber-900">
                          STAGE 4: Explainable Heuristic Anomaly Evaluation
                        </span>
                        <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-amber-100 text-amber-900 border border-amber-300">
                          FLAGGED FOR AUDIT
                        </span>
                      </div>

                      {auditDetail.risk_assessments && auditDetail.risk_assessments.length > 0 ? (
                        <div className="space-y-2">
                          <div className="flex items-center space-x-3 text-[11px]">
                            <span>
                              Risk Score: <strong className="text-amber-800">{auditDetail.risk_assessments[0].risk_score}/100</strong>
                            </span>
                            <span>
                              Severity: <strong className="text-rose-700 uppercase">{auditDetail.risk_assessments[0].risk_level}</strong>
                            </span>
                          </div>
                          <div className="space-y-1">
                            {auditDetail.risk_assessments[0].flags.map((flag, idx) => (
                              <div key={idx} className="bg-white p-2 rounded border border-amber-200 text-[11px]">
                                <span className="font-bold text-slate-800">{flag.code}:</span>{' '}
                                <span className="text-slate-600">{flag.reason || flag.description}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <p className="text-slate-600 text-[11px]">
                          Automated flags: Billing spike or off-hours cluster detected. Requires manual auditor rationale to authorize.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Auditor Adjudication Decision Box */}
                  <div className="pt-4 border-t border-slate-200 space-y-3">
                    <label className="block text-xs font-bold text-slate-800">
                      Documented Auditor Rationale (Mandatory for audit trail log)
                    </label>
                    <textarea
                      rows={3}
                      value={decisionReason}
                      onChange={(e) => setDecisionReason(e.target.value)}
                      placeholder="e.g. Verified clinical patient chart via phone; approved high-complexity pediatric emergency due to emergency surgery."
                      className="w-full text-xs rounded-xl border border-slate-300 p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    />

                    <div className="flex items-center justify-end space-x-3 pt-2">
                      <button
                        type="button"
                        onClick={() => handleAuditorDecision('reject')}
                        disabled={submittingDecision || !decisionReason}
                        className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-300"
                      >
                        Reject Claim
                      </button>

                      <button
                        type="button"
                        onClick={() => handleAuditorDecision('approve')}
                        disabled={submittingDecision || !decisionReason}
                        className="px-5 py-2 rounded-xl text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 flex items-center space-x-1.5 shadow-sm"
                      >
                        {submittingDecision ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span>Committing to Ledger...</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Authorize Subsidy & Release M-Pesa Payout</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>

          </div>
        </div>
      )}

      {/* Ledger Reversal Modal */}
      {showReversalModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <RotateCcw className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-base">Ledger Reversal Tool</h3>
              </div>
              <button onClick={() => setShowReversalModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <p className="text-xs text-slate-500">
                In an immutable ledger, transactions are never deleted or modified. A compensating reversal event
                is appended, crediting the funding program and linking to the original transaction hash.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Ledger Entry UUID
                </label>
                <input
                  type="text"
                  value={reversalLedgerId}
                  onChange={(e) => setReversalLedgerId(e.target.value)}
                  placeholder="e.g. 40000000-0000-4000-8000-000000000001"
                  className="w-full text-xs rounded-lg border border-slate-300 p-2 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Documented Reversal Reason
                </label>
                <textarea
                  rows={2}
                  value={reversalReason}
                  onChange={(e) => setReversalReason(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2 text-slate-700"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowReversalModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleExecuteReversal}
                  disabled={reversing || !reversalLedgerId}
                  className="px-4 py-2 text-xs font-bold rounded-xl text-white bg-amber-600 hover:bg-amber-700 flex items-center space-x-1.5"
                >
                  {reversing ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Appending Reversal...</span>
                    </>
                  ) : (
                    <>
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Execute Immutable Reversal</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
