class CloudStorage {
    constructor() {
        this.apiBase = '/api';
        this.files = [];
        this.currentUploadController = null;
        this.uploadStartTime = null;
        this.uploadStartBytes = 0;
        
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
        
        // Theme toggle elements
        this.themeToggle = document.getElementById('themeToggle');
        this.themeIcon = document.getElementById('themeIcon');
        
        // Share modal elements
        this.shareModal = document.getElementById('shareModal');
        this.shareFileName = document.getElementById('shareFileName');
        this.cancelShare = document.getElementById('cancelShare');
        this.createShare = document.getElementById('createShare');
        this.expiresInput = document.getElementById('expiresInput');
        this.maxDownloadsInput = document.getElementById('maxDownloadsInput');
        this.passwordShareInput = document.getElementById('passwordInput');
        this.existingShares = document.getElementById('existingShares');
        this.sharesList = document.getElementById('sharesList');
        
        // Share success modal elements
        this.shareSuccessModal = document.getElementById('shareSuccessModal');
        this.shareLinkInput = document.getElementById('shareLinkInput');
        this.copyLinkBtn = document.getElementById('copyLinkBtn');
        this.closeShareSuccess = document.getElementById('closeShareSuccess');
        
        // Initialize theme
        this.initializeTheme();
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

        // Share modal events
        this.cancelShare.addEventListener('click', () => {
            this.hideShareModal();
        });

        this.createShare.addEventListener('click', () => {
            this.createShareLink();
        });

        this.shareModal.addEventListener('click', (e) => {
            if (e.target === this.shareModal) {
                this.hideShareModal();
            }
        });

        // Share success modal events
        this.copyLinkBtn.addEventListener('click', () => {
            this.copyShareLink();
        });

        this.closeShareSuccess.addEventListener('click', () => {
            this.hideShareSuccessModal();
        });

        this.shareSuccessModal.addEventListener('click', (e) => {
            if (e.target === this.shareSuccessModal) {
                this.hideShareSuccessModal();
            }
        });

        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideDeleteModal();
                this.hideShareModal();
                this.hideShareSuccessModal();
            }
        });

        // Theme toggle event
        this.themeToggle.addEventListener('click', () => {
            this.toggleTheme();
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
        const fileIconClass = this.getFileIconClass(file.type);
        const formattedDate = new Date(file.modified).toLocaleString();
        const fileExtension = file.name.split('.').pop().toUpperCase() || 'FILE';

        card.innerHTML = `
            <div class="file-header">
                <i class="${fileIcon} file-icon ${fileIconClass}"></i>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-details">
                        <div class="file-meta">
                            <span class="file-type">${fileExtension}</span>
                            <span class="file-size">${file.size_formatted}</span>
                        </div>
                        <div class="file-date">${formattedDate}</div>
                    </div>
                </div>
            </div>
            <div class="file-actions">
                <a href="${this.apiBase}/download/${encodeURIComponent(file.name)}" 
                   class="btn btn-primary" download>
                    <i class="fas fa-download"></i> Download
                </a>
                <button class="btn btn-secondary" onclick="cloudStorage.showShareModal('${file.name}')">
                    <i class="fas fa-share-alt"></i> Share
                </button>
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

    getFileIconClass(type) {
        if (!type) return 'file-text';
        
        if (type.startsWith('image/')) return 'file-image';
        if (type.startsWith('video/')) return 'file-video';
        if (type.startsWith('audio/')) return 'file-audio';
        if (type.includes('pdf')) return 'file-pdf';
        if (type.includes('word') || type.includes('document')) return 'file-doc';
        if (type.includes('excel') || type.includes('spreadsheet')) return 'file-doc';
        if (type.includes('powerpoint') || type.includes('presentation')) return 'file-doc';
        if (type.includes('zip') || type.includes('rar') || type.includes('tar')) return 'file-archive';
        if (type.includes('text')) return 'file-text';
        
        return 'file-text';
    }

    async handleFileUpload(files) {
        if (files.length === 0) return;

        // Reset upload tracking and show progress
        this.resetUploadTracking();
        this.showUploadProgress();

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            try {
                await this.uploadFile(file, i + 1, files.length);
            } catch (error) {
                if (error.message === 'Upload was cancelled') {
                    // User cancelled, stop processing remaining files
                    break;
                }
                this.showToast('error', `Failed to upload ${file.name}: ${error.message}`);
            }
        }

        // Clean up
        this.currentUploadController = null;
        this.resetUploadTracking();
        
        // Hide upload progress and refresh
        this.hideUploadProgress();
        this.loadFiles();
        this.loadStorageInfo();
        
        // Reset file input
        this.fileInput.value = '';
    }

    async uploadFile(file, current, total) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);

            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    // Initialize timing on first progress event if not set
                    if (!this.uploadStartTime) {
                        this.uploadStartTime = Date.now();
                        this.uploadStartBytes = 0;
                    }
                    
                    // Calculate individual file progress
                    const fileProgress = (event.loaded / event.total) * 100;
                    
                    // Calculate overall progress across all files
                    const previousFiles = current - 1;
                    const overallProgress = ((previousFiles / total) + (fileProgress / 100 / total)) * 100;
                    
                    // Update progress bar and text
                    this.progressFill.style.width = `${overallProgress}%`;
                    
                    // Show detailed progress info
                    const uploadedMB = (event.loaded / 1024 / 1024).toFixed(1);
                    const totalMB = (event.total / 1024 / 1024).toFixed(1);
                    const speed = this.calculateUploadSpeed(event.loaded);
                    
                    this.progressText.innerHTML = `
                        <div class="upload-details">
                            <div class="file-info">Uploading: ${file.name} (${current}/${total})</div>
                            <div class="progress-info">
                                <span>${uploadedMB}MB / ${totalMB}MB</span>
                                <span>${fileProgress.toFixed(1)}%</span>
                                <span>${speed}</span>
                            </div>
                        </div>
                    `;
                }
            });

            // Handle upload completion
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        if (data.success) {
                            this.showToast('success', data.message);
                            
                            // Update to show file completed
                            const overallProgress = (current / total) * 100;
                            this.progressFill.style.width = `${overallProgress}%`;
                            
                            resolve(data);
                        } else {
                            reject(new Error(data.error));
                        }
                    } catch (error) {
                        reject(new Error('Invalid server response'));
                    }
                } else {
                    reject(new Error(`Upload failed with status: ${xhr.status}`));
                }
            });

            // Handle upload errors
            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });

            // Handle upload abort
            xhr.addEventListener('abort', () => {
                reject(new Error('Upload was cancelled'));
            });

            // Store the xhr object for potential cancellation
            this.currentUploadController = xhr;

            // Start the upload
            xhr.open('POST', `${this.apiBase}/upload`);
            xhr.send(formData);
        });
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

    calculateUploadSpeed(uploadedBytes) {
        if (!this.uploadStartTime) {
            return '0 KB/s';
        }

        const elapsed = (Date.now() - this.uploadStartTime) / 1000; // seconds
        if (elapsed < 0.1) return '0 KB/s'; // Avoid division by very small numbers
        
        const bytesPerSecond = uploadedBytes / elapsed;

        if (bytesPerSecond < 1024) {
            return `${bytesPerSecond.toFixed(0)} B/s`;
        } else if (bytesPerSecond < 1024 * 1024) {
            return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`;
        } else {
            return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)} MB/s`;
        }
    }

    resetUploadTracking() {
        this.uploadStartTime = null;
        this.uploadStartBytes = 0;
    }

    cancelUpload() {
        if (this.currentUploadController) {
            this.currentUploadController.abort();
            this.currentUploadController = null;
            this.hideUploadProgress();
            this.resetUploadTracking();
            this.showToast('info', 'Upload cancelled');
        }
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

    showShareModal(filename) {
        this.currentShareFile = filename;
        this.shareFileName.textContent = filename;
        
        // Reset form
        this.expiresInput.value = '';
        this.maxDownloadsInput.value = '';
        this.passwordShareInput.value = '';
        
        // Load existing shares
        this.loadExistingShares(filename);
        
        this.shareModal.classList.add('show');
    }

    hideShareModal() {
        this.shareModal.classList.remove('show');
        this.currentShareFile = null;
        this.existingShares.style.display = 'none';
    }

    async loadExistingShares(filename) {
        try {
            const response = await fetch(`${this.apiBase}/shares/${encodeURIComponent(filename)}`);
            const data = await response.json();

            if (data.success && data.shares.length > 0) {
                this.renderExistingShares(data.shares);
                this.existingShares.style.display = 'block';
            } else {
                this.existingShares.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading existing shares:', error);
            this.existingShares.style.display = 'none';
        }
    }

    renderExistingShares(shares) {
        const shareItems = shares.map(share => {
            const createdDate = new Date(share.created_at).toLocaleString();
            const expiresText = share.expires_at 
                ? new Date(share.expires_at).toLocaleString()
                : 'Never';
            const downloadsText = share.max_downloads 
                ? `${share.download_count}/${share.max_downloads}`
                : `${share.download_count}/∞`;

            return `
                <div class="share-item">
                    <div class="share-item-header">
                        <span><strong>ID:</strong> ${share.share_id}</span>
                        <button class="btn btn-danger btn-sm" onclick="cloudStorage.deleteShare('${share.share_id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    <div class="share-url">${share.share_url}</div>
                    <div class="share-stats">
                        <span><i class="fas fa-calendar"></i> Created: ${createdDate}</span>
                        <span><i class="fas fa-clock"></i> Expires: ${expiresText}</span>
                        <span><i class="fas fa-download"></i> Downloads: ${downloadsText}</span>
                        ${share.has_password ? '<span><i class="fas fa-lock"></i> Password Protected</span>' : ''}
                    </div>
                </div>
            `;
        }).join('');

        this.sharesList.innerHTML = shareItems;
    }

    async createShareLink() {
        if (!this.currentShareFile) return;

        const shareData = {
            filename: this.currentShareFile
        };

        // Add optional parameters
        if (this.expiresInput.value) {
            shareData.expires_hours = parseInt(this.expiresInput.value);
        }

        if (this.maxDownloadsInput.value) {
            shareData.max_downloads = parseInt(this.maxDownloadsInput.value);
        }

        if (this.passwordShareInput.value) {
            shareData.password = this.passwordShareInput.value;
        }

        try {
            this.createShare.disabled = true;
            this.createShare.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';

            const response = await fetch(`${this.apiBase}/share`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(shareData)
            });

            const data = await response.json();

            if (data.success) {
                this.hideShareModal();
                this.showShareSuccess(data.share_url);
                this.showToast('success', data.message);
            } else {
                this.showToast('error', 'Failed to create share: ' + data.error);
            }
        } catch (error) {
            this.showToast('error', 'Error creating share: ' + error.message);
        } finally {
            this.createShare.disabled = false;
            this.createShare.innerHTML = '<i class="fas fa-share"></i> Create Link';
        }
    }

    async deleteShare(shareId) {
        if (!confirm('Are you sure you want to delete this share link?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/share/${shareId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('success', data.message);
                // Reload existing shares
                if (this.currentShareFile) {
                    await this.loadExistingShares(this.currentShareFile);
                }
            } else {
                this.showToast('error', 'Failed to delete share: ' + data.error);
            }
        } catch (error) {
            this.showToast('error', 'Error deleting share: ' + error.message);
        }
    }

    showShareSuccess(shareUrl) {
        this.shareLinkInput.value = shareUrl;
        this.shareSuccessModal.classList.add('show');
    }

    hideShareSuccessModal() {
        this.shareSuccessModal.classList.remove('show');
    }

    async copyShareLink() {
        try {
            await navigator.clipboard.writeText(this.shareLinkInput.value);
            this.showToast('success', 'Share link copied to clipboard!');
            
            // Update button text temporarily
            const originalText = this.copyLinkBtn.innerHTML;
            this.copyLinkBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            
            setTimeout(() => {
                this.copyLinkBtn.innerHTML = originalText;
            }, 2000);
        } catch (error) {
            // Fallback for older browsers
            this.shareLinkInput.select();
            this.shareLinkInput.setSelectionRange(0, 99999);
            document.execCommand('copy');
            this.showToast('success', 'Share link copied to clipboard!');
        }
    }

    showToast(type, message, title = null) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = type === 'success' ? 'fas fa-check-circle' : 
                    type === 'error' ? 'fas fa-exclamation-circle' : 
                    type === 'warning' ? 'fas fa-exclamation-triangle' :
                    'fas fa-info-circle';

        const toastTitle = title || (
            type === 'success' ? 'Success' :
            type === 'error' ? 'Error' :
            type === 'warning' ? 'Warning' :
            'Info'
        );

        toast.innerHTML = `
            <i class="${icon} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-title">${toastTitle}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" aria-label="Close">&times;</button>
        `;

        // Add click handler for close button
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.removeToast(toast);
        });

        this.toastContainer.appendChild(toast);

        // Show with animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Auto remove after 5 seconds
        setTimeout(() => {
            this.removeToast(toast);
        }, 5000);
    }

    removeToast(toast) {
        if (toast && toast.parentNode) {
            toast.classList.remove('show');
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }

    // Theme management methods
    initializeTheme() {
        // Check for saved theme preference or default to 'light'
        const savedTheme = localStorage.getItem('cloudStorageTheme') || 'light';
        this.setTheme(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('cloudStorageTheme', theme);
        
        // Update theme icon
        if (this.themeIcon) {
            if (theme === 'dark') {
                this.themeIcon.className = 'fas fa-sun';
                this.themeToggle.title = 'Switch to light mode';
            } else {
                this.themeIcon.className = 'fas fa-moon';
                this.themeToggle.title = 'Switch to dark mode';
            }
        }
        
        // Add smooth transition effect
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
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
