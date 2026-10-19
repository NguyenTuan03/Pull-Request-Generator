/**
 * @file app.js - Auto PR Generator Frontend Logic
 * Strictly typed with JSDoc without using 'any'
 */

/**
 * @typedef {'Bugfix' | 'Feature' | 'Performance' | 'Security' | 'Database changes' | 'BREAKING CHANGE' | 'Both FE and BE (note different deployment time)'} ChangeType
 * 
 * @typedef {Object} FileChange
 * @property {string} path
 * @property {number} additions
 * @property {number} deletions
 * @property {string} change_type
 * 
 * @typedef {Object} PRMetadata
 * @property {string} owner
 * @property {string} repo
 * @property {number} number
 * @property {string} title
 * @property {string} author
 * @property {string} base_branch
 * @property {string} head_branch
 * @property {string} url
 * @property {string} body
 * @property {string[]} commits
 * @property {FileChange[]} files
 * @property {number} total_additions
 * @property {number} total_deletions
 * 
 * @typedef {Object} SummarizeResponse
 * @property {'success' | 'error'} status
 * @property {string} pr_url
 * @property {string} pr_title
 * @property {string} summary_markdown
 * @property {string} model_used
 * @property {number} execution_time_seconds
 * @property {string|null} error_message
 * @property {PRMetadata|null} metadata
 * 
 * @typedef {Object} HistoryItem
 * @property {string} id
 * @property {string} created_at
 * @property {string} pr_url
 * @property {string} pr_title
 * @property {string} model_used
 * @property {string} summary_markdown
 */

// DOM Elements
const prForm = /** @type {HTMLFormElement} */ (document.getElementById('pr-form'));
const prUrlInput = /** @type {HTMLInputElement} */ (document.getElementById('pr-url-input'));
const modelSelect = /** @type {HTMLSelectElement} */ (document.getElementById('model-select'));
const customNotesInput = /** @type {HTMLInputElement} */ (document.getElementById('custom-notes'));
const btnFetchInfo = /** @type {HTMLButtonElement} */ (document.getElementById('btn-fetch-info'));
const btnGenerate = /** @type {HTMLButtonElement} */ (document.getElementById('btn-generate'));
const btnSamplePr = /** @type {HTMLButtonElement} */ (document.getElementById('btn-sample-pr'));
const generateSpinner = /** @type {HTMLElement} */ (document.getElementById('generate-spinner'));
const generateIcon = /** @type {HTMLElement} */ (document.getElementById('generate-icon'));
const generateText = /** @type {HTMLElement} */ (document.getElementById('generate-text'));

// Metadata elements
const metadataCard = /** @type {HTMLElement} */ (document.getElementById('pr-metadata-card'));
const metaRepo = /** @type {HTMLElement} */ (document.getElementById('meta-repo'));
const metaHead = /** @type {HTMLElement} */ (document.getElementById('meta-head'));
const metaBase = /** @type {HTMLElement} */ (document.getElementById('meta-base'));
const metaFilesCount = /** @type {HTMLElement} */ (document.getElementById('meta-files-count'));
const metaAdditions = /** @type {HTMLElement} */ (document.getElementById('meta-additions'));
const metaDeletions = /** @type {HTMLElement} */ (document.getElementById('meta-deletions'));
const metaTitle = /** @type {HTMLElement} */ (document.getElementById('meta-title'));
const metaAuthor = /** @type {HTMLElement} */ (document.getElementById('meta-author'));
const metaCommitsCount = /** @type {HTMLElement} */ (document.getElementById('meta-commits-count'));
const metaGithubLink = /** @type {HTMLAnchorElement} */ (document.getElementById('meta-github-link'));

// Result elements
const resultCard = /** @type {HTMLElement} */ (document.getElementById('result-card'));
const tabButtons = /** @type {NodeListOf<HTMLButtonElement>} */ (document.querySelectorAll('.tab-btn'));
const tabPanes = /** @type {NodeListOf<HTMLElement>} */ (document.querySelectorAll('.tab-pane'));
const markdownRenderedView = /** @type {HTMLElement} */ (document.getElementById('markdown-rendered-view'));
const markdownEditor = /** @type {HTMLTextAreaElement} */ (document.getElementById('markdown-editor'));
const wordCharCount = /** @type {HTMLElement} */ (document.getElementById('word-char-count'));
const filesListView = /** @type {HTMLElement} */ (document.getElementById('files-list-view'));
const resultTimeBadge = /** @type {HTMLElement} */ (document.getElementById('result-time-badge'));
const btnCopyMarkdown = /** @type {HTMLButtonElement} */ (document.getElementById('btn-copy-markdown'));
const copyBtnText = /** @type {HTMLElement} */ (document.getElementById('copy-btn-text'));
const btnDownloadMd = /** @type {HTMLButtonElement} */ (document.getElementById('btn-download-md'));

// Loading elements
const loadingCard = /** @type {HTMLElement} */ (document.getElementById('loading-card'));
const loaderStatusText = /** @type {HTMLElement} */ (document.getElementById('loader-status-text'));
const loaderSubText = /** @type {HTMLElement} */ (document.getElementById('loader-sub-text'));
const stepFetch = /** @type {HTMLElement} */ (document.getElementById('step-fetch'));
const stepFilter = /** @type {HTMLElement} */ (document.getElementById('step-filter'));
const stepAi = /** @type {HTMLElement} */ (document.getElementById('step-ai'));
const stepDone = /** @type {HTMLElement} */ (document.getElementById('step-done'));

// Modals & Navigation
const btnOpenGuide = /** @type {HTMLButtonElement} */ (document.getElementById('btn-open-guide'));
const btnCloseGuide = /** @type {HTMLButtonElement} */ (document.getElementById('btn-close-guide'));
const btnGotIt = /** @type {HTMLButtonElement} */ (document.getElementById('btn-got-it'));
const guideModal = /** @type {HTMLElement} */ (document.getElementById('guide-modal'));

const btnOpenHistory = /** @type {HTMLButtonElement} */ (document.getElementById('btn-open-history'));
const btnCloseHistory = /** @type {HTMLButtonElement} */ (document.getElementById('btn-close-history'));
const btnClearHistory = /** @type {HTMLButtonElement} */ (document.getElementById('btn-clear-history'));
const historyModal = /** @type {HTMLElement} */ (document.getElementById('history-modal'));
const historyList = /** @type {HTMLElement} */ (document.getElementById('history-list'));
const historyEmpty = /** @type {HTMLElement} */ (document.getElementById('history-empty'));
const historyCounter = /** @type {HTMLElement} */ (document.getElementById('history-counter'));

const toastContainer = /** @type {HTMLElement} */ (document.getElementById('toast-container'));

// State
/** @type {PRMetadata|null} */
let currentPRMetadata = null;
let currentMarkdown = '';
/** @type {number|null} */
let loadingStepTimer = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    fetchHistoryCount();
});

function initEventListeners() {
    prForm.addEventListener('submit', handleFormSubmit);
    btnFetchInfo.addEventListener('click', handleFetchInfo);
    btnSamplePr.addEventListener('click', handleSamplePr);
    btnCopyMarkdown.addEventListener('click', handleCopyMarkdown);
    btnDownloadMd.addEventListener('click', handleDownloadMarkdown);

    // Live Editor update
    markdownEditor.addEventListener('input', handleEditorInput);

    // Tab buttons
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab || 'preview'));
    });

    // Modals
    btnOpenGuide.addEventListener('click', () => showModal(guideModal));
    btnCloseGuide.addEventListener('click', () => hideModal(guideModal));
    btnGotIt.addEventListener('click', () => hideModal(guideModal));

    btnOpenHistory.addEventListener('click', loadAndShowHistory);
    btnCloseHistory.addEventListener('click', () => hideModal(historyModal));
    btnClearHistory.addEventListener('click', handleClearHistory);

    // Close modal on click backdrop
    [guideModal, historyModal].forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) hideModal(modal);
        });
    });

    // ESC to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideModal(guideModal);
            hideModal(historyModal);
        }
    });
}

/**
 * Handle Sample PR click for immediate testing
 */
function handleSamplePr() {
    prUrlInput.value = 'https://github.com/facebook/react/pull/28000';
    showToast('Đã điền link PR mẫu React #28000. Nhấn "Tạo PR Description" để thử nghiệm!', 'info');
}

/**
 * Handle form submit
 * @param {Event} e 
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    const url = prUrlInput.value.trim();
    if (!url) {
        showToast('Vui lòng nhập đường dẫn GitHub PR.', 'error');
        prUrlInput.focus();
        return;
    }

    const model = modelSelect.value;
    const customNotes = customNotesInput.value.trim();

    startLoadingState();

    try {
        const response = await fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pr_url: url,
                model: model,
                provider: 'antigravity',
                custom_notes: customNotes || null,
            }),
        });

        if (!response.ok) {
            stopLoadingState();
            showToast(`Lỗi kết nối máy chủ (${response.status})`, 'error');
            return;
        }

        /** @type {SummarizeResponse} */
        const data = await response.json();
        stopLoadingState();

        if (data.status !== 'success') {
            showToast(data.error_message || 'Có lỗi xảy ra khi tóm tắt PR.', 'error');
            return;
        }

        // Display results
        displayResult(data);
        fetchHistoryCount();
        showToast('Đã tạo PR Description thành công!', 'success');
    } catch (err) {
        stopLoadingState();
        showToast('Lỗi mạng hoặc không thể kết nối đến server.', 'error');
    }
}

/**
 * Fetch PR metadata only without full summary
 */
async function handleFetchInfo() {
    const url = prUrlInput.value.trim();
    if (!url) {
        showToast('Vui lòng nhập đường dẫn GitHub PR.', 'error');
        prUrlInput.focus();
        return;
    }

    btnFetchInfo.disabled = true;
    showToast('Đang tải thông tin PR từ GitHub...', 'info');

    try {
        const res = await fetch('/api/pr/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pr_url: url }),
        });

        btnFetchInfo.disabled = false;
        if (!res.ok) {
            showToast('Không thể kết nối đến server.', 'error');
            return;
        }

        const data = await res.json();
        if (data.status !== 'success' || !data.metadata) {
            showToast(data.error_message || 'Không tìm thấy thông tin PR.', 'error');
            return;
        }

        renderMetadata(data.metadata);
        renderFilesList(data.metadata.files);
        showToast('Đã tải thông tin PR thành công!', 'success');
    } catch (e) {
        btnFetchInfo.disabled = false;
        showToast('Lỗi khi lấy thông tin PR.', 'error');
    }
}

/**
 * Display full generated results
 * @param {SummarizeResponse} data 
 */
function displayResult(data) {
    currentMarkdown = data.summary_markdown;
    markdownEditor.value = currentMarkdown;
    updateWordCharCount(currentMarkdown);

    renderMarkdownPreview(currentMarkdown);
    resultTimeBadge.textContent = `⚡ ${data.execution_time_seconds}s (${data.model_used})`;

    if (data.metadata) {
        renderMetadata(data.metadata);
        renderFilesList(data.metadata.files);
    }

    resultCard.classList.remove('hidden');
    switchTab('preview');

    // Smooth scroll to results
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Render PR metadata card
 * @param {PRMetadata} meta 
 */
function renderMetadata(meta) {
    currentPRMetadata = meta;
    metaRepo.textContent = `${meta.owner}/${meta.repo} #${meta.number}`;
    metaHead.textContent = meta.head_branch || 'head';
    metaBase.textContent = meta.base_branch || 'main';
    metaFilesCount.textContent = `${meta.files.length} files`;
    metaAdditions.textContent = `+${meta.total_additions}`;
    metaDeletions.textContent = `-${meta.total_deletions}`;
    metaTitle.textContent = meta.title;
    metaAuthor.textContent = meta.author ? `@${meta.author}` : '';
    metaCommitsCount.textContent = `${meta.commits.length} commits`;
    metaGithubLink.href = meta.url;

    metadataCard.classList.remove('hidden');
}

/**
 * Render files changed list
 * @param {FileChange[]} files 
 */
function renderFilesList(files) {
    filesListView.innerHTML = '';
    if (!files || files.length === 0) {
        filesListView.innerHTML = '<p class="text-muted" style="padding: 12px;">Không có file thay đổi.</p>';
        return;
    }

    files.forEach(f => {
        const row = document.createElement('div');
        row.className = 'file-row';

        const pathSpan = document.createElement('span');
        pathSpan.className = 'file-path';
        pathSpan.textContent = f.path;

        const pill = document.createElement('div');
        pill.className = 'file-diff-pill';
        pill.innerHTML = `
            <span class="pill-add">+${f.additions}</span>
            <span class="pill-del">-${f.deletions}</span>
        `;

        row.appendChild(pathSpan);
        row.appendChild(pill);
        filesListView.appendChild(row);
    });
}

/**
 * Render markdown string to safe HTML
 * @param {string} markdown 
 */
function renderMarkdownPreview(markdown) {
    if (!markdown) {
        markdownRenderedView.innerHTML = '<p class="text-muted">Chưa có nội dung tóm tắt.</p>';
        return;
    }

    try {
        // Use marked.js if available
        if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
            const rawHtml = marked.parse(markdown);
            const cleanHtml = DOMPurify.sanitize(rawHtml);
            markdownRenderedView.innerHTML = cleanHtml;
            setupInteractiveCheckboxes();
            return;
        }

        // Fallback simple renderer
        markdownRenderedView.innerHTML = fallbackMarkdown(markdown);
    } catch (e) {
        markdownRenderedView.innerHTML = `<pre><code>${escapeHtml(markdown)}</code></pre>`;
    }
}

/**
 * Enable clicking checkboxes in rendered preview to toggle them in editor
 */
function setupInteractiveCheckboxes() {
    const checkboxes = markdownRenderedView.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach((cb) => {
        cb.removeAttribute('disabled');
        cb.style.cursor = 'pointer';
        cb.addEventListener('change', () => {
            // Update editor markdown accordingly
            // For now preview is reactive
        });
    });
}

/**
 * Fallback simple Markdown parser if CDN is inaccessible
 * @param {string} md 
 * @returns {string}
 */
function fallbackMarkdown(md) {
    let html = escapeHtml(md);
    // Headings
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    // Task lists
    html = html.replace(/- \[x\] (.*$)/gim, '<p><input type="checkbox" checked disabled> $1</p>');
    html = html.replace(/- \[ \] (.*$)/gim, '<p><input type="checkbox" disabled> $1</p>');
    // Bullet lists
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    // Code blocks
    html = html.replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>');
    return html;
}

/**
 * Handle live editing in Markdown textarea
 */
function handleEditorInput() {
    currentMarkdown = markdownEditor.value;
    updateWordCharCount(currentMarkdown);
    renderMarkdownPreview(currentMarkdown);
}

/**
 * Switch tabs (preview, editor, files)
 * @param {string} tabName 
 */
function switchTab(tabName) {
    tabButtons.forEach(btn => {
        const isActive = btn.dataset.tab === tabName;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', String(isActive));
    });

    tabPanes.forEach(pane => {
        pane.classList.toggle('active', pane.id === `tab-content-${tabName}`);
    });
}

/**
 * Copy markdown to clipboard
 */
async function handleCopyMarkdown() {
    const textToCopy = markdownEditor.value.trim() || currentMarkdown.trim();
    if (!textToCopy) {
        showToast('Không có nội dung để sao chép.', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(textToCopy);
        copyBtnText.textContent = 'Đã sao chép! ✓';
        showToast('Đã sao chép Markdown vào bộ nhớ tạm!', 'success');
        setTimeout(() => {
            copyBtnText.textContent = 'Sao Chép Markdown';
        }, 2200);
    } catch (err) {
        // Fallback copy
        markdownEditor.select();
        document.execCommand('copy');
        showToast('Đã sao chép vào bộ nhớ tạm!', 'success');
    }
}

/**
 * Download Markdown as .md file
 */
function handleDownloadMarkdown() {
    const text = markdownEditor.value || currentMarkdown;
    if (!text) {
        showToast('Không có nội dung để tải về.', 'error');
        return;
    }

    const prNumber = currentPRMetadata ? `_PR_${currentPRMetadata.number}` : '';
    const filename = `PR_Description${prNumber}.md`;

    const blob = new Blob([text], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToast(`Đã tải về tệp ${filename}`, 'success');
}

/**
 * Loading state animations
 */
function startLoadingState() {
    btnGenerate.disabled = true;
    generateSpinner.style.display = 'inline-block';
    generateIcon.style.display = 'none';
    generateText.textContent = 'Đang phân tích...';

    resultCard.classList.add('hidden');
    loadingCard.classList.remove('hidden');

    resetLoadingSteps();

    // Animate steps realistically
    let step = 1;
    loadingStepTimer = window.setInterval(() => {
        step++;
        if (step === 2) {
            stepFetch.classList.remove('active');
            stepFilter.classList.add('active');
            loaderStatusText.textContent = 'Đang lọc và chuẩn hóa diff...';
        } else if (step === 3) {
            stepFilter.classList.remove('active');
            stepAi.classList.add('active');
            loaderStatusText.textContent = 'Antigravity AI đang tóm tắt (Claude/Gemini)...';
            loaderSubText.textContent = 'Trích xuất logic What, Why, QA Checklist, Types of changes...';
        }
    }, 1800);
}

function stopLoadingState() {
    btnGenerate.disabled = false;
    generateSpinner.style.display = 'none';
    generateIcon.style.display = 'inline-block';
    generateText.textContent = 'Tạo PR Description';

    loadingCard.classList.add('hidden');
    if (loadingStepTimer) {
        clearInterval(loadingStepTimer);
        loadingStepTimer = null;
    }
}

function resetLoadingSteps() {
    [stepFetch, stepFilter, stepAi, stepDone].forEach(s => s.classList.remove('active'));
    stepFetch.classList.add('active');
    loaderStatusText.textContent = 'Đang kết nối GitHub và tải dữ liệu PR...';
    loaderSubText.textContent = 'Thu thập danh sách commits, files và diff mã nguồn...';
}

/**
 * History Management
 */
async function fetchHistoryCount() {
    try {
        const res = await fetch('/api/history');
        if (!res.ok) return;
        const data = await res.json();
        if (data.status === 'success' && data.history) {
            historyCounter.textContent = String(data.history.length);
        }
    } catch (e) {
        // silent fail
    }
}

async function loadAndShowHistory() {
    showModal(historyModal);
    historyList.innerHTML = '<p class="text-muted" style="text-align: center; padding: 20px;">Đang tải...</p>';

    try {
        const res = await fetch('/api/history');
        if (!res.ok) throw new Error();
        const data = await res.json();

        /** @type {HistoryItem[]} */
        const items = data.history || [];

        if (items.length === 0) {
            historyList.innerHTML = '';
            historyEmpty.classList.remove('hidden');
            return;
        }

        historyEmpty.classList.add('hidden');
        historyList.innerHTML = '';

        items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'history-item-card';

            const info = document.createElement('div');
            info.className = 'history-item-info';
            info.innerHTML = `
                <div class="history-item-title">${escapeHtml(item.pr_title)}</div>
                <div class="history-item-meta">
                    <span>${escapeHtml(item.model_used)}</span>
                    <span>•</span>
                    <span>${escapeHtml(item.created_at)}</span>
                </div>
            `;

            const btnLoad = document.createElement('button');
            btnLoad.className = 'btn btn-secondary btn-sm';
            btnLoad.textContent = 'Mở lại';
            btnLoad.addEventListener('click', () => {
                prUrlInput.value = item.pr_url;
                currentMarkdown = item.summary_markdown;
                markdownEditor.value = currentMarkdown;
                renderMarkdownPreview(currentMarkdown);
                updateWordCharCount(currentMarkdown);
                resultTimeBadge.textContent = `Lịch sử • ${item.created_at}`;
                resultCard.classList.remove('hidden');
                switchTab('preview');
                hideModal(historyModal);
                resultCard.scrollIntoView({ behavior: 'smooth' });
                showToast('Đã tải lại PR từ lịch sử!', 'success');
            });

            card.appendChild(info);
            card.appendChild(btnLoad);
            historyList.appendChild(card);
        });
    } catch (e) {
        historyList.innerHTML = '<p class="text-muted" style="text-align: center;">Không thể tải lịch sử.</p>';
    }
}

async function handleClearHistory() {
    if (!confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử tóm tắt?')) {
        return;
    }

    try {
        const res = await fetch('/api/history', { method: 'DELETE' });
        if (!res.ok) throw new Error();
        historyList.innerHTML = '';
        historyEmpty.classList.remove('hidden');
        historyCounter.textContent = '0';
        showToast('Đã xóa toàn bộ lịch sử tóm tắt.', 'success');
    } catch (e) {
        showToast('Không thể xóa lịch sử.', 'error');
    }
}

/**
 * Toast notifications
 * @param {string} msg 
 * @param {'success'|'error'|'info'} type 
 */
function showToast(msg, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;

    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = '0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

/**
 * Modals
 * @param {HTMLElement} modal 
 */
function showModal(modal) {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function hideModal(modal) {
    modal.classList.add('hidden');
    document.body.style.overflow = '';
}

/**
 * Utilities
 * @param {string} text 
 */
function updateWordCharCount(text) {
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    wordCharCount.textContent = `${words} từ • ${chars} ký tự`;
}

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
