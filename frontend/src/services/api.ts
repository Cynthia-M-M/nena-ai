import type { EncounterCreate, EncounterResponse, ProgramRule, LedgerChainVerifyResponse } from '../types';

const BASE_URL = '/api/v1';

// Client-side HS256 mock JWT generator for seamless instant demo role-switching
function createClientDemoToken(userId: string, email: string): string {
  // In demo mode, our FastAPI backend accepts test-token-<userId> or HS256 tokens
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    sub: userId,
    id: userId,
    email: email,
    role: 'authenticated',
    aud: 'authenticated',
    exp: Math.floor(Date.now() / 1000) + 86400,
    iat: Math.floor(Date.now() / 1000)
  }));
  // Mock signature
  return `${header}.${payload}.demo_signature_client_side`;
}

export class ApiClient {
  private token: string = '';

  setToken(token: string) {
    this.token = token;
  }

  setDemoUser(userId: string, email: string) {
    this.token = createClientDemoToken(userId, email);
  }

  private getHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...extraHeaders,
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const headers = this.getHeaders(options.headers as Record<string, string>);
    
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: `HTTP error ${response.status}: ${response.statusText}` };
      }
      throw new Error(errorData.message || errorData.detail || 'API request failed');
    }

    if (response.status === 204) {
      return null as any;
    }

    return response.json();
  }

  // Health
  getHealth() {
    return this.request<{ status: string; database: string; ledger_chain_head: string }>('/health');
  }

  // Encounters
  submitEncounter(data: EncounterCreate) {
    return this.request<EncounterResponse>('/encounters', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Idempotency-Key': data.idempotency_key }
    });
  }

  confirmConsent(encounterId: string, otp: string) {
    return this.request<any>(`/encounters/${encounterId}/consent`, {
      method: 'POST',
      body: JSON.stringify({ otp }),
    });
  }

  getEncounter(encounterId: string) {
    return this.request<any>(`/encounters/${encounterId}`);
  }

  // Programs
  listPrograms() {
    return this.request<any[]>('/programs');
  }

  getProgram(programId: string) {
    return this.request<any>(`/programs/${programId}`);
  }

  updateProgramRules(programId: string, rules: Partial<ProgramRule>) {
    return this.request<any>(`/programs/${programId}/rules`, {
      method: 'PUT',
      body: JSON.stringify(rules),
    });
  }

  // Governance & Audit
  listAuditEncounters() {
    return this.request<any[]>('/audit/encounters');
  }

  getAuditTrail(encounterId: string) {
    return this.request<any>(`/audit/encounters/${encounterId}`);
  }

  submitAuditDecision(encounterId: string, decision: 'approve' | 'reject', reason: string) {
    return this.request<any>(`/audit/encounters/${encounterId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, reason }),
    });
  }

  // Ledger
  getLedgerFeed() {
    return this.request<any[]>('/ledger');
  }

  verifyLedgerChain() {
    return this.request<LedgerChainVerifyResponse>('/ledger/verify', {
      method: 'POST',
    });
  }

  reverseLedgerEntry(ledgerId: string, reason: string) {
    return this.request<any>(`/ledger/${ledgerId}/reverse`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  // Dashboards
  getFunderDashboard(funderOrgId: string) {
    return this.request<any>(`/dashboard/funder/${funderOrgId}`);
  }

  getClinicDashboard(clinicOrgId: string) {
    return this.request<any>(`/dashboard/clinic/${clinicOrgId}`);
  }

  // Clinics & Devices
  listClinicDevices(clinicOrgId: string) {
    return this.request<any[]>(`/clinics/${clinicOrgId}/devices`);
  }

  registerDevice(clinicOrgId: string, deviceName: string, deviceFingerprint: string) {
    return this.request<any>(`/clinics/${clinicOrgId}/devices`, {
      method: 'POST',
      body: JSON.stringify({ device_name: deviceName, device_fingerprint: deviceFingerprint }),
    });
  }

  revokeDevice(clinicOrgId: string, deviceId: string) {
    return this.request<any>(`/clinics/${clinicOrgId}/devices/${deviceId}`, {
      method: 'DELETE',
    });
  }
}

export const api = new ApiClient();
