import type { ActivityContentResponse, InteractionCreate } from "../types";

const DB_NAME = "rapid-learn";
const QUEUE_STORE = "queue";
const CONTENT_STORE = "activity-content";
const DB_VERSION = 2;

type QueueRecord = { id?: number; payload: InteractionCreate; createdAt: number };
type ContentRecord = {
  activityId: string;
  conceptId: string;
  payload: ActivityContentResponse;
  cachedAt: number;
};

export async function queuedCount(): Promise<number> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const request = db.transaction(QUEUE_STORE).objectStore(QUEUE_STORE).count();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueInteraction(payload: InteractionCreate): Promise<void> {
  const db = await openDatabase();
  await transactionDone(
    db.transaction(QUEUE_STORE, "readwrite").objectStore(QUEUE_STORE).add({
      payload,
      createdAt: Date.now(),
    } satisfies QueueRecord),
  );
}

export async function flushQueue(
  send: (payload: InteractionCreate) => Promise<unknown>,
): Promise<void> {
  const db = await openDatabase();
  const items = await getAll<QueueRecord>(db, QUEUE_STORE);
  for (const item of items) {
    await send(item.payload);
    if (item.id !== undefined) {
      await transactionDone(
        db.transaction(QUEUE_STORE, "readwrite").objectStore(QUEUE_STORE).delete(item.id),
      );
    }
  }
}

export async function cacheActivityContent(payload: ActivityContentResponse): Promise<void> {
  const db = await openDatabase();
  await transactionDone(
    db.transaction(CONTENT_STORE, "readwrite").objectStore(CONTENT_STORE).put({
      activityId: payload.activity.id,
      conceptId: payload.activity.concept_id,
      payload,
      cachedAt: Date.now(),
    } satisfies ContentRecord),
  );
}

export async function cachedActivityContent(
  activityId: string,
): Promise<ActivityContentResponse | undefined> {
  const db = await openDatabase();
  const item = await getOne<ContentRecord>(db, CONTENT_STORE, activityId);
  return item?.payload;
}

export async function cachedContentMetadata(): Promise<{
  activityIds: string[];
  conceptIds: string[];
}> {
  const db = await openDatabase();
  const items = await getAll<ContentRecord>(db, CONTENT_STORE);
  return {
    activityIds: items.map((item) => item.activityId),
    conceptIds: [...new Set(items.map((item) => item.conceptId))],
  };
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        db.createObjectStore(QUEUE_STORE, { keyPath: "id", autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(CONTENT_STORE)) {
        db.createObjectStore(CONTENT_STORE, { keyPath: "activityId" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function transactionDone(request: IDBRequest): Promise<void> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

function getAll<T>(db: IDBDatabase, store: string): Promise<T[]> {
  return new Promise((resolve, reject) => {
    const request = db.transaction(store).objectStore(store).getAll();
    request.onsuccess = () => resolve(request.result as T[]);
    request.onerror = () => reject(request.error);
  });
}

function getOne<T>(db: IDBDatabase, store: string, key: IDBValidKey): Promise<T | undefined> {
  return new Promise((resolve, reject) => {
    const request = db.transaction(store).objectStore(store).get(key);
    request.onsuccess = () => resolve(request.result as T | undefined);
    request.onerror = () => reject(request.error);
  });
}
