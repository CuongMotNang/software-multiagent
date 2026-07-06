/**
 * Task Model - Entity and validation logic
 */

const MAX_TITLE_LENGTH = 200;
const MAX_DESC_LENGTH = 1000;

/**
 * Generate unique ID
 */
function generateId() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    // Fallback for older browsers
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Normalize text (trim and collapse spaces)
 */
function normalizeText(text) {
    if (!text) return '';
    return text.trim().replace(/\s+/g, ' ');
}

/**
 * Sanitize text for safe HTML rendering
 */
function sanitizeText(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;

    return date.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format date for detail view
 */
function formatDateDetail(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

class Task {
    constructor(data = {}) {
        this.id = data.id || generateId();
        this.title = data.title || '';
        this.description = data.description || '';
        this.status = data.status || 'pending';
        this.created_at = data.created_at || new Date().toISOString();
        this.updated_at = data.updated_at || new Date().toISOString();
        this.completed_at = data.completed_at || null;
    }

    /**
     * Validate task data
     * Returns { isValid: boolean, error: string|null }
     */
    static validate(title, description = '') {
        const normalizedTitle = normalizeText(title);

        if (!normalizedTitle) {
            return {
                isValid: false,
                error: 'Tiêu đề không được để trống'
            };
        }

        if (normalizedTitle.length > MAX_TITLE_LENGTH) {
            return {
                isValid: false,
                error: `Tiêu đề không được vượt quá ${MAX_TITLE_LENGTH} ký tự`
            };
        }

        if (description && description.length > MAX_DESC_LENGTH) {
            return {
                isValid: false,
                error: `Mô tả không được vượt quá ${MAX_DESC_LENGTH} ký tự`
            };
        }

        return { isValid: true, error: null };
    }

    /**
     * Create a new task
     */
    static create(title, description = '') {
        const validation = Task.validate(title, description);
        if (!validation.isValid) {
            throw new Error(validation.error);
        }

        const now = new Date().toISOString();
        return new Task({
            title: normalizeText(title),
            description: description || '',
            status: 'pending',
            created_at: now,
            updated_at: now,
            completed_at: null
        });
    }

    /**
     * Update task
     */
    update(title, description) {
        if (this.status === 'completed') {
            throw new Error('Không thể chỉnh sửa nhiệm vụ đã hoàn thành');
        }

        const validation = Task.validate(title, description);
        if (!validation.isValid) {
            throw new Error(validation.error);
        }

        this.title = normalizeText(title);
        this.description = normalizeText(description) || '';
        this.updated_at = new Date().toISOString();

        return this;
    }

    /**
     * Toggle completion status
     */
    toggleStatus() {
        const now = new Date().toISOString();

        if (this.status === 'pending') {
            this.status = 'completed';
            this.completed_at = now;
        } else {
            this.status = 'pending';
            this.completed_at = null;
        }

        this.updated_at = now;
        return this;
    }

    /**
     * Convert to plain object for storage
     */
    toJSON() {
        return {
            id: this.id,
            title: this.title,
            description: this.description,
            status: this.status,
            created_at: this.created_at,
            updated_at: this.updated_at,
            completed_at: this.completed_at
        };
    }

    /**
     * Create Task from plain object
     */
    static fromJSON(data) {
        return new Task(data);
    }
}

export { Task, generateId, normalizeText, sanitizeText, formatDate, formatDateDetail, MAX_TITLE_LENGTH, MAX_DESC_LENGTH };
