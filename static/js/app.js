class CloudStorage {
    constructor() {
        this.apiBase = '/api';
        this.files = [];
        this.currentUploadController = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadFiles();
        this.loadStorageInfo();
    }

    initializeElements() {
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.filesContainer = document.getElementById('filesContainer');
        this.loadingFiles = document.getElementById('loadingFiles');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.storageInfo = document.getElementById('storageInfo');
        this.toastContainer = document.getElementById('toastContainer');
        this.deleteModal = document.getElementById('deleteModal');
        this.deleteFileName = document.getElementById('deleteFileName');
        this.cancelDelete = document.getElementById('cancelDelete');
        this.confirmDelete = document.getElementById('confirmDelete');
    }

    bindEvents() {
        // Upload area events
        this.uploadArea.addEventListener('click', () => {
            if (!this.uploadProgress.style.display || this.uploadProgress.style.display === 'none') {
                this.fileInput.click();
            }
        });

        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('dragover');
        });

        this.uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');
        });

        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files);
            this.handleFileUpload(files);
        });

        // File input change
        this.fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFileUpload(files);
        });

        // Refresh button
        this.refreshBtn.addEventListener('click', () => {
            this.loadFiles();
            this.loadStorageInfo();
        });

        // Modal events
        this.cancelDelete.addEventListener('click', () => {
            this.hideDeleteModal();
        });

        this.confirmDelete.addEventListener('click', () => {
            this.executeDelete();
        });

        // Close modal on background click
        this.deleteModal.addEventListener('click', (e) => {
            if (e.target === this.deleteModal) {
                this.hideDeleteModal();
            }
        });

        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideDeleteModal();
            }
        });
    }

    async loadFiles() {
        try {
            this.showLoading();
            const response = await fetch(`${this.apiBase}/files`);
            const data = await response.json();

            if (data.success) {
                this.files = data.files;
                this.renderFiles();
            } else {
                this.showToast('error', 'Failed to load files: ' + data.error);
            }
        } catch (error) {
            this.showToast('error', 'Error loading files: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async loadStorageInfo() {
        try {
            const response = await fetch(`${this.apiBase}/storage`);
            const data = await response.json();

            if (data.success) {
                const storage = data.storage;
                const usagePercent = ((storage.used_space / storage.total_space) * 100).toFixed(1);
                this.storageInfo.innerHTML = `
                    <span class="storage-text">
                        ${storage.used_space_formatted} / ${storage.total_space_formatted} 
                        (${usagePercent}%) • ${storage.file_count} files
                    </span>
                `;
            }
        } catch (error) {
            console.error('Error loading storage info:', error);
        }
    }

    showLoading() {
        this.loadingFiles.style.display = 'block';
        this.filesContainer.innerHTML = '';
        this.filesContainer.appendChild(this.loadingFiles);
    }

    hideLoading() {
        this.loadingFiles.style.display = 'none';
    }

    renderFiles() {
        if (this.files.length === 0) {
            this.filesContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <h3>No files uploaded yet</h3>
                    <p>Upload your first file using the area above</p>
                </div>
            `;
            return;
        }

        const filesGrid = document.createElement('div');
        filesGrid.className = 'files-grid';

        this.files.forEach(file => {
            const fileCard = this.createFileCard(file);
            filesGrid.appendChild(fileCard);
        });

        this.filesContainer.innerHTML = '';
        this.filesContainer.appendChild(filesGrid);
    }

    createFileCard(file) {
        const card = document.createElement('div');
        card.className = 'file-card';

        const fileIcon = this.getFileIcon(file.type);
        const formattedDate = new Date(file.modified).toLocaleString();

        card.innerHTML = `
            <div class="file-info">
                <div class="file-name">
                    <i class="${fileIcon}"></i> ${file.name}
                </div>
                <div class="file-meta">
                    <span class="file-size">${file.size_formatted}</span>
                    <span class="file-type">${file.type || 'unknown'}</span>
                </div>
                <div class="file-date">${formattedDate}</div>
            </div>
            <div class="file-actions">
                <a href="${this.apiBase}/download/${encodeURIComponent(file.name)}" 
                   class="btn btn-primary" download>
                    <i class="fas fa-download"></i> Download
                </a>
                <button class="btn btn-danger" onclick="cloudStorage.showDeleteModal('${file.name}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        `;

        return card;
    }

    getFileIcon(type) {
        if (!type) return 'fas fa-file';
        
        if (type.startsWith('image/')) return 'fas fa-file-image';
        if (type.startsWith('video/')) return 'fas fa-file-video';
        if (type.startsWith('audio/')) return 'fas fa-file-audio';
        if (type.includes('pdf')) return 'fas fa-file-pdf';
        if (type.includes('word') || type.includes('document')) return 'fas fa-file-word';
        if (type.includes('excel') || type.includes('spreadsheet')) return 'fas fa-file-excel';
        if (type.includes('powerpoint') || type.includes('presentation')) return 'fas fa-file-powerpoint';
        if (type.includes('zip') || type.includes('rar') || type.includes('tar')) return 'fas fa-file-archive';
        if (type.includes('text')) return 'fas fa-file-alt';
        
        return 'fas fa-file';
    }

    async handleFileUpload(files) {
        if (files.length === 0) return;

        // Show upload progress
        this.showUploadProgress();

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            try {
                await this.uploadFile(file, i + 1, files.length);
            } catch (error) {
                this.showToast('error', `Failed to upload ${file.name}: ${error.message}`);
            }
        }

        // Hide upload progress and refresh
        this.hideUploadProgress();
        this.loadFiles();
        this.loadStorageInfo();
        
        // Reset file input
        this.fileInput.value = '';
    }

    async uploadFile(file, current, total) {
        const formData = new FormData();
        formData.append('file', file);

        // Update progress text
        this.progressText.textContent = `Uploading ${file.name} (${current}/${total})...`;

        const response = await fetch(`${this.apiBase}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            this.showToast('success', data.message);
            // Update progress bar
            const progressPercent = (current / total) * 100;
            this.progressFill.style.width = `${progressPercent}%`;
        } else {
            throw new Error(data.error);
        }
    }

    showUploadProgress() {
        this.uploadProgress.style.display = 'flex';
        this.progressFill.style.width = '0%';
    }

    hideUploadProgress() {
        setTimeout(() => {
            this.uploadProgress.style.display = 'none';
        }, 500);
    }

    showDeleteModal(filename) {
        this.deleteFileName.textContent = filename;
        this.deleteModal.classList.add('show');
        this.currentDeleteFile = filename;
    }

    hideDeleteModal() {
        this.deleteModal.classList.remove('show');
        this.currentDeleteFile = null;
    }

    async executeDelete() {
        if (!this.currentDeleteFile) return;

        try {
            const response = await fetch(`${this.apiBase}/delete/${encodeURIComponent(this.currentDeleteFile)}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('success', data.message);
                this.loadFiles();
                this.loadStorageInfo();
            } else {
                this.showToast('error', 'Failed to delete file: ' + data.error);
            }
        } catch (error) {
            this.showToast('error', 'Error deleting file: ' + error.message);
        } finally {
            this.hideDeleteModal();
        }
    }

    showToast(type, message) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = type === 'success' ? 'fas fa-check-circle' : 
                    type === 'error' ? 'fas fa-exclamation-circle' : 
                    'fas fa-info-circle';

        toast.innerHTML = `
            <i class="${icon}"></i>
            <span class="toast-message">${message}</span>
            <button class="toast-close">&times;</button>
        `;

        // Add click handler for close button
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.removeToast(toast);
        });

        this.toastContainer.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            this.removeToast(toast);
        }, 5000);
    }

    removeToast(toast) {
        if (toast && toast.parentNode) {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }
}

// Add slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize the application
let cloudStorage;
document.addEventListener('DOMContentLoaded', () => {
    cloudStorage = new CloudStorage();
});
