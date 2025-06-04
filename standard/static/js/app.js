/**
 * 연금복권 패턴 분석 시스템 - 클라이언트사이드 JavaScript
 *
 * 주요 기능:
 * - 작업 실행 및 모니터링
 * - 실시간 상태 업데이트
 * - 차트 로드 및 관리
 * - 사용자 인터페이스 제어
 * - 알림 시스템
 */

class LotteryAnalysisApp {
    constructor() {
        this.currentTaskId = null;
        this.checkInterval = null;
        this.statusUpdateInterval = null;
        this.settings = this.loadSettings();
        this.notifications = [];

        this.init();
    }

    /**
     * 애플리케이션 초기화
     */
    init() {
        console.log('🎰 연금복권 패턴 분석 시스템 초기화');

        this.setupEventListeners();
        this.initializeUI();
        this.startStatusMonitoring();
        this.loadInitialData();

        console.log('✅ 초기화 완료');
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 페이지 로드 완료 시
        document.addEventListener('DOMContentLoaded', () => {
            this.updateSystemStatus();
            this.initializeTooltips();
        });

        // 윈도우 리사이즈 시 차트 반응형 처리
        window.addEventListener('resize', this.debounce(() => {
            this.resizeCharts();
        }, 250));

        // 페이지 가시성 변경 시
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseStatusMonitoring();
            } else {
                this.resumeStatusMonitoring();
                this.updateSystemStatus();
            }
        });

        // 키보드 단축키
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // 오류 처리
        window.addEventListener('error', (e) => {
            console.error('JavaScript 오류:', e.error);
            this.showNotification('시스템 오류가 발생했습니다.', 'error');
        });

        // 네트워크 상태 감지
        window.addEventListener('online', () => {
            this.showNotification('인터넷 연결이 복구되었습니다.', 'success', 3000);
            this.updateSystemStatus();
        });

        window.addEventListener('offline', () => {
            this.showNotification('인터넷 연결이 끊어졌습니다.', 'warning', 5000);
        });
    }

    /**
     * UI 초기화
     */
    initializeUI() {
        // 로딩 상태 초기화
        this.hideLoading();

        // 진행률 숨김
        this.hideProgress();

        // 알림 컨테이너 확인/생성
        this.ensureAlertsContainer();

        // 차트 컨테이너 확인
        this.initializeChartContainers();
    }

    /**
     * 키보드 단축키 처리
     */
    handleKeyboardShortcuts(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'r':
                    e.preventDefault();
                    this.refreshData();
                    break;
                case '1':
                    e.preventDefault();
                    this.executeAction('crawl');
                    break;
                case '2':
                    e.preventDefault();
                    this.executeAction('analyze');
                    break;
                case '3':
                    e.preventDefault();
                    this.executeAction('number_analyze');
                    break;
                case '4':
                    e.preventDefault();
                    this.executeAction('pattern_analyze');
                    break;
                case 's':
                    e.preventDefault();
                    this.saveCurrentState();
                    break;
            }
        }

        // ESC 키로 진행 중인 작업 취소 (UI만)
        if (e.key === 'Escape' && this.currentTaskId) {
            this.showCancelDialog();
        }
    }

    /**
     * 작업 실행
     */
    async executeAction(action, lotteryType = '720') {
        if (this.currentTaskId) {
            this.showNotification('이미 실행 중인 작업이 있습니다.', 'warning');
            return false;
        }

        this.showLoading(true);
        this.showProgress(true, `${this.getActionName(action)} 준비 중...`, 0);

        try {
            const response = await this.makeRequest('/api/execute/' + action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ lottery_type: lotteryType })
            });

            const data = await response.json();

            if (data.status === 'started') {
                this.currentTaskId = data.task_id;
                this.updateTaskId(data.task_id);

                const typeName = lotteryType === '720' ? '720+' : '520';
                this.showNotification(`${this.getActionName(action)} 작업이 시작되었습니다. (연금복권${typeName})`, 'info');

                this.startTaskMonitoring();
                this.logAction(action, lotteryType, 'started');

                return true;
            } else {
                this.hideLoading();
                this.hideProgress();
                this.showNotification(data.message, 'error');
                return false;
            }
        } catch (error) {
            this.hideLoading();
            this.hideProgress();
            this.showNotification('작업 실행 중 오류가 발생했습니다: ' + error.message, 'error');
            console.error('Execute action error:', error);
            return false;
        }
    }

    /**
     * 작업 모니터링 시작
     */
    startTaskMonitoring() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }

        let progress = 0;
        let progressSpeed = Math.random() * 3 + 1; // 1-4 사이의 속도

        this.checkInterval = setInterval(async () => {
            if (this.currentTaskId) {
                try {
                    await this.checkTaskStatus();

                    // 진행률 시뮬레이션 (실제 진행률이 없으므로)
                    if (progress < 90) {
                        progress += progressSpeed;
                        progressSpeed *= 0.98; // 점진적으로 느려짐

                        if (progress > 90) progress = 90;
                        this.updateProgress(progress, '작업 진행 중...');
                    }
                } catch (error) {
                    console.error('Task monitoring error:', error);
                }
            }
        }, 2000);
    }

    /**
     * 작업 상태 확인
     */
    async checkTaskStatus() {
        try {
            const response = await this.makeRequest(`/api/task/${this.currentTaskId}`);
            const data = await response.json();

            switch (data.status) {
                case 'completed':
                    this.handleTaskCompleted(data);
                    break;
                case 'failed':
                    this.handleTaskFailed(data);
                    break;
                case 'running':
                    // 계속 진행 중
                    break;
                default:
                    console.warn('Unknown task status:', data.status);
            }
        } catch (error) {
            console.error('작업 상태 확인 오류:', error);
        }
    }

    /**
     * 작업 완료 처리
     */
    handleTaskCompleted(data) {
        this.hideLoading();
        this.updateProgress(100, '작업 완료!');
        this.showNotification('작업이 성공적으로 완료되었습니다!', 'success');

        this.currentTaskId = null;
        this.clearTaskMonitoring();

        // 결과 업데이트
        setTimeout(() => {
            this.refreshData();
            this.hideProgress();
        }, 2000);

        // 성공 로그
        this.logTaskCompletion('success', data);

        // 완료 사운드 (선택사항)
        this.playNotificationSound('success');
    }

    /**
     * 작업 실패 처리
     */
    handleTaskFailed(data) {
        this.hideLoading();
        this.hideProgress();
        this.showNotification('작업 실행에 실패했습니다: ' + (data.error || '알 수 없는 오류'), 'error');

        this.currentTaskId = null;
        this.clearTaskMonitoring();

        // 실패 로그
        this.logTaskCompletion('failed', data);

        // 오류 상세 정보 표시 (개발 모드)
        if (this.settings.debugMode && data.error) {
            console.error('Task failed with error:', data.error);
        }
    }

    /**
     * 작업 모니터링 정리
     */
    clearTaskMonitoring() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }

    /**
     * 시스템 상태 업데이트
     */
    async updateSystemStatus() {
        try {
            const response = await this.makeRequest('/api/status');
            const status = await response.json();

            this.displaySystemStatus(status);
            this.updateStatusIndicators(status);

            return status;
        } catch (error) {
            console.error('시스템 상태 확인 오류:', error);
            this.showNotification('상태 업데이트에 실패했습니다.', 'error', 3000);
            return null;
        }
    }

    /**
     * 시스템 상태 표시
     */
    displaySystemStatus(status) {
        const statusElements = {
            'crawl-status': status.crawl_data_exists,
            'basic-analysis-status': status.basic_analysis_exists,
            'number-analysis-status': status.number_analysis_exists,
            'pattern-analysis-status': status.pattern_analysis_exists
        };

        Object.entries(statusElements).forEach(([elementId, exists]) => {
            const element = document.getElementById(elementId);
            if (element) {
                element.className = `status-indicator ${exists ? 'status-success' : 'status-error'}`;
                element.title = exists ? '완료됨' : '미완료';
            }
        });

        // 실행 중인 작업 표시
        const runningTasksElement = document.getElementById('running-tasks');
        if (runningTasksElement) {
            runningTasksElement.textContent = status.running_tasks || 0;
            runningTasksElement.className = status.running_tasks > 0 ? 'status-warning' : 'status-success';
        }
    }

    /**
     * 상태 지시자 업데이트
     */
    updateStatusIndicators(status) {
        // 네비게이션 메뉴의 상태 업데이트
        const navItems = {
            'crawl': status.crawl_data_exists,
            'analyze': status.basic_analysis_exists,
            'number_analyze': status.number_analysis_exists,
            'pattern_analyze': status.pattern_analysis_exists
        };

        Object.entries(navItems).forEach(([action, completed]) => {
            const links = document.querySelectorAll(`a[onclick*="${action}"]`);
            links.forEach(link => {
                if (completed) {
                    link.classList.add('completed');
                    link.title = '완료됨';
                } else {
                    link.classList.remove('completed');
                    link.title = '미완료';
                }
            });
        });
    }

    /**
     * 차트 로드
     */
    async loadCharts() {
        const container = document.getElementById('charts-container');
        if (!container) return;

        try {
            this.showChartLoading(container);

            const response = await this.makeRequest('/api/charts');
            const charts = await response.json();

            this.displayCharts(charts, container);
        } catch (error) {
            console.error('차트 로드 오류:', error);
            this.showChartError(container, error.message);
        }
    }

    /**
     * 차트 표시
     */
    displayCharts(charts, container) {
        if (charts.length === 0) {
            container.innerHTML = `
                <div class="no-data">
                    <h4>📈 차트 데이터가 없습니다</h4>
                    <p>분석을 실행하여 차트를 생성해주세요.</p>
                    <button class="btn btn-primary" onclick="lotteryApp.executeAction('analyze')">
                        📈 분석 시작
                    </button>
                </div>
            `;
            return;
        }

        let chartsHtml = '<div class="chart-grid">';
        charts.forEach((chart, index) => {
            chartsHtml += `
                <div class="chart-wrapper" data-chart="${chart.filename}">
                    <div class="chart-title">${chart.title}</div>
                    <div class="chart-container">
                        <img src="/charts/${chart.filename}?v=${Date.now()}"
                             alt="${chart.title}"
                             loading="lazy"
                             onload="this.style.display='block'; this.nextElementSibling.style.display='none';"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
                             style="display: none;">
                        <div class="chart-loading" style="display: block;">
                            <div class="spinner"></div>
                            <p>차트 로드 중...</p>
                        </div>
                        <div class="chart-error" style="display: none;">
                            <p>차트를 로드할 수 없습니다.</p>
                            <button class="btn btn-sm btn-secondary" onclick="lotteryApp.reloadChart('${chart.filename}')">
                                다시 시도
                            </button>
                        </div>
                    </div>
                    ${chart.modified ? `<small style="color: #6c757d; margin-top: 10px; display: block;">생성: ${chart.modified}</small>` : ''}
                </div>
            `;
        });
        chartsHtml += '</div>';

        container.innerHTML = chartsHtml;

        // 차트 로드 애니메이션
        this.animateChartLoad(container);
    }

    /**
     * 차트 로드 애니메이션
     */
    animateChartLoad(container) {
        const chartWrappers = container.querySelectorAll('.chart-wrapper');
        chartWrappers.forEach((wrapper, index) => {
            wrapper.style.opacity = '0';
            wrapper.style.transform = 'translateY(20px)';

            setTimeout(() => {
                wrapper.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                wrapper.style.opacity = '1';
                wrapper.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    /**
     * 개별 차트 재로드
     */
    async reloadChart(filename) {
        const chartWrapper = document.querySelector(`[data-chart="${filename}"]`);
        if (!chartWrapper) return;

        const img = chartWrapper.querySelector('img');
        const loading = chartWrapper.querySelector('.chart-loading');
        const error = chartWrapper.querySelector('.chart-error');

        if (img && loading && error) {
            img.style.display = 'none';
            error.style.display = 'none';
            loading.style.display = 'block';

            img.src = `/charts/${filename}?v=${Date.now()}`;
        }
    }

    /**
     * 차트 로딩 표시
     */
    showChartLoading(container) {
        container.innerHTML = `
            <div class="loading-chart">
                <div class="spinner"></div>
                <p>차트를 로드하는 중입니다...</p>
            </div>
        `;
    }

    /**
     * 차트 오류 표시
     */
    showChartError(container, errorMessage) {
        container.innerHTML = `
            <div class="no-data">
                <h4>❌ 차트 로드 실패</h4>
                <p>차트를 불러오는 중 오류가 발생했습니다.</p>
                <small style="color: #6c757d;">${errorMessage}</small>
                <div style="margin-top: 15px;">
                    <button class="btn btn-secondary" onclick="lotteryApp.loadCharts()">
                        🔄 다시 시도
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * 데이터 새로고침
     */
    async refreshData() {
        this.showNotification('데이터를 새로고침하는 중...', 'info', 2000);

        try {
            await this.updateSystemStatus();

            // 현재 페이지에 따라 적절한 데이터 새로고침
            const currentPath = window.location.pathname;

            if (currentPath.includes('dashboard')) {
                // 대시보드 데이터 새로고침
                await this.refreshDashboard();
            } else if (currentPath.includes('patterns')) {
                // 패턴 데이터 새로고침
                await this.refreshPatterns();
            } else if (currentPath.includes('charts')) {
                // 차트 새로고침
                await this.loadCharts();
            }

            this.showNotification('데이터가 업데이트되었습니다.', 'success', 3000);
        } catch (error) {
            console.error('Data refresh error:', error);
            this.showNotification('데이터 새로고침에 실패했습니다.', 'error');
        }
    }

    /**
     * 대시보드 새로고침
     */
    async refreshDashboard() {
        // 대시보드 특화 로직 구현
        if (typeof loadDashboardCharts === 'function') {
            await loadDashboardCharts();
        }
    }

    /**
     * 패턴 페이지 새로고침
     */
    async refreshPatterns() {
        // 패턴 페이지 특화 로직 구현
        const chartImages = document.querySelectorAll('#charts img');
        chartImages.forEach(img => {
            if (img.src) {
                const originalSrc = img.src.split('?')[0];
                img.src = originalSrc + '?v=' + Date.now();
            }
        });
    }

    /**
     * 로딩 표시/숨김
     */
    showLoading(show) {
        const loadingElements = document.querySelectorAll('.loading, .spinner');
        const loadingElement = document.getElementById('loading');

        if (loadingElement) {
            loadingElement.style.display = show ? 'block' : 'none';
        }

        loadingElements.forEach(element => {
            element.style.display = show ? 'block' : 'none';
        });
    }

    hideLoading() {
        this.showLoading(false);
    }

    /**
     * 진행률 표시/숨김
     */
    showProgress(show, message = '', percentage = 0) {
        const progressSection = document.getElementById('progress-section');

        if (progressSection) {
            progressSection.style.display = show ? 'block' : 'none';
        }

        if (show) {
            this.updateProgress(percentage, message);
        }
    }

    hideProgress() {
        this.showProgress(false);
    }

    /**
     * 진행률 업데이트
     */
    updateProgress(percentage, message = '') {
        const progressBar = document.getElementById('progress-bar');
        const progressMessage = document.getElementById('progress-message');
        const progressPercentage = document.getElementById('progress-percentage');

        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.textContent = `${Math.round(percentage)}%`;
        }

        if (progressMessage && message) {
            progressMessage.textContent = message;
        }

        if (progressPercentage) {
            progressPercentage.textContent = `${Math.round(percentage)}%`;
        }
    }

    /**
     * 작업 ID 업데이트
     */
    updateTaskId(taskId) {
        const taskIdElement = document.getElementById('current-task-id');
        if (taskIdElement) {
            taskIdElement.textContent = taskId || '-';
        }
    }

    /**
     * 알림 표시
     */
    showNotification(message, type = 'info', duration = 5000) {
        // 기존 알림 제거 (같은 타입)
        this.clearNotificationsOfType(type);

        // 새 알림 생성
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // 닫기 버튼 추가
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            position: absolute;
            top: 5px;
            right: 10px;
            background: none;
            border: none;
            color: inherit;
            font-size: 18px;
            cursor: pointer;
            opacity: 0.7;
        `;
        closeBtn.onclick = () => this.removeNotification(notification);
        notification.appendChild(closeBtn);

        document.body.appendChild(notification);
        this.notifications.push(notification);

        // 애니메이션으로 표시
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // 자동 제거
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification);
            }, duration);
        }

        return notification;
    }

    /**
     * 알림 제거
     */
    removeNotification(notification) {
        if (notification && notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                // 배열에서 제거
                const index = this.notifications.indexOf(notification);
                if (index > -1) {
                    this.notifications.splice(index, 1);
                }
            }, 300);
        }
    }

    /**
     * 특정 타입의 알림 제거
     */
    clearNotificationsOfType(type) {
        const notifications = document.querySelectorAll(`.notification-${type}`);
        notifications.forEach(notification => {
            this.removeNotification(notification);
        });
    }

    /**
     * 차트 반응형 처리
     */
    resizeCharts() {
        const charts = document.querySelectorAll('.chart-container img');
        charts.forEach(chart => {
            chart.style.maxWidth = '100%';
            chart.style.height = 'auto';
        });
    }

    /**
     * 상태 모니터링 시작
     */
    startStatusMonitoring() {
        // 30초마다 상태 업데이트
        this.statusUpdateInterval = setInterval(() => {
            if (!document.hidden) {
                this.updateSystemStatus();
            }
        }, 30000);
    }

    /**
     * 상태 모니터링 일시정지
     */
    pauseStatusMonitoring() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
        }
    }

    /**
     * 상태 모니터링 재개
     */
    resumeStatusMonitoring() {
        this.startStatusMonitoring();
    }

    /**
     * 초기 데이터 로드
     */
    async loadInitialData() {
        await this.updateSystemStatus();

        // 차트 컨테이너가 있으면 차트 로드
        if (document.getElementById('charts-container')) {
            await this.loadCharts();
        }
    }

    /**
     * 유틸리티 함수들
     */
    getActionName(action) {
        const names = {
            'crawl': '데이터 크롤링',
            'analyze': '기본 분석',
            'number_analyze': '번호별 분석',
            'pattern_analyze': '패턴 분석'
        };
        return names[action] || action;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * HTTP 요청 래퍼
     */
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        const response = await fetch(url, defaultOptions);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response;
    }

    /**
     * 설정 관리
     */
    saveSettings() {
        try {
            localStorage.setItem('lottery_analysis_settings', JSON.stringify(this.settings));
        } catch (error) {
            console.warn('설정 저장 실패:', error);
        }
    }

    loadSettings() {
        try {
            const stored = localStorage.getItem('lottery_analysis_settings');
            return stored ? JSON.parse(stored) : this.getDefaultSettings();
        } catch (error) {
            console.warn('설정 로드 실패:', error);
            return this.getDefaultSettings();
        }
    }

    getDefaultSettings() {
        return {
            debugMode: false,
            autoRefresh: true,
            notificationSound: false,
            theme: 'light'
        };
    }

    /**
     * 로깅 및 분석
     */
    logAction(action, lotteryType, status) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            action,
            lotteryType,
            status,
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        console.log('Action logged:', logEntry);

        // 향후 분석을 위한 로그 저장 (선택사항)
        this.saveActionLog(logEntry);
    }

    logTaskCompletion(status, data) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            taskId: this.currentTaskId,
            status,
            duration: data.end_time && data.start_time ?
                new Date(data.end_time) - new Date(data.start_time) : null,
            error: data.error || null
        };

        console.log('Task completion logged:', logEntry);
    }

    saveActionLog(logEntry) {
        try {
            const logs = JSON.parse(localStorage.getItem('lottery_action_logs') || '[]');
            logs.push(logEntry);

            // 최대 100개 로그만 유지
            if (logs.length > 100) {
                logs.splice(0, logs.length - 100);
            }

            localStorage.setItem('lottery_action_logs', JSON.stringify(logs));
        } catch (error) {
            console.warn('로그 저장 실패:', error);
        }
    }

    /**
     * 현재 상태 저장
     */
    saveCurrentState() {
        const state = {
            currentPath: window.location.pathname,
            timestamp: new Date().toISOString(),
            scrollPosition: window.scrollY
        };

        try {
            sessionStorage.setItem('lottery_app_state', JSON.stringify(state));
            this.showNotification('현재 상태가 저장되었습니다.', 'success', 2000);
        } catch (error) {
            console.warn('상태 저장 실패:', error);
        }
    }

    /**
     * 알림 컨테이너 확인/생성
     */
    ensureAlertsContainer() {
        if (!document.getElementById('alerts')) {
            const alertsDiv = document.createElement('div');
            alertsDiv.id = 'alerts';
            alertsDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
            `;
            document.body.appendChild(alertsDiv);
        }
    }

    /**
     * 차트 컨테이너 초기화
     */
    initializeChartContainers() {
        const containers = document.querySelectorAll('[id$="-container"]');
        containers.forEach(container => {
            if (!container.hasAttribute('data-initialized')) {
                container.setAttribute('data-initialized', 'true');
                // 필요한 초기화 로직
            }
        });
    }

    /**
     * 툴팁 초기화
     */
    initializeTooltips() {
        const tooltipElements = document.querySelectorAll('[title]');
        tooltipElements.forEach(element => {
            // 간단한 툴팁 기능
            element.addEventListener('mouseenter', (e) => {
                // 툴팁 로직 구현 (선택사항)
            });
        });
    }

    /**
     * 취소 다이얼로그 표시
     */
    showCancelDialog() {
        const confirmed = confirm('진행 중인 작업을 취소하시겠습니까?\n(실제 작업은 계속 진행됩니다)');
        if (confirmed) {
            this.cancelCurrentTask();
        }
    }

    /**
     * 현재 작업 취소 (UI만)
     */
    cancelCurrentTask() {
        this.currentTaskId = null;
        this.clearTaskMonitoring();
        this.hideLoading();
        this.hideProgress();
        this.showNotification('작업 모니터링이 중단되었습니다.', 'warning');
    }

    /**
     * 알림음 재생 (선택사항)
     */
    playNotificationSound(type) {
        if (!this.settings.notificationSound) return;

        try {
            // 간단한 비프음 (Web Audio API 사용)
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = type === 'success' ? 800 : 400;
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (error) {
            console.warn('알림음 재생 실패:', error);
        }
    }
}

// 전역 인스턴스 생성
const lotteryApp = new LotteryAnalysisApp();

// 전역 함수들 (템플릿에서 사용)
window.executeAction = function(action, lotteryType = '720') {
    return lotteryApp.executeAction(action, lotteryType);
};

window.refreshStatus = function() {
    return lotteryApp.updateSystemStatus();
};

window.refreshData = function() {
    return lotteryApp.refreshData();
};

// 탭 기능들
window.showTab = function(tabName) {
    const clickedElement = event?.target;
    if (!clickedElement) return;

    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

    clickedElement.classList.add('active');
    const targetPane = document.getElementById(tabName);
    if (targetPane) {
        targetPane.classList.add('active');
    }

    if (tabName === 'charts') {
        lotteryApp.loadCharts();
    }
};

window.showPatternTab = function(tabName) {
    const clickedElement = event?.target;
    if (!clickedElement) return;

    document.querySelectorAll('.pattern-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.pattern-pane').forEach(pane => pane.classList.remove('active'));

    clickedElement.classList.add('active');
    const targetPane = document.getElementById(tabName);
    if (targetPane) {
        targetPane.classList.add('active');
    }
};

// 애플리케이션 정보
window.lotteryApp = lotteryApp;

console.log('🎰 연금복권 패턴 분석 시스템 JavaScript 로드 완료');
console.log('📋 사용 가능한 키보드 단축키:');
console.log('   Ctrl+1: 데이터 크롤링');
console.log('   Ctrl+2: 기본 분석');
console.log('   Ctrl+3: 번호별 분석');
console.log('   Ctrl+4: 패턴 분석');
console.log('   Ctrl+R: 데이터 새로고침');
console.log('   Ctrl+S: 현재 상태 저장');
console.log('   ESC: 작업 취소 (UI만)');