/**
 * Storage Service - Abstraction layer for data persistence
 * Supports localStorage with fallback to memory storage
 */

const STORAGE_KEY = 'ptm_tasks';
const VERSION_KEY = 'ptm_version';
const LAST_SYNC_KEY = 'ptm_last_sync';
const CURRENT_VERSION = '1.0';
const MAX_TASKS = 1000;

class StorageService {
    constructor() {
        this.memoryStore = null;
        this.useMemory = false;
        this._checkStorage();
    }

    /**
     * Check if localStorage is available and working
     */
    _checkStorage() {
        try {
            const testKey = '__ptm_test__';
            localStorage.setItem(testKey, 'test');
            localStorage.removeItem(testKey);
            this.useMemory = false;
        } catch (e) {
            console.warn('localStorage không khả dụng, sử dụng memory storage:', e.message);
            this.useMemory = true;
            this.memoryStore = new Map();
        }
    }

    /**
     * Check if storage is using memory fallback
     */
    isMemoryFallback() {
        return this.useMemory;
    }

    /**
     * Get item from storage
     */
    _getItem(key) {
        if (this.useMemory) {
            return this.memoryStore.get(key) || null;
        }
        try {
            return localStorage.getItem(key);
        } catch (e) {
            console.error('Lỗi đọc localStorage:', e);
            return null;
        }
    }

    /**
     * Set item to storage
     */
    _setItem(key, value) {
        if (this.useMemory) {
            this.memoryStore.set(key, value);
            return true;
        }
        try {
            localStorage.setItem(key, value);
            return true;
        } catch (e) {
            if (e.name === 'QuotaExceededError' || e.code === 22) {
                console.error('localStorage đã đầy:', e);
                throw new Error('STORAGE_FULL');
            }
            console.error('Lỗi ghi localStorage:', e);
            throw e;
        }
    }

    /**
     * Get all tasks
     */
    getTasks() {
        try {
            const data = this._getItem(STORAGE_KEY);
            if (!data) return [];

            const tasks = JSON.parse(data);
            if (!Array.isArray(tasks)) {
                throw new Error('Invalid data format');
            }
            return tasks;
        } catch (e) {
            console.error('Dữ liệu localStorage bị corrupt, khởi tạo lại:', e);
            // Clear corrupted data
            this._clearAll();
            return [];
        }
    }

    /**
     * Save tasks to storage
     */
    saveTasks(tasks) {
        if (tasks.length > MAX_TASKS) {
            throw new Error('TASK_LIMIT_EXCEEDED');
        }

        const data = JSON.stringify(tasks);
        this._setItem(STORAGE_KEY, data);
        this._setItem(VERSION_KEY, CURRENT_VERSION);
        this._setItem(LAST_SYNC_KEY, new Date().toISOString());
    }

    /**
     * Clear all data
     */
    _clearAll() {
        if (this.useMemory) {
            this.memoryStore.clear();
        } else {
            try {
                localStorage.removeItem(STORAGE_KEY);
                localStorage.removeItem(VERSION_KEY);
                localStorage.removeItem(LAST_SYNC_KEY);
            } catch (e) {
                console.error('Lỗi xóa localStorage:', e);
            }
        }
    }

    /**
     * Check if task limit is reached
     */
    isLimitReached() {
        const tasks = this.getTasks();
        return tasks.length >= MAX_TASKS;
    }

    /**
     * Get task count
     */
    getTaskCount() {
        return this.getTasks().length;
    }
}

export default StorageService;
