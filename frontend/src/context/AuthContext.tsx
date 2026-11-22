import React, { createContext, useContext, useState, useEffect } from 'react';
import type { DemoUser } from '../types';
import { api } from '../services/api';
import { offlineQueue } from '../services/offlineQueue';

export const DEMO_PERSONAS: DemoUser[] = [
  {
    user_id: '00000000-0000-0000-0000-000000000001',
    name: 'Nurse Jane (Staff)',
    email: 'jane@mwangazaclinic.ke',
    role: 'clinic_staff',
    organization_id: '20000000-0000-4000-8000-000000000001',
    organization_name: 'Mwangaza Community Clinic',
    organization_type: 'clinic',
    facility_code: 'KE-DEMO-NAI-001',
    county: 'Nairobi',
    device_id: '50000000-0000-4000-8000-000000000001',
    device_name: 'Mwangaza Demo Tablet',
    device_fingerprint: 'DEMO-DEVICE-FINGERPRINT-001'
  },
  {
    user_id: '00000000-0000-0000-0000-000000000003',
    name: 'Alice (Clinic Admin)',
    email: 'alice@mwangazaclinic.ke',
    role: 'clinic_admin',
    organization_id: '20000000-0000-4000-8000-000000000001',
    organization_name: 'Mwangaza Community Clinic',
    organization_type: 'clinic',
    facility_code: 'KE-DEMO-NAI-001',
    county: 'Nairobi',
    device_id: '50000000-0000-4000-8000-000000000001',
    device_name: 'Mwangaza Demo Tablet',
    device_fingerprint: 'DEMO-DEVICE-FINGERPRINT-001'
  },
  {
    user_id: '00000000-0000-0000-0000-000000000006',
    name: 'Charlie (Staff - Kisumu)',
    email: 'charlie@lakeviewclinic.ke',
    role: 'clinic_staff',
    organization_id: '20000000-0000-4000-8000-000000000002',
    organization_name: 'Lakeview Family Health Centre',
    organization_type: 'clinic',
    facility_code: 'KE-DEMO-KSM-001',
    county: 'Kisumu',
    device_id: '50000000-0000-4000-8000-000000000002',
    device_name: 'Lakeview Demo Tablet',
    device_fingerprint: 'DEMO-DEVICE-FINGERPRINT-002'
  },
  {
    user_id: '00000000-0000-0000-0000-000000000002',
    name: 'John (NGO Funder Admin)',
    email: 'john@afyabridge.org',
    role: 'funder_admin',
    organization_id: '10000000-0000-4000-8000-000000000001',
    organization_name: 'AfyaBridge Foundation',
    organization_type: 'ngo'
  },
  {
    user_id: '00000000-0000-0000-0000-000000000004',
    name: 'Bob (Lead Auditor)',
    email: 'bob@auditor.ke',
    role: 'auditor',
    organization_id: '10000000-0000-4000-8000-000000000001',
    organization_name: 'AfyaBridge Foundation (Auditor)',
    organization_type: 'ngo'
  },
  {
    user_id: '00000000-0000-0000-0000-000000000005',
    name: 'Platform Root Admin',
    email: 'root@nena.health',
    role: 'platform_admin',
    organization_id: '10000000-0000-4000-8000-000000000001',
    organization_name: 'Nena AI Global Governance',
    organization_type: 'platform'
  }
];

interface AuthContextType {
  currentUser: DemoUser;
  switchUser: (user: DemoUser) => void;
  isOnline: boolean;
  toggleOfflineSimulation: () => void;
  pendingSyncCount: number;
  refreshPendingSync: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<DemoUser>(DEMO_PERSONAS[0]);
  const [isSimulatedOffline, setIsSimulatedOffline] = useState<boolean>(false);
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [pendingSyncCount, setPendingSyncCount] = useState<number>(0);

  const refreshPendingSync = async () => {
    try {
      const count = await offlineQueue.getPendingCount();
      setPendingSyncCount(count);
    } catch {
      setPendingSyncCount(0);
    }
  };

  useEffect(() => {
    api.setDemoUser(currentUser.user_id, currentUser.email);
    refreshPendingSync();
  }, [currentUser]);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const toggleOfflineSimulation = () => {
    setIsSimulatedOffline(prev => !prev);
  };

  const effectiveOnline = isOnline && !isSimulatedOffline;

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        switchUser: (user) => setCurrentUser(user),
        isOnline: effectiveOnline,
        toggleOfflineSimulation,
        pendingSyncCount,
        refreshPendingSync,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
