/**
 * UI Module - Rendering and DOM manipulation
 */

import { sanitizeText, formatDate, formatDateDetail } from './task.js';

/**
 * UI Manager class
 */
class UIManager {
    constructor() {
        this.currentFilter = 'all';
        this.editingTaskId = null;
        this.deletingTaskId = null;
        this._initElements();
    }

    /**
     * Initialize DOM element references
     */
    _initElements() {
        // Screens
        this.taskListScreen = document.getElementById('task-list-screen');
        this.taskFormScreen = document.getElementById('task-form-screen');
        this.taskDetailScreen = document.getElementById('task-detail-screen');

        // Task List
        this.taskList = document.getElementById('task-list');
        this.emptyState = document.getElementById('empty-state');
        this.taskCount = document.getElementById('task-count');
        this.filterTabs = document.querySelectorAll('.filter-tab');

        // Form
        this.taskForm = document.getElementById('task-form');
        this.formTitle = document.getElementById('form-title');
        this.titleInput = document.getElementById('task-title');
        this.descInput = document.getElementById('task-description');
        this.titleError = document.getElementById('title-error');
        this.titleCounter = document.getElementById('title-counter');
        this.descCounter = document.getElementById('desc-counter');

        // Detail
        this.taskDetailContent = document.getElementById('task-detail-content');

        // Modals
        this.deleteModal = document.getElementById('delete-modal');
        this.limitModal = document.getElementById('limit-modal');
        this.storageWarning = document.getElementById('storage-warning');

        // Buttons
        this.addTaskBtn = document.getElementById('add-task-btn');
        this.backBtn = document.getElementById('back-btn');
        this.cancelBtn = document.getElementById('cancel-btn');
        this.detailBackBtn = document.getElementById('detail-back-btn');
        this.cancelDeleteBtn = document.getElementById('cancel-delete-btn');
        this.confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        this.limitOkBtn = document.getElementById('limit-ok-btn');
        this.closeWarningBtn = document.getElementById('close-warning');
    }

    /**
     * Show a specific screen
     */
    showScreen(screenName) {
        this.taskListScreen.classList.add('hidden');
        this.taskFormScreen.classList.add('hidden');
        this.taskDetailScreen.classList.add('hidden');

        switch (screenName) {
            case 'list':
                this.taskListScreen.classList.remove('hidden');
                break;
            case 'form':
                this.taskFormScreen.classList.remove('hidden');
                break;
            case 'detail':
                this.taskDetailScreen.classList.remove('hidden');
                break;
        }
    }

    /**
     * Show/hide storage warning
     */
    showStorageWarning(show) {
        if (show) {
            this.storageWarning.classList.remove('hidden');
        } else {
            this.storageWarning.classList.add('hidden');
        }
    }

    /**
     * Render task list
     */
    renderTaskList(tasks, filter = 'all') {
        // Filter tasks
        let filteredTasks = tasks;
        if (filter === 'pending') {
            filteredTasks = tasks.filter(t => t.status === 'pending');
        } else if (filter === 'completed') {
            filteredTasks = tasks.filter(t => t.status === 'completed');
        }

        // Sort: pending first, then by created_at desc
        filteredTasks.sort((a, b) => {
            if (a.status !== b.status) {
                return a.status === 'pending' ? -1 : 1;
            }
            return new Date(b.created_at) - new Date(a.created_at);
        });

        // Update count
        const totalCount = tasks.length;
        const filteredCount = filteredTasks.length;
        const pendingCount = tasks.filter(t => t.status === 'pending').length;
        const completedCount = tasks.filter(t => t.status === 'completed').length;

        if (filter === 'all') {
            this.taskCount.textContent = `${totalCount} nhiệm vụ (${pendingCount} chưa hoàn thành, ${completedCount} đã hoàn thành)`;
        } else if (filter === 'pending') {
            this.taskCount.textContent = `${filteredCount} nhiệm vụ chưa hoàn thành / ${totalCount} tổng`;
        } else {
            this.taskCount.textContent = `${filteredCount} nhiệm vụ đã hoàn thành / ${totalCount} tổng`;
        }

        // Show/hide empty state
        if (filteredTasks.length === 0) {
            this.taskList.innerHTML = '';
            this.emptyState.classList.remove('hidden');
            return;
        }

        this.emptyState.classList.add('hidden');

        // Render tasks
        this.taskList.innerHTML = filteredTasks.map(task => this._renderTaskItem(task)).join('');
    }

    /**
     * Render a single task item
     */
    _renderTaskItem(task) {
        const isCompleted = task.status === 'completed';
        const statusText = isCompleted ? 'Đã hoàn thành' : 'Chưa hoàn thành';
        const statusClass = isCompleted ? 'completed' : 'pending';
        const dateText = isCompleted
            ? `Hoàn thành: ${formatDate(task.completed_at)}`
            : `Tạo: ${formatDate(task.created_at)}`;

        return `
            <li class="task-item ${statusClass}" data-id="${task.id}">
                <input
                    type="checkbox"
                    class="task-checkbox"
                    ${isCompleted ? 'checked' : ''}
                    aria-label="Đánh dấu ${isCompleted ? 'chưa hoàn thành' : 'hoàn thành'} nhiệm vụ ${sanitizeText(task.title)}"
                    data-action="toggle"
                >
                <div class="task-content" data-action="view">
                    <div class="task-title">${sanitizeText(task.title)}</div>
                    <div class="task-meta">
                        <span class="task-status ${statusClass}">${statusText}</span>
                        <span>${dateText}</span>
                    </div>
                </div>
                <div class="task-actions">
                    <button class="action-btn" data-action="view" aria-label="Xem chi tiết nhiệm vụ ${sanitizeText(task.title)}">
                        👁
                    </button>
                    ${!isCompleted ? `
                    <button class="action-btn" data-action="edit" aria-label="Chỉnh sửa nhiệm vụ ${sanitizeText(task.title)}">
                        ✏️
                    </button>
                    ` : ''}
                    <button class="action-btn delete" data-action="delete" aria-label="Xóa nhiệm vụ ${sanitizeText(task.title)}">
                        🗑
                    </button>
                </div>
            </li>
        `;
    }

    /**
     * Show create form
     */
    showCreateForm() {
        this.editingTaskId = null;
        this.formTitle.textContent = 'Thêm việc mới';
        this.taskForm.reset();
        this.titleError.textContent = '';
        this.titleCounter.textContent = '0/200';
        this.descCounter.textContent = '0/1000';
        this.titleCounter.classList.remove('warning');
        this.showScreen('form');
        this.titleInput.focus();
    }

    /**
     * Show edit form
     */
    showEditForm(task) {
        this.editingTaskId = task.id;
        this.formTitle.textContent = 'Chỉnh sửa nhiệm vụ';
        this.titleInput.value = task.title;
        this.descInput.value = task.description || '';
        this.titleError.textContent = '';
        this.titleCounter.textContent = `${task.title.length}/200`;
        this.descCounter.textContent = `${(task.description || '').length}/1000`;
        this.titleCounter.classList.remove('warning');
        this.showScreen('form');
        this.titleInput.focus();
    }

    /**
     * Show task detail
     */
    showTaskDetail(task) {
        const isCompleted = task.status === 'completed';
        const statusText = isCompleted ? 'Đã hoàn thành' : 'Chưa hoàn thành';
        const statusClass = isCompleted ? 'completed' : 'pending';

        this.taskDetailContent.innerHTML = `
            <div class="detail-status ${statusClass}">
                ${isCompleted ? '✅' : '⏳'} ${statusText}
            </div>
            <div class="detail-title">${sanitizeText(task.title)}</div>
            <div class="detail-description">${sanitizeText(task.description) || ''}</div>
            <div class="detail-meta">
                <div>📅 Tạo lúc: ${formatDateDetail(task.created_at)}</div>
                <div>🔄 Cập nhật: ${formatDateDetail(task.updated_at)}</div>
                ${task.completed_at ? `<div>✅ Hoàn thành: ${formatDateDetail(task.completed_at)}</div>` : ''}
            </div>
            <div class="detail-actions">
                <button class="btn btn-secondary" data-action="back">← Quay lại</button>
                ${!isCompleted ? `<button class="btn btn-primary" data-action="edit-detail">✏️ Chỉnh sửa</button>` : ''}
                <button class="btn btn-danger" data-action="delete-detail">🗑 Xóa</button>
            </div>
        `;

        this.showScreen('detail');
    }

    /**
     * Show delete confirmation modal
     */
    showDeleteModal(taskId) {
        this.deletingTaskId = taskId;
        this.deleteModal.classList.remove('hidden');
    }

    /**
     * Hide delete modal
     */
    hideDeleteModal() {
        this.deletingTaskId = null;
        this.deleteModal.classList.add('hidden');
    }

    /**
     * Show limit reached modal
     */
    showLimitModal() {
        this.limitModal.classList.remove('hidden');
    }

    /**
     * Hide limit modal
     */
    hideLimitModal() {
        this.limitModal.classList.add('hidden');
    }

    /**
     * Show error on form
     */
    showFormError(message) {
        this.titleError.textContent = message;
    }

    /**
     * Clear form error
     */
    clearFormError() {
        this.titleError.textContent = '';
    }

    /**
     * Update character counter
     */
    updateCounter(element, current, max) {
        element.textContent = `${current}/${max}`;
        if (current >= max) {
            element.classList.add('warning');
        } else {
            element.classList.remove('warning');
        }
    }

    /**
     * Set active filter tab
     */
    setActiveFilter(filter) {
        this.currentFilter = filter;
        this.filterTabs.forEach(tab => {
            const isActive = tab.dataset.filter === filter;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-selected', isActive);
            tab.setAttribute('tabindex', isActive ? '0' : '-1');
        });
    }
}

export default UIManager;
