/**
 * 연금복권 패턴 분석 클라이언트사이드 JavaScript
 */

class LotteryAnalysisApp {
    constructor() {
        this.currentTaskId = null;
        this.checkInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // 페이지 로드 완료 시
        document.addEventListener('DOMContentLoaded', () => {
            this.updateSystemStatus();
        });

        // 윈도우 리사이즈 시 차트 반응형 처리
        window.addEventListener('resize', this.debounce(() => {
            this.resizeCharts();
        }, 250));

        // 키보드 단축키
        document.addEventListener('keydown', (e) => {
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
                }
            }
        });
    }

    // 작업 실행
    async executeAction(action) {
        if (this.currentTaskId) {
            this.showNotification('이미 실행 중인 작업이 있습니다.', 'warning');
            return;
        }

        this.showLoading(true);
        this.updateProgress(0, `${this.getActionName(action)} 준비 중...`);

        try {
            const response = await fetch(`/api/execute/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.status === 'started') {
                this.currentTaskId = data.task_id;
                this.showNotification(`${this.getActionName(action)} 작업이 시작되었습니다.`, 'info');
                this.startTaskMonitoring();
            } else {
                this.showLoading(false);
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            this.showLoading(false);
            this.showNotification('작업 실행 중 오류가 발생했습니다: ' + error.message, 'error');
        }
    }

    // 작업 모니터링 시작
    startTaskMonitoring() {
        if (this.checkInterval) clearInterval(this.checkInterval);

        let progress = 0;
        this.checkInterval = setInterval(async () => {
            if (this.currentTaskId) {
                await this.checkTaskStatus();

                // 진행률 시뮬레이션 (실제 진행률이 없으므로)
                progress += Math.random() * 10;
                if (progress > 90) progress = 90;
                this.updateProgress(progress);
            }
        }, 2000);
    }

    // 작업 상태 확인
    async checkTaskStatus() {
        try {
            const response = await fetch(`/api/task/${this.currentTaskId}`);
            const data = await response.json();

            if (data.status === 'completed') {
                this.showLoading(false);
                this.updateProgress(100, '작업 완료!');
                this.showNotification('작업이 성공적으로 완료되었습니다!', 'success');
                this.currentTaskId = null;
                clearInterval(this.checkInterval);

                // 결과 업데이트
                setTimeout(() => {
                    this.refreshData();
                }, 1000);

            } else if (data.status === 'failed') {
                this.showLoading(false);
                this.updateProgress(0, '작업 실패');
                this.showNotification('작업 실행에 실패했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
                this.currentTaskId = null;
                clearInterval(this.checkInterval);
            }
        } catch (error) {
            console.error('작업 상태 확인 오류:', error);
        }
    }

    // 시스템 상태 업데이트
    async updateSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();

            this.displaySystemStatus(status);
        } catch (error) {
            console.error('시스템 상태 확인 오류:', error);
        }
    }

    // 시스템 상태 표시
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

    // 차트 로드
    async loadCharts() {
        try {
            const response = await fetch('/api/charts');
            const charts = await response.json();

            this.displayCharts(charts);
        } catch (error) {
            console.error('차트 로드 오류:', error);
        }
    }

    // 차트 표시
    displayCharts(charts) {
        const container = document.getElementById('charts-container');
        if (!container) return;

        if (charts.length === 0) {
            container.innerHTML = `
                <div class="no-data">
                    <h4>📈 차트 데이터가 없습니다</h4>
                    <p>분석을 실행하여 차트를 생성해주세요.</p>
                </div>
            `;
            return;
        }

        let chartsHtml = '';
        charts.forEach(chart => {
            chartsHtml += `
                <div class="chart-wrapper">
                    <div class="chart-title">${chart.title}</div>
                    <div class="chart-container">
                        <img src="/charts/${chart.filename}?v=${Date.now()}"
                             alt="${chart.title}"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                        <div style="display: none; padding: 20px; background: #f8f9fa; border-radius: 6px; color: #6c757d;">
                            차트를 로드할 수 없습니다.
                        </div>
                    </div>
                    ${chart.modified ? `<small style="color: #6c757d;">생성: ${chart.modified}</small>` : ''}
                </div>
            `;
        });

        container.innerHTML = chartsHtml;
    }

    // 초기 데이터 로드
    async loadInitialData() {
        await this.updateSystemStatus();

        // 차트 컨테이너가 있으면 차트 로드
        if (document.getElementById('charts-container')) {
            await this.loadCharts();
        }
    }

    // 데이터 새로고침
    async refreshData() {
        this.showNotification('데이터를 새로고침하는 중...', 'info');

        await this.updateSystemStatus();

        // 현재 페이지에 따라 적절한 데이터 새로고침
        const currentPath = window.location.pathname;

        if (currentPath.includes('dashboard') || currentPath.includes('charts')) {
            await this.loadCharts();
        }

        this.showNotification('데이터가 업데이트되었습니다.', 'success');
    }

    // 로딩 표시
    showLoading(show) {
        const loadingElements = document.querySelectorAll('.loading, .spinner');
        loadingElements.forEach(element => {
            element.style.display = show ? 'block' : 'none';
        });
    }

    // 진행률 업데이트
    updateProgress(percentage, message = '') {
        const progressBar = document.querySelector('.progress-bar');
        const progressMessage = document.getElementById('progress-message');

        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.textContent = `${Math.round(percentage)}%`;
        }

        if (progressMessage && message) {
            progressMessage.textContent = message;
        }
    }

    // 알림 표시
    showNotification(message, type = 'info', duration = 5000) {
        // 기존 알림 제거
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());

        // 새 알림 생성
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // 애니메이션으로 표시
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // 자동 제거
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    // 차트 반응형 처리
    resizeCharts() {
        const charts = document.querySelectorAll('.chart-container img');
        charts.forEach(chart => {
            // 차트 크기 재조정 로직
            chart.style.maxWidth = '100%';
            chart.style.height = 'auto';
        });
    }

    // 작업명 변환
    getActionName(action) {
        const names = {
            'crawl': '데이터 크롤링',
            'analyze': '기본 분석',
            'number_analyze': '번호별 분석',
            'pattern_analyze': '패턴 분석'
        };
        return names[action] || action;
    }

    // 디바운스 유틸리티
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

    // 로컬 스토리지 유틸리티 (설정 저장용)
    saveSettings(key, value) {
        try {
            localStorage.setItem(`lottery_analysis_${key}`, JSON.stringify(value));
        } catch (error) {
            console.warn('설정 저장 실패:', error);
        }
    }

    loadSettings(key, defaultValue = null) {
        try {
            const stored = localStorage.getItem(`lottery_analysis_${key}`);
            return stored ? JSON.parse(stored) : defaultValue;
        } catch (error) {
            console.warn('설정 로드 실패:', error);
            return defaultValue;
        }
    }
}

// 전역 인스턴스 생성
const lotteryApp = new LotteryAnalysisApp();

// 전역 함수들 (템플릿에서 사용)
window.executeAction = function(action) {
    if (typeof lotteryApp !== 'undefined') {
        lotteryApp.executeAction(action);
    } else {
        console.error('lotteryApp이 초기화되지 않았습니다.');
    }
}

window.refreshStatus = function() {
    if (typeof lotteryApp !== 'undefined') {
        lotteryApp.updateSystemStatus();
    }
}

window.refreshData = function() {
    if (typeof lotteryApp !== 'undefined') {
        lotteryApp.refreshData();
    }
}

// 탭 기능 (대시보드용)
window.showTab = function(tabName) {
    const clickedElement = event.target;

    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

    clickedElement.classList.add('active');
    const targetPane = document.getElementById(tabName);
    if (targetPane) {
        targetPane.classList.add('active');
    }

    if (tabName === 'charts' && typeof lotteryApp !== 'undefined') {
        lotteryApp.loadCharts();
    }
}

// 패턴 탭 기능
window.showPatternTab = function(tabName) {
    const clickedElement = event.target;

    document.querySelectorAll('.pattern-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.pattern-pane').forEach(pane => pane.classList.remove('active'));

    clickedElement.classList.add('active');
    const targetPane = document.getElementById(tabName);
    if (targetPane) {
        targetPane.classList.add('active');
    }
}