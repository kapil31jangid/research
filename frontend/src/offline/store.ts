import type { ActivityContentResponse, CurriculumContext, InteractionCreate } from "../types";

const DB_NAME = "rapid-learn";
const QUEUE_STORE = "queue";
const CONTENT_STORE = "activity-content-v3";
const DB_VERSION = 3;

type QueueRecord = { id?: number; payload: InteractionCreate; createdAt: number };
type ContentRecord = {
  cacheKey: string;
  activityId: string;
  conceptId: string;
  curriculumKey: string;
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
  const context = payload.activity.curriculum_context;
  const curriculumKey = curriculumCacheKey(context);
  await transactionDone(
    db.transaction(CONTENT_STORE, "readwrite").objectStore(CONTENT_STORE).put({
      cacheKey: `${curriculumKey}:${payload.activity.id}`,
      activityId: payload.activity.id,
      conceptId: payload.activity.concept_id,
      curriculumKey,
      payload,
      cachedAt: Date.now(),
    } satisfies ContentRecord),
  );
}

export async function cachedActivityContent(
  activityId: string,
  context?: CurriculumContext,
): Promise<ActivityContentResponse | undefined> {
  const db = await openDatabase();
  if (context) {
    const key = `${curriculumCacheKey(context)}:${activityId}`;
    return (await getOne<ContentRecord>(db, CONTENT_STORE, key))?.payload;
  }
  const items = await getAll<ContentRecord>(db, CONTENT_STORE);
  return items.find((item) => item.activityId === activityId)?.payload;
}

export async function cachedContentMetadata(): Promise<{
  activityIds: string[];
  conceptIds: string[];
  curriculumKeys: string[];
}> {
  const db = await openDatabase();
  const items = await getAll<ContentRecord>(db, CONTENT_STORE);
  return {
    activityIds: [...new Set(items.map((item) => item.activityId))],
    conceptIds: [...new Set(items.map((item) => item.conceptId))],
    curriculumKeys: [...new Set(items.map((item) => item.curriculumKey))],
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
        db.createObjectStore(CONTENT_STORE, { keyPath: "cacheKey" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export function curriculumCacheKey(context: CurriculumContext): string {
  return [context.board_id, `class-${context.class_level}`, context.subject_id].join(":");
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
