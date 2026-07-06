/**
 * Personal Task Manager - Main Application
 */

import StorageService from './storage.js';
import { Task } from './task.js';
import UIManager from './ui.js';

class TaskManagerApp {
    constructor() {
        this.storage = new StorageService();
        this.ui = new UIManager();
        this.tasks = [];
        this.debounceTimer = null;

        this._init();
    }

    /**
     * Initialize the application
     */
    _init() {
        // Check storage fallback
        if (this.storage.isMemoryFallback()) {
            this.ui.showStorageWarning(true);
        }

        // Load tasks
        this._loadTasks();

        // Setup event listeners
        this._setupEventListeners();

        // Initial render
        this._render();
    }

    /**
     * Load tasks from storage
     */
    _loadTasks() {
        const data = this.storage.getTasks();
        this.tasks = data.map(t => Task.fromJSON(t));
    }

    /**
     * Save tasks to storage
     */
    _saveTasks() {
        try {
            this.storage.saveTasks(this.tasks.map(t => t.toJSON()));
        } catch (e) {
            if (e.message === 'STORAGE_FULL') {
                alert('Bộ nhớ đã đầy, không thể lưu thêm. Vui lòng xóa nhiệm vụ cũ.');
            } else if (e.message === 'TASK_LIMIT_EXCEEDED') {
                this.ui.showLimitModal();
            } else {
                console.error('Lỗi lưu dữ liệu:', e);
            }
        }
    }

    /**
     * Render current state
     */
    _render() {
        this.ui.renderTaskList(this.tasks, this.ui.currentFilter);
    }

    /**
     * Setup all event listeners
     */
    _setupEventListeners() {
        // Add task button
        this.ui.addTaskBtn.addEventListener('click', () => {
            this._handleAddTaskClick();
        });

        // Back button (form)
        this.ui.backBtn.addEventListener('click', () => {
            this.ui.showScreen('list');
        });

        // Cancel button (form)
        this.ui.cancelBtn.addEventListener('click', () => {
            this.ui.showScreen('list');
        });

        // Detail back button
        this.ui.detailBackBtn.addEventListener('click', () => {
            this.ui.showScreen('list');
        });

        // Form submit
        this.ui.taskForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this._handleFormSubmit();
        });

        // Title input with counter
        this.ui.titleInput.addEventListener('input', (e) => {
            const length = e.target.value.length;
            this.ui.updateCounter(this.ui.titleCounter, length, 200);
            this.ui.clearFormError();
        });

        // Description input with counter
        this.ui.descInput.addEventListener('input', (e) => {
            const length = e.target.value.length;
            this.ui.updateCounter(this.ui.descCounter, length, 1000);
        });

        // FilterFAB click with debounce
        this.ui.addTaskBtn.addEventListener('click', () => {
            this._debounce(() => this._handleAddTaskClick(), 300);
        });

        // Filter tabs
        this.ui.filterTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.ui.setActiveFilter(filter);
                this._render();
            });
        });

        // Task list interactions (event delegation)
        this.ui.taskList.addEventListener('click', (e) => {
            this._handleTaskListClick(e);
        });

        // Task list checkbox change
        this.ui.taskList.addEventListener('change', (e) => {
            if (e.target.classList.contains('task-checkbox')) {
                const taskId = e.target.closest('.task-item').dataset.id;
                this._debounce(() => this._toggleTaskStatus(taskId), 300);
            }
        });

        // Delete modal
        this.ui.cancelDeleteBtn.addEventListener('click', () => {
            this.ui.hideDeleteModal();
        });

        this.ui.confirmDeleteBtn.addEventListener('click', () => {
            this._handleConfirmDelete();
        });

        // Limit modal
        this.ui.limitOkBtn.addEventListener('click', () => {
            this.ui.hideLimitModal();
        });

        // Close warning
        this.ui.closeWarningBtn.addEventListener('click', () => {
            this.ui.showStorageWarning(false);
        });

        // Detail screen actions (event delegation)
        this.ui.taskDetailContent.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (!action) return;

            if (action === 'back') {
                this.ui.showScreen('list');
            } else if (action === 'edit-detail') {
                const task = this.tasks.find(t => t.id === this._currentDetailId);
                if (task) {
                    this.ui.showEditForm(task);
                }
            } else if (action === 'delete-detail') {
                this.ui.showDeleteModal(this._currentDetailId);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (!this.ui.deleteModal.classList.contains('hidden')) {
                    this.ui.hideDeleteModal();
                } else if (!this.ui.limitModal.classList.contains('hidden')) {
                    this.ui.hideLimitModal();
                }
            }
        });
    }

    /**
     * Debounce utility
     */
    _debounce(fn, delay) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(fn, delay);
    }

    /**
     * Handle add task button click
     */
    _handleAddTaskClick() {
        if (this.storage.isLimitReached()) {
            this.ui.showLimitModal();
            return;
        }
        this.ui.showCreateForm();
    }

    /**
     * Handle form submit
     */
    _handleFormSubmit() {
        const title = this.ui.titleInput.value;
        const description = this.ui.descInput.value;

        // Validate
        const validation = Task.validate(title, description);
        if (!validation.isValid) {
            this.ui.showFormError(validation.error);
            return;
        }

        if (this.ui.editingTaskId) {
            // Edit mode
            const task = this.tasks.find(t => t.id === this.ui.editingTaskId);
            if (task) {
                if (task.status === 'completed') {
                    this.ui.showFormError('Không thể chỉnh sửa nhiệm vụ đã hoàn thành');
                    return;
                }
                try {
                    task.update(title, description);
                    this._saveTasks();
                    this._render();
                    this.ui.showScreen('list');
                } catch (e) {
                    this.ui.showFormError(e.message);
                }
            }
        } else {
            // Create mode
            try {
                const newTask = Task.create(title, description);
                this.tasks.push(newTask);
                this._saveTasks();
                this._render();
                this.ui.showScreen('list');
            } catch (e) {
                this.ui.showFormError(e.message);
            }
        }
    }

    /**
     * Handle task list click (event delegation)
     */
    _handleTaskListClick(e) {
        const taskItem = e.target.closest('.task-item');
        if (!taskItem) return;

        const taskId = taskItem.dataset.id;
        const action = e.target.dataset.action;

        if (!action) return;

        switch (action) {
            case 'toggle':
                // Handled by change event
                break;
            case 'view':
                this._viewTask(taskId);
                break;
            case 'edit':
                this._editTask(taskId);
                break;
            case 'delete':
                this.ui.showDeleteModal(taskId);
                break;
        }
    }

    /**
     * View task detail
     */
    _viewTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;

        this._currentDetailId = taskId;
        this.ui.showTaskDetail(task);
    }

    /**
     * Edit task
     */
    _editTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;

        if (task.status === 'completed') {
            // Should not happen due to UI, but handle just in case
            return;
        }

        this.ui.showEditForm(task);
    }

    /**
     * Toggle task status
     */
    _toggleTaskStatus(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;

        task.toggleStatus();
        this._saveTasks();
        this._render();
    }

    /**
     * Handle confirm delete
     */
    _handleConfirmDelete() {
        const taskId = this.ui.deletingTaskId;
        if (!taskId) return;

        this.tasks = this.tasks.filter(t => t.id !== taskId);
        this._saveTasks();
        this._render();
        this.ui.hideDeleteModal();

        // If we're in detail view, go back to list
        if (!this.ui.taskDetailScreen.classList.contains('hidden')) {
            this.ui.showScreen('list');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TaskManagerApp();
});
