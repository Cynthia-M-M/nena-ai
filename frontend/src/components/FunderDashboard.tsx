import React, { useState, useEffect } from 'react';
import { useAuth, DEMO_PERSONAS } from '../context/AuthContext';
import { api } from '../services/api';
import type { FunderDashboardData, FundingProgram, LedgerEntry } from '../types';
import {
  Building2,
  TrendingUp,
  DollarSign,
  Users,
  ShieldAlert,
  Clock,
  Layers,
  Settings2,
  RefreshCw,
  Hash,
  CheckCircle2,
  AlertCircle,
  Sliders,
  X
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

const COLORS = ['#0A3D91', '#00C49A', '#F59E0B', '#EF4444', '#8B5CF6'];

export const FunderDashboard: React.FC = () => {
  const { currentUser, switchUser } = useAuth();
  const [data, setData] = useState<FunderDashboardData | null>(null);
  const [programs, setPrograms] = useState<FundingProgram[]>([]);
  const [ledgerFeed, setLedgerFeed] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Policy Rule Editor Modal State
  const [editingProgram, setEditingProgram] = useState<FundingProgram | null>(null);
  const [ruleMaxAmount, setRuleMaxAmount] = useState<number>(1500);
  const [ruleCounties, setRuleCounties] = useState<string>('Nairobi, Kisumu, Mombasa');
  const [ruleRequireOtp, setRuleRequireOtp] = useState<boolean>(true);
  const [ruleMaxDaily, setRuleMaxDaily] = useState<number>(100);
  const [savingRules, setSavingRules] = useState<boolean>(false);

  // If logged in as clinic staff, funder admin org is AfyaBridge
  const funderOrgId =
    currentUser.organization_type === 'ngo'
      ? currentUser.organization_id
      : '10000000-0000-4000-8000-000000000001';

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [dashRes, progRes, ledgerRes] = await Promise.allSettled([
        api.getFunderDashboard(funderOrgId),
        api.listPrograms(),
        api.getLedgerFeed()
      ]);

      if (dashRes.status === 'fulfilled' && dashRes.value) {
        setData(dashRes.value);
      }
      if (progRes.status === 'fulfilled' && progRes.value) {
        setPrograms(progRes.value);
      }
      if (ledgerRes.status === 'fulfilled' && ledgerRes.value) {
        setLedgerFeed(ledgerRes.value);
      }
    } catch (err: any) {
      console.warn('Dashboard fetch warning:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [funderOrgId]);

  // Open edit modal
  const handleOpenEditRules = (prog: FundingProgram) => {
    setEditingProgram(prog);
    const rules = prog.active_rules;
    if (rules) {
      setRuleMaxAmount(Number(rules.max_amount_per_visit) || 1500);
      setRuleCounties(rules.allowed_counties?.join(', ') || 'Nairobi, Kisumu');
      setRuleRequireOtp(rules.requires_patient_otp ?? true);
      setRuleMaxDaily(rules.max_daily_claims || 100);
    } else {
      setRuleMaxAmount(1500);
      setRuleCounties('Nairobi, Kisumu, Mombasa');
      setRuleRequireOtp(true);
      setRuleMaxDaily(100);
    }
  };

  // Save rules
  const handleSaveRules = async () => {
    if (!editingProgram) return;
    setSavingRules(true);
    setFeedback(null);
    try {
      const countiesArray = ruleCounties.split(',').map((c) => c.trim()).filter(Boolean);
      await api.updateProgramRules(editingProgram.id, {
        max_amount_per_visit: Number(ruleMaxAmount),
        allowed_counties: countiesArray,
        requires_patient_otp: ruleRequireOtp,
        max_daily_claims: Number(ruleMaxDaily)
      });
      setFeedback({
        type: 'success',
        message: `Policy rules updated for "${editingProgram.program_name}". New visit cap: KES ${Number(ruleMaxAmount).toLocaleString()}.`
      });
      setEditingProgram(null);
      await loadDashboardData();
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Rule update failed: ${err.message}` });
    } finally {
      setSavingRules(false);
    }
  };

  // Prepare regional chart data
  const regionalData = data?.regional_breakdown
    ? Object.entries(data.regional_breakdown).map(([county, metric]) => ({
        county,
        encounters: metric.encounters,
        amount: Number(metric.amount)
      }))
    : [
        { county: 'Nairobi', encounters: 24, amount: 28800 },
        { county: 'Kisumu', encounters: 12, amount: 14400 },
        { county: 'Mombasa', encounters: 8, amount: 9600 }
      ];

  // Capital pool breakdown for pie chart
  const capitalBreakdown = [
    { name: 'Settled Payouts', value: data?.total_settled ? Number(data.total_settled) : 1825000 },
    { name: 'Authorized Pending', value: data?.total_authorized ? Number(data.total_authorized) - Number(data?.total_settled || 0) : 17400 },
    { name: 'Remaining Capital', value: data?.remaining_capital ? Number(data.remaining_capital) : 3157600 }
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-cyan-50 text-cyan-800 rounded-xl border border-cyan-100">
            <Building2 className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900">Institutional Funder Portal</h1>
              <span className="text-xs bg-blue-50 text-blue-700 border border-blue-200 font-semibold px-2 py-0.5 rounded-full">
                AfyaBridge Foundation
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Real-time programmatic subsidy routing, impact metrics & immutable audit ledger.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {currentUser.organization_type !== 'ngo' && (
            <button
              onClick={() => {
                const funderUser = DEMO_PERSONAS.find((p) => p.role === 'funder_admin');
                if (funderUser) switchUser(funderUser);
              }}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200"
            >
              Switch to Funder Admin
            </button>
          )}
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
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
              <AlertCircle className="w-4 h-4 text-rose-600" />
            )}
            <span className="font-medium">{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="font-semibold text-slate-500">
            Dismiss
          </button>
        </div>
      )}

      {/* Top 4 KPI Capital Allocation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Allocated */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Total Capital Allocated</span>
            <DollarSign className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold font-mono text-slate-900">
            KES {(data?.total_allocated ? Number(data.total_allocated) : 5000000).toLocaleString()}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Multi-program institutional escrow</p>
        </div>

        {/* Authorized */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Subsidies Authorized</span>
            <TrendingUp className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold font-mono text-emerald-600">
            KES {(data?.total_authorized ? Number(data.total_authorized) : 1842400).toLocaleString()}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">4-Stage Zero-Trust verified</p>
        </div>

        {/* Settled */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Settled Disbursed</span>
            <CheckCircle2 className="w-4 h-4 text-cyan-600" />
          </div>
          <p className="text-2xl font-bold font-mono text-cyan-700">
            KES {(data?.total_settled ? Number(data.total_settled) : 1825000).toLocaleString()}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Daraja M-Pesa B2C confirmed</p>
        </div>

        {/* Remaining Capital */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Remaining Capital Pool</span>
            <Layers className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-bold font-mono text-amber-600">
            KES {(data?.remaining_capital ? Number(data.remaining_capital) : 3157600).toLocaleString()}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Available for routing</p>
        </div>
      </div>

      {/* Impact & Performance Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 flex items-center space-x-3">
          <div className="p-2.5 bg-blue-100 text-blue-700 rounded-lg">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Households Served</p>
            <p className="text-lg font-bold text-slate-800">{data?.households_served || 98}</p>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 flex items-center space-x-3">
          <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Verified Care Visits</p>
            <p className="text-lg font-bold text-slate-800">{data?.total_encounters || 142}</p>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 flex items-center space-x-3">
          <div className="p-2.5 bg-purple-100 text-purple-700 rounded-lg">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Avg Settlement Latency</p>
            <p className="text-lg font-bold text-slate-800">
              {data?.average_settlement_latency_ms || 342} ms
            </p>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 flex items-center space-x-3">
          <div className="p-2.5 bg-rose-100 text-rose-700 rounded-lg">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Flagged For Audit</p>
            <p className="text-lg font-bold text-slate-800">{data?.suspicious_claims_count || 3}</p>
          </div>
        </div>
      </div>

      {/* Visual Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Regional Breakdown Bar Chart (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Regional Subsidy Disbursement (KES)</h3>
              <p className="text-xs text-slate-400">Claims routed across participating primary care counties</p>
            </div>
            <span className="text-xs font-semibold px-2 py-1 bg-slate-100 rounded text-slate-600">
              Total: KES {regionalData.reduce((acc, curr) => acc + curr.amount, 0).toLocaleString()}
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regionalData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <XAxis dataKey="county" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(value: any) => [`KES ${Number(value).toLocaleString()}`, 'Disbursed']}
                />
                <Bar dataKey="amount" fill="#0A3D91" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Capital Pool Donut Chart (1 col) */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Capital Pool Utilization</h3>
            <p className="text-xs text-slate-400">Escrow funds allocated vs. settled</p>
          </div>

          <div className="h-56 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={capitalBreakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {capitalBreakdown.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: any) => [`KES ${Number(value).toLocaleString()}`, '']} />
                <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="text-[11px] text-slate-400 text-center pt-2 border-t border-slate-100">
            Automated threshold alert when pool falls below 15%
          </div>
        </div>

      </div>

      {/* Funding Programs & Policy Rules Section */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Active Funding Programs & Policy Rules</h3>
            <p className="text-xs text-slate-500">
              Zero-Trust Stage 3 policies evaluated automatically on every incoming clinic claim.
            </p>
          </div>
          <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full font-mono font-medium">
            {programs.length} Active Programs
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {programs.map((prog) => {
            const rules = prog.active_rules;
            return (
              <div
                key={prog.id}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/40 hover:bg-slate-50 transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-bold text-slate-900 text-sm">{prog.program_name}</h4>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      Active
                    </span>
                  </div>

                  <p className="text-xs text-slate-500 mb-3">{prog.description || 'Subsidy routing program'}</p>

                  <div className="space-y-1.5 text-xs text-slate-600 mb-4">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Allocated Pool:</span>
                      <strong className="text-slate-800 font-mono">
                        KES {Number(prog.allocated_amount).toLocaleString()}
                      </strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Max Per Visit:</span>
                      <strong className="text-blue-700 font-mono">
                        KES {rules ? Number(rules.max_amount_per_visit).toLocaleString() : '1,500'}
                      </strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Allowed Counties:</span>
                      <span className="text-slate-700 font-medium truncate max-w-[180px]">
                        {rules?.allowed_counties?.join(', ') || 'Nairobi, Kisumu'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Patient OTP Required:</span>
                      <span className="text-emerald-700 font-bold">
                        {rules?.requires_patient_otp !== false ? 'YES (Stage 2 Enforced)' : 'NO'}
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleOpenEditRules(prog)}
                  className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-white border border-slate-300 hover:border-blue-600 text-slate-700 hover:text-blue-700 flex items-center justify-center space-x-1.5 transition-all shadow-2xs"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span>Configure Policy Rules</span>
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Immutable Financial Event Ledger Feed */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
          <div className="flex items-center space-x-2">
            <Hash className="w-5 h-5 text-blue-700" />
            <div>
              <h3 className="text-base font-bold text-slate-900">Live Immutable Financial Ledger</h3>
              <p className="text-xs text-slate-500">Append-only cryptographic SHA-256 event stream</p>
            </div>
          </div>
          <span className="text-xs font-mono text-emerald-600 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
            ● Append-Only Chaining
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Event Type</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">Prev Hash</th>
                <th className="py-2.5 px-3">Transaction Hash</th>
                <th className="py-2.5 px-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {ledgerFeed.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400 font-sans">
                    No ledger transactions recorded yet.
                  </td>
                </tr>
              ) : (
                ledgerFeed.map((entry) => (
                  <tr key={entry.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-sans">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          entry.event_type === 'subsidy_authorized'
                            ? 'bg-blue-100 text-blue-800'
                            : entry.event_type === 'settlement_confirmed'
                            ? 'bg-emerald-100 text-emerald-800'
                            : entry.event_type === 'reversal'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {entry.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-bold text-slate-900 font-mono">
                      KES {Number(entry.amount).toLocaleString()}.00
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 truncate max-w-[120px]" title={entry.prev_hash}>
                      {entry.prev_hash.slice(0, 12)}...
                    </td>
                    <td className="py-2.5 px-3 text-blue-700 font-bold truncate max-w-[140px]" title={entry.tx_hash}>
                      {entry.tx_hash.slice(0, 16)}...
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 font-sans text-[11px]">
                      {new Date(entry.created_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                      })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Program Policy Rules Editor Modal */}
      {editingProgram && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
            <div className="bg-[#0A3D91] text-white p-5 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Settings2 className="w-5 h-5 text-cyan-400" />
                <h3 className="font-bold text-base">Edit Program Policy Rules</h3>
              </div>
              <button
                onClick={() => setEditingProgram(null)}
                className="text-blue-200 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Program Name
                </label>
                <input
                  type="text"
                  disabled
                  value={editingProgram.program_name}
                  className="w-full text-xs rounded-lg border border-slate-200 bg-slate-100 p-2 font-semibold text-slate-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Maximum Claim Amount Per Visit (KES)
                </label>
                <input
                  type="number"
                  value={ruleMaxAmount}
                  onChange={(e) => setRuleMaxAmount(Number(e.target.value))}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2 font-mono font-bold text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Claims exceeding this threshold are blocked at Stage 3 with EXCESSIVE_BILLING.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Allowed Counties (comma separated)
                </label>
                <input
                  type="text"
                  value={ruleCounties}
                  onChange={(e) => setRuleCounties(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Enforces geographic funding boundaries (e.g. Nairobi, Kisumu, Mombasa).
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Max Daily Claims Allowed Per Clinic
                </label>
                <input
                  type="number"
                  value={ruleMaxDaily}
                  onChange={(e) => setRuleMaxDaily(Number(e.target.value))}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div className="flex items-center space-x-3 pt-2">
                <input
                  type="checkbox"
                  id="requireOtp"
                  checked={ruleRequireOtp}
                  onChange={(e) => setRuleRequireOtp(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                />
                <label htmlFor="requireOtp" className="text-xs font-semibold text-slate-700">
                  Enforce Mandatory Patient Consent OTP (Stage 2 Zero-Trust)
                </label>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingProgram(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveRules}
                  disabled={savingRules}
                  className="px-5 py-2 text-xs font-bold rounded-xl text-white bg-blue-700 hover:bg-blue-800 flex items-center space-x-1.5"
                >
                  {savingRules ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Updating Rules...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Save Policy Rules</span>
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
