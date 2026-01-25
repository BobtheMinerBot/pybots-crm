// CRM Main JavaScript - Extracted from base.html
// This file is cacheable by the browser

// ========== Toast Notifications ==========
        const toastIcons = {
            success: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
            error: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
            info: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
            warning: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
        };

        function showToast(message, type = 'info', duration = null, title = null) {
            // Default durations by type - success is quick (1.5s), others longer
            const defaultDurations = { success: 1500, error: 6000, warning: 5000, info: 4000 };
            duration = duration ?? defaultDurations[type] ?? 4000;
            
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;

            // Auto-generate title if not provided
            const autoTitle = title || {
                'success': 'Success',
                'error': 'Error',
                'warning': 'Warning',
                'info': 'Info'
            }[type] || 'Notification';

            toast.innerHTML = `
                <span class="toast-icon">${toastIcons[type]}</span>
                <div class="toast-body">
                    <div class="toast-title">${autoTitle}</div>
                    <div class="toast-content">${message}</div>
                </div>
                <button class="toast-close" onclick="dismissToast(this.parentElement)">&times;</button>
                ${duration > 0 ? `<div class="toast-progress" style="animation-duration: ${duration}ms;"></div>` : ''}
            `;
            container.appendChild(toast);

            // Pause progress on hover
            if (duration > 0) {
                let timeoutId;
                let remainingTime = duration;
                let startTime = Date.now();

                const startTimeout = () => {
                    startTime = Date.now();
                    timeoutId = setTimeout(() => dismissToast(toast), remainingTime);
                };

                toast.addEventListener('mouseenter', () => {
                    clearTimeout(timeoutId);
                    remainingTime -= (Date.now() - startTime);
                });

                toast.addEventListener('mouseleave', startTimeout);

                startTimeout();
            }

            return toast;
        }

        function dismissToast(toast) {
            if (!toast || toast.classList.contains('removing')) return;
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }

        // Shorthand toast functions
        function toastSuccess(message, title) { return showToast(message, 'success', 1500, title); }
        function toastError(message, title) { return showToast(message, 'error', 6000, title); }
        function toastWarning(message, title) { return showToast(message, 'warning', 5000, title); }
        function toastInfo(message, title) { return showToast(message, 'info', 4000, title); }

        // ========== Confirmation Dialog ==========
        function showConfirmDialog({ title, message, confirmText = 'Confirm', cancelText = 'Cancel', type = 'danger', onConfirm, onCancel }) {
            const iconSvg = type === 'danger'
                ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>'
                : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';

            const overlay = document.createElement('div');
            overlay.className = 'confirm-dialog-overlay';
            overlay.innerHTML = `
                <div class="confirm-dialog">
                    <div class="confirm-dialog-icon ${type}">${iconSvg}</div>
                    <div class="confirm-dialog-title">${title}</div>
                    <div class="confirm-dialog-message">${message}</div>
                    <div class="confirm-dialog-actions">
                        <button class="btn btn-secondary" data-action="cancel">${cancelText}</button>
                        <button class="btn ${type === 'danger' ? 'btn-danger' : 'btn-primary'}" data-action="confirm">${confirmText}</button>
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const confirmBtn = overlay.querySelector('[data-action="confirm"]');
            const cancelBtn = overlay.querySelector('[data-action="cancel"]');

            const cleanup = () => overlay.remove();

            confirmBtn.addEventListener('click', () => {
                cleanup();
                if (onConfirm) onConfirm();
            });

            cancelBtn.addEventListener('click', () => {
                cleanup();
                if (onCancel) onCancel();
            });

            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    cleanup();
                    if (onCancel) onCancel();
                }
            });

            // Focus confirm button
            confirmBtn.focus();

            return { close: cleanup };
        }

        // ========== Keyboard Shortcuts ==========
        function openShortcutsModal() {
            document.getElementById('shortcutsModal').classList.add('visible');
        }

        function closeShortcutsModal() {
            document.getElementById('shortcutsModal').classList.remove('visible');
        }

        document.addEventListener('keydown', function (e) {
            // Skip if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                if (e.key === 'Escape') {
                    e.target.blur();
                }
                return;
            }

            // ? - Show shortcuts modal
            if (e.key === '?' || (e.shiftKey && e.key === '/')) {
                e.preventDefault();
                openShortcutsModal();
                return;
            }

            // Escape - Close modals
            if (e.key === 'Escape') {
                closeShortcutsModal();
                // Close other modals - check for any visible modal
                document.querySelectorAll('.modal-overlay.visible, .shortcuts-modal.visible').forEach(m => m.classList.remove('visible'));
                return;
            }

            // N - New lead (only on leads page)
            if (e.key === 'n' || e.key === 'N') {
                const addLeadBtn = document.querySelector('a[href*="add"]');
                if (addLeadBtn) {
                    e.preventDefault();
                    addLeadBtn.click();
                }
                return;
            }

            // S or / - Focus search
            if (e.key === 's' || e.key === 'S' || e.key === '/') {
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    e.preventDefault();
                    searchInput.focus();
                    searchInput.select();
                }
                return;
            }

            // E - Edit (on lead detail page)
            if (e.key === 'e' || e.key === 'E') {
                const editBtn = document.querySelector('a.btn[href*="edit"]');
                if (editBtn) {
                    e.preventDefault();
                    editBtn.click();
                }
                return;
            }

            // J/K or Arrow keys - Navigate leads
            if (['j', 'k', 'J', 'K', 'ArrowDown', 'ArrowUp'].includes(e.key)) {
                const rows = document.querySelectorAll('.grid-table tbody tr');
                if (rows.length === 0) return;

                e.preventDefault();
                let currentIndex = -1;
                rows.forEach((row, i) => {
                    if (row.classList.contains('selected')) currentIndex = i;
                });

                if (e.key === 'j' || e.key === 'J' || e.key === 'ArrowDown') {
                    currentIndex = Math.min(currentIndex + 1, rows.length - 1);
                } else {
                    currentIndex = Math.max(currentIndex - 1, 0);
                }

                rows.forEach(row => row.classList.remove('selected'));
                rows[currentIndex].classList.add('selected');
                rows[currentIndex].scrollIntoView({ block: 'nearest' });
                return;
            }

            // Enter - Open selected lead
            if (e.key === 'Enter') {
                const selectedRow = document.querySelector('.grid-table tbody tr.selected');
                if (selectedRow) {
                    const link = selectedRow.querySelector('.lead-name a');
                    if (link) {
                        e.preventDefault();
                        link.click();
                    }
                }
                return;
            }
        });

        // Close shortcuts modal on click outside
        document.getElementById('shortcutsModal').addEventListener('click', function (e) {
            if (e.target === this) {
                closeShortcutsModal();
            }
        });

        // ========== Stage Collapse Memory ==========
        function saveStageState(stageId, collapsed) {
            const states = JSON.parse(localStorage.getItem('stageCollapseStates') || '{}');
            states[stageId] = collapsed;
            localStorage.setItem('stageCollapseStates', JSON.stringify(states));
        }

        function restoreStageStates() {
            const states = JSON.parse(localStorage.getItem('stageCollapseStates') || '{}');
            Object.keys(states).forEach(stageId => {
                const section = document.getElementById(stageId);
                if (section && states[stageId]) {
                    section.classList.add('collapsed');
                }
            });
        }

        // Call on page load
        document.addEventListener('DOMContentLoaded', restoreStageStates);

        // ========== Recently Viewed Leads ==========
        function addToRecentlyViewed(leadId, leadName, leadStatus) {
            let recent = JSON.parse(localStorage.getItem('recentlyViewedLeads') || '[]');
            // Remove if already exists
            recent = recent.filter(l => l.id !== leadId);
            // Add to front
            recent.unshift({ id: leadId, name: leadName, status: leadStatus });
            // Keep only last 5
            recent = recent.slice(0, 5);
            localStorage.setItem('recentlyViewedLeads', JSON.stringify(recent));
        }

        function getRecentlyViewed() {
            return JSON.parse(localStorage.getItem('recentlyViewedLeads') || '[]');
        }

        // ========== Mobile Navigation ==========
        function toggleMobileNav() {
            const drawer = document.getElementById('mobileNavDrawer');
            const overlay = document.getElementById('mobileNavOverlay');
            const isOpen = drawer.classList.contains('open');

            if (isOpen) {
                closeMobileNav();
            } else {
                drawer.classList.add('open');
                overlay.classList.add('visible');
                document.body.style.overflow = 'hidden';
            }
        }

        function closeMobileNav() {
            const drawer = document.getElementById('mobileNavDrawer');
            const overlay = document.getElementById('mobileNavOverlay');

            drawer.classList.remove('open');
            overlay.classList.remove('visible');
            document.body.style.overflow = '';
        }

        // Close mobile nav on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeMobileNav();
            }
        });

        // Close mobile nav when clicking a link
        document.querySelectorAll('.mobile-nav-links a').forEach(link => {
            link.addEventListener('click', closeMobileNav);
        });

        // ========== Mobile Table Scroll Indicator ==========
        document.addEventListener('DOMContentLoaded', function() {
            const tableWrappers = document.querySelectorAll('.grid-table-wrapper');
            tableWrappers.forEach(wrapper => {
                wrapper.addEventListener('scroll', function() {
                    const maxScroll = this.scrollWidth - this.clientWidth;
                    if (this.scrollLeft >= maxScroll - 10) {
                        this.classList.add('scrolled-right');
                    } else {
                        this.classList.remove('scrolled-right');
                    }
                });
            });
        });

        // ========== Viewport Height Fix for Mobile ==========
        function setViewportHeight() {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        }
        setViewportHeight();
        window.addEventListener('resize', setViewportHeight);