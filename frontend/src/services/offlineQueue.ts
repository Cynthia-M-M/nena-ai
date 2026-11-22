import { openDB } from 'idb';
import type { DBSchema } from 'idb';
import type { EncounterCreate, OfflineQueueItem } from '../types';

interface NenaOfflineDB extends DBSchema {
  offline_encounters: {
    key: string;
    value: OfflineQueueItem;
    indexes: { 'by-status': string; 'by-timestamp': string };
  };
}

const DB_NAME = 'nena-offline-vault';
const DB_VERSION = 1;

async function getDB() {
  return openDB<NenaOfflineDB>(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('offline_encounters')) {
        const store = db.createObjectStore('offline_encounters', { keyPath: 'id' });
        store.createIndex('by-status', 'status');
        store.createIndex('by-timestamp', 'created_at');
      }
    },
  });
}

export const offlineQueue = {
  async enqueue(payload: EncounterCreate): Promise<OfflineQueueItem> {
    const db = await getDB();
    const item: OfflineQueueItem = {
      id: payload.idempotency_key || crypto.randomUUID(),
      payload: { ...payload, offline_created: true },
      created_at: new Date().toISOString(),
      status: 'pending',
    };
    await db.put('offline_encounters', item);
    return item;
  },

  async getAll(): Promise<OfflineQueueItem[]> {
    const db = await getDB();
    return db.getAllFromIndex('offline_encounters', 'by-timestamp');
  },

  async getPendingCount(): Promise<number> {
    const db = await getDB();
    const all = await db.getAll('offline_encounters');
    return all.filter(item => item.status === 'pending').length;
  },

  async remove(id: string): Promise<void> {
    const db = await getDB();
    await db.delete('offline_encounters', id);
  },

  async updateStatus(id: string, status: 'pending' | 'syncing' | 'synced' | 'failed', error?: string): Promise<void> {
    const db = await getDB();
    const item = await db.get('offline_encounters', id);
    if (item) {
      item.status = status;
      if (error) item.error = error;
      await db.put('offline_encounters', item);
    }
  },

  async clear(): Promise<void> {
    const db = await getDB();
    await db.clear('offline_encounters');
  }
};
