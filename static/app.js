// Z哥选股策略 Dashboard JavaScript Application

class StockDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/api';
        this.currentData = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.charts = {};
        
        this.init();
    }
    
    async init() {
        console.log('Initializing dashboard...');
        try {
            console.log('Setting up event listeners...');
            this.setupEventListeners();
            console.log('Initializing charts...');
            this.initializeCharts();
            console.log('Loading initial data...');
            await this.loadInitialData();
            console.log('Updating last update time...');
            this.updateLastUpdateTime();
            console.log('Dashboard initialization complete');
        } catch (error) {
            console.error('Initialization error:', error);
            this.showError('初始化失败: ' + error.message);
        }
    }
    
    async loadInitialData() {
        await Promise.all([
            this.loadStats(),
            this.loadLatestSelections()
        ]);
    }
    
    async loadStats() {
        try {
            console.log('Loading stats from:', `${this.apiBaseUrl}/stats`);
            const response = await fetch(`${this.apiBaseUrl}/stats`);
            console.log('Stats response status:', response.status);
            if (!response.ok) throw new Error(`Failed to load stats: ${response.status} ${response.statusText}`);

            const stats = await response.json();
            console.log('Stats data:', stats);
            this.updateStatsCards(stats);
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showError('加载统计数据失败: ' + error.message);
        }
    }
    
    async loadLatestSelections() {
        try {
            console.log('Loading selections from:', `${this.apiBaseUrl}/selections/latest?limit=100`);
            const response = await fetch(`${this.apiBaseUrl}/selections/latest?limit=100`);
            console.log('Selections response status:', response.status);
            if (!response.ok) throw new Error(`Failed to load selections: ${response.status} ${response.statusText}`);

            const data = await response.json();
            console.log('Selections data length:', data.length);
            console.log('Sample selection data:', data.slice(0, 2));
            this.currentData = data;
            this.filteredData = [...data];
            this.updateTable();
            this.updateCharts();
        } catch (error) {
            console.error('Error loading selections:', error);
            this.showError('加载选股数据失败: ' + error.message);
        }
    }
    
    updateStatsCards(stats) {
        document.getElementById('totalSelections').textContent = stats.total_selections || 0;
        document.getElementById('strategy1Count').textContent = stats.strategy_stats['少妇战法'] || 0;
        document.getElementById('strategy2Count').textContent = stats.strategy_stats['补票战法'] || 0;
        document.getElementById('strategy3Count').textContent = stats.strategy_stats['TePu战法'] || 0;
    }
    
    updateTable() {
        const tbody = document.getElementById('resultsTableBody');
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = this.filteredData.slice(startIndex, endIndex);
        
        if (pageData.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="fas fa-inbox fa-2x mb-2"></i><br>
                        暂无数据
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = pageData.map(item => `
            <tr>
                <td>
                    <strong>${item.stock_code}</strong>
                </td>
                <td>${item.stock_name || '--'}</td>
                <td>
                    <span class="badge strategy-badge strategy-${item.strategy_name}">
                        ${item.strategy_name}
                    </span>
                </td>
                <td>${this.formatDate(item.selection_date)}</td>
                <td>
                    ${item.confidence_score ? 
                        `<span class="badge bg-info">${(item.confidence_score * 100).toFixed(1)}%</span>` : 
                        '--'
                    }
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="dashboard.showStockDetail('${item.stock_code}')">
                        <i class="fas fa-eye"></i> 详情
                    </button>
                </td>
            </tr>
        `).join('');
        
        this.updatePagination();
    }
    
    updatePagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        const pagination = document.getElementById('pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let paginationHTML = '';
        
        // Previous button
        paginationHTML += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="dashboard.goToPage(${this.currentPage - 1})">上一页</a>
            </li>
        `;
        
        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="dashboard.goToPage(${i})">${i}</a>
                </li>
            `;
        }
        
        // Next button
        paginationHTML += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="dashboard.goToPage(${this.currentPage + 1})">下一页</a>
            </li>
        `;
        
        pagination.innerHTML = paginationHTML;
    }
    
    goToPage(page) {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.updateTable();
        }
    }
    
    initializeCharts() {
        this.initStrategyChart();
        this.initTrendChart();
    }
    
    initStrategyChart() {
        const ctx = document.getElementById('strategyChart').getContext('2d');
        this.charts.strategy = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['少妇战法', '补票战法', 'TePu战法'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#28a745', '#ffc107', '#17a2b8'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    initTrendChart() {
        const ctx = document.getElementById('trendChart').getContext('2d');
        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '选股数量',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    updateCharts() {
        this.updateStrategyChart();
        this.updateTrendChart();
    }
    
    updateStrategyChart() {
        if (!this.charts.strategy || !this.charts.strategy.data) {
            console.warn('Strategy chart not initialized yet');
            return;
        }

        const strategyCounts = this.getStrategyCounts(this.filteredData);
        this.charts.strategy.data.datasets[0].data = [
            strategyCounts['少妇战法'] || 0,
            strategyCounts['补票战法'] || 0,
            strategyCounts['TePu战法'] || 0
        ];
        this.charts.strategy.update();
    }
    
    updateTrendChart() {
        if (!this.charts.trend || !this.charts.trend.data) {
            console.warn('Trend chart not initialized yet');
            return;
        }

        const trendData = this.getTrendData(this.filteredData);
        this.charts.trend.data.labels = trendData.labels;
        this.charts.trend.data.datasets[0].data = trendData.data;
        this.charts.trend.update();
    }
    
    getStrategyCounts(data) {
        return data.reduce((acc, item) => {
            acc[item.strategy_name] = (acc[item.strategy_name] || 0) + 1;
            return acc;
        }, {});
    }
    
    getTrendData(data) {
        const dailyCounts = data.reduce((acc, item) => {
            const date = item.selection_date.split('T')[0];
            acc[date] = (acc[date] || 0) + 1;
            return acc;
        }, {});
        
        const sortedDates = Object.keys(dailyCounts).sort();
        const last7Days = sortedDates.slice(-7);
        
        return {
            labels: last7Days.map(date => this.formatDate(date)),
            data: last7Days.map(date => dailyCounts[date] || 0)
        };
    }
    
    setupEventListeners() {
        // Set default date to today
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('dateFilter').value = today;
    }
    
    async showStockDetail(stockCode) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/stocks/${stockCode}/history`);
            if (!response.ok) throw new Error('Failed to load stock history');
            
            const history = await response.json();
            this.displayStockDetail(stockCode, history);
        } catch (error) {
            console.error('Error loading stock detail:', error);
            this.showError('加载股票详情失败');
        }
    }
    
    displayStockDetail(stockCode, history) {
        const modal = new bootstrap.Modal(document.getElementById('stockDetailModal'));
        const content = document.getElementById('stockDetailContent');
        
        content.innerHTML = `
            <h6>股票代码: ${stockCode}</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>策略</th>
                            <th>置信度</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${history.map(item => `
                            <tr>
                                <td>${this.formatDate(item.selection_date)}</td>
                                <td>
                                    <span class="badge strategy-badge strategy-${item.strategy_name}">
                                        ${item.strategy_name}
                                    </span>
                                </td>
                                <td>
                                    ${item.confidence_score ? 
                                        `${(item.confidence_score * 100).toFixed(1)}%` : 
                                        '--'
                                    }
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        modal.show();
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN');
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        document.getElementById('lastUpdate').innerHTML = `
            <i class="fas fa-clock me-1"></i>
            最后更新: ${now.toLocaleString('zh-CN')}
        `;
    }
    
    showError(message) {
        console.error(message);

        // Create error alert in the UI
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <strong>错误:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of the container
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
    
    showSuccess(message) {
        // You can implement a toast notification system here
        console.log(message);
    }

    applyFilters() {
        const dateFilter = document.getElementById('dateFilter').value;
        const strategyFilter = document.getElementById('strategyFilter').value;
        const stockCodeFilter = document.getElementById('stockCodeFilter').value.trim();

        this.filteredData = this.currentData.filter(item => {
            let matches = true;

            if (dateFilter) {
                const itemDate = item.selection_date.split('T')[0];
                matches = matches && itemDate === dateFilter;
            }

            if (strategyFilter) {
                matches = matches && item.strategy_name === strategyFilter;
            }

            if (stockCodeFilter) {
                matches = matches && item.stock_code.toLowerCase().includes(stockCodeFilter.toLowerCase());
            }

            return matches;
        });

        this.currentPage = 1;
        this.updateTable();
        this.updateCharts();
    }

    clearFilters() {
        document.getElementById('dateFilter').value = '';
        document.getElementById('strategyFilter').value = '';
        document.getElementById('stockCodeFilter').value = '';

        this.filteredData = [...this.currentData];
        this.currentPage = 1;
        this.updateTable();
        this.updateCharts();
    }

    exportData() {
        if (this.filteredData.length === 0) {
            this.showError('没有数据可导出');
            return;
        }

        const csvContent = this.generateCSV(this.filteredData);
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');

        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `stock_selections_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            this.showSuccess('数据导出成功');
        }
    }

    generateCSV(data) {
        const headers = ['股票代码', '股票名称', '策略', '选择日期', '置信度'];
        const csvRows = [headers.join(',')];

        data.forEach(item => {
            const row = [
                item.stock_code,
                item.stock_name || '',
                item.strategy_name,
                this.formatDate(item.selection_date),
                item.confidence_score ? (item.confidence_score * 100).toFixed(1) + '%' : ''
            ];
            csvRows.push(row.join(','));
        });

        return csvRows.join('\n');
    }

    async refreshData() {
        const refreshBtn = document.querySelector('[onclick="refreshData()"]');
        const originalHTML = refreshBtn.innerHTML;

        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>刷新中...';
        refreshBtn.disabled = true;

        try {
            await this.loadInitialData();
            this.updateLastUpdateTime();
            this.showSuccess('数据刷新成功');
        } catch (error) {
            this.showError('数据刷新失败: ' + error.message);
        } finally {
            refreshBtn.innerHTML = originalHTML;
            refreshBtn.disabled = false;
        }
    }
}

// Global functions for HTML onclick handlers
window.applyFilters = function() {
    if (window.dashboard) {
        dashboard.applyFilters();
    } else {
        console.error('Dashboard not initialized');
    }
};

window.clearFilters = function() {
    if (window.dashboard) {
        dashboard.clearFilters();
    } else {
        console.error('Dashboard not initialized');
    }
};

window.exportData = function() {
    if (window.dashboard) {
        dashboard.exportData();
    } else {
        console.error('Dashboard not initialized');
    }
};

window.refreshData = function() {
    if (window.dashboard) {
        dashboard.refreshData();
    } else {
        console.error('Dashboard not initialized');
    }
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing dashboard...');
    try {
        window.dashboard = new StockDashboard();
        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
    }
});
