/**
 * Chart Modal Component
 * 
 * Manages the modal dialog for displaying candlestick charts
 * Integrates with the existing dashboard and CandlestickChart component
 */

class ChartModal {
    constructor(options = {}) {
        this.modalId = options.modalId || 'stockChartModal';
        this.apiBaseUrl = options.apiBaseUrl || 'http://localhost:8000/api';
        this.chart = null;
        this.currentStockCode = null;
        this.currentStockName = null;
        
        this.init();
    }
    
    init() {
        this.createModal();
        this.setupEventListeners();
    }
    
    createModal() {
        // Check if modal already exists
        if (document.getElementById(this.modalId)) {
            return;
        }
        
        const modalHTML = `
            <div class="modal fade" id="${this.modalId}" tabindex="-1" aria-labelledby="${this.modalId}Label" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="${this.modalId}Label">
                                <i class="fas fa-chart-line me-2"></i>
                                <span id="chartStockTitle">股票走势图</span>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Chart Controls -->
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <div class="btn-group" role="group" aria-label="时间周期">
                                        <input type="radio" class="btn-check" name="chartPeriod" id="periodDaily" value="daily" checked>
                                        <label class="btn btn-outline-primary" for="periodDaily">日线</label>
                                        
                                        <input type="radio" class="btn-check" name="chartPeriod" id="periodWeekly" value="weekly">
                                        <label class="btn btn-outline-primary" for="periodWeekly">周线</label>
                                        
                                        <input type="radio" class="btn-check" name="chartPeriod" id="periodMonthly" value="monthly">
                                        <label class="btn btn-outline-primary" for="periodMonthly">月线</label>
                                    </div>
                                </div>
                                <div class="col-md-6 text-end">
                                    <button type="button" class="btn btn-outline-secondary btn-sm" id="fitContentBtn">
                                        <i class="fas fa-expand-arrows-alt me-1"></i>
                                        适应内容
                                    </button>
                                    <button type="button" class="btn btn-outline-info btn-sm" id="refreshChartBtn">
                                        <i class="fas fa-sync-alt me-1"></i>
                                        刷新
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Price Display -->
                            <div class="row mb-3">
                                <div class="col-12">
                                    <div class="card bg-light">
                                        <div class="card-body py-2">
                                            <div class="row text-center" id="priceDisplay">
                                                <div class="col">
                                                    <small class="text-muted">开盘</small>
                                                    <div class="fw-bold" id="priceOpen">--</div>
                                                </div>
                                                <div class="col">
                                                    <small class="text-muted">最高</small>
                                                    <div class="fw-bold text-success" id="priceHigh">--</div>
                                                </div>
                                                <div class="col">
                                                    <small class="text-muted">最低</small>
                                                    <div class="fw-bold text-danger" id="priceLow">--</div>
                                                </div>
                                                <div class="col">
                                                    <small class="text-muted">收盘</small>
                                                    <div class="fw-bold" id="priceClose">--</div>
                                                </div>
                                                <div class="col">
                                                    <small class="text-muted">日期</small>
                                                    <div class="fw-bold" id="priceDate">--</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Loading Indicator -->
                            <div class="text-center mb-3" id="chartLoading" style="display: none;">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">加载中...</span>
                                </div>
                                <div class="mt-2">正在加载图表数据...</div>
                            </div>
                            
                            <!-- Error Display -->
                            <div class="alert alert-danger" id="chartError" style="display: none;">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                <span id="chartErrorMessage">加载图表数据时出错</span>
                            </div>
                            
                            <!-- Chart Container -->
                            <div id="chartContainer" style="height: 500px; width: 100%;"></div>
                        </div>
                        <div class="modal-footer">
                            <small class="text-muted me-auto">
                                数据来源: 本地CSV文件 | 
                                <a href="https://www.tradingview.com/" target="_blank" class="text-decoration-none">
                                    Powered by TradingView
                                </a>
                            </small>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    setupEventListeners() {
        const modal = document.getElementById(this.modalId);
        
        // Modal shown event - check if already bound to avoid duplicates
        if (!modal.hasAttribute('data-chart-listener-bound')) {
            modal.addEventListener('shown.bs.modal', () => {
                console.log('=== MODAL SHOWN EVENT ===');
                console.log('Stock code:', this.currentStockCode);
                if (this.currentStockCode) {
                    // Simple direct chart creation
                    this.createSimpleChart();
                }
            });
            modal.setAttribute('data-chart-listener-bound', 'true');
        }
        
        // Modal hidden event
        modal.addEventListener('hidden.bs.modal', () => {
            this.destroyChart();
        });
        
        // Period change
        const periodInputs = modal.querySelectorAll('input[name="chartPeriod"]');
        periodInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                if (e.target.checked && this.candlestickSeries && this.chart && this.currentStockCode) {
                    this.loadSimpleData(this.candlestickSeries, this.chart);
                }
            });
        });
        
        // Fit content button
        const fitContentBtn = modal.querySelector('#fitContentBtn');
        fitContentBtn.addEventListener('click', () => {
            if (this.chart) {
                this.chart.fitContent();
            }
        });
        
        // Refresh button
        const refreshBtn = modal.querySelector('#refreshChartBtn');
        refreshBtn.addEventListener('click', () => {
            if (this.candlestickSeries && this.chart && this.currentStockCode) {
                this.loadSimpleData(this.candlestickSeries, this.chart);
            }
        });
        
        // Chart container events
        const chartContainer = modal.querySelector('#chartContainer');
        chartContainer.addEventListener('loadingStateChange', (e) => {
            this.showLoading(e.detail.loading);
        });
        
        chartContainer.addEventListener('chartError', (e) => {
            this.showError(e.detail.message);
        });
        
        chartContainer.addEventListener('priceUpdate', (e) => {
            this.updatePriceDisplay(e.detail);
        });
    }
    
    show(stockCode, stockName = null) {
        this.currentStockCode = stockCode;
        this.currentStockName = stockName;

        console.log('=== SHOW CHART ===');
        console.log('Stock code:', stockCode);

        // Update modal title
        const title = document.getElementById('chartStockTitle');
        title.textContent = stockName ?
            `${stockName} (${stockCode}) - 走势图` :
            `${stockCode} - 走势图`;

        // Destroy any existing chart first
        this.destroyChart();

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById(this.modalId));
        modal.show();

        // Create chart immediately after showing modal
        setTimeout(() => {
            console.log('Creating chart after modal show...');
            this.createSimpleChart();
        }, 500);
    }
    
    createSimpleChart() {
        console.log('=== CREATE SIMPLE CHART ===');

        // Clear any existing content
        const container = document.getElementById('chartContainer');
        if (!container) {
            console.error('Chart container not found');
            return;
        }

        container.innerHTML = '';
        console.log('Container cleared, dimensions:', container.clientWidth, 'x', container.clientHeight);

        // Check TradingView library
        if (typeof window.LightweightCharts === 'undefined') {
            console.error('TradingView library not available');
            container.innerHTML = '<div class="alert alert-danger">TradingView库未加载</div>';
            return;
        }

        try {
            console.log('=== CREATING CHART ===');

            // Create chart
            const chart = window.LightweightCharts.createChart(container, {
                width: container.clientWidth || 800,
                height: 400,
                layout: {
                    backgroundColor: '#ffffff',
                    textColor: '#333333',
                },
                grid: {
                    vertLines: { color: '#f0f0f0' },
                    horzLines: { color: '#f0f0f0' },
                },
                timeScale: {
                    borderColor: '#D1D4DC',
                },
                rightPriceScale: {
                    borderColor: '#D1D4DC',
                },
            });

            console.log('Chart created successfully:', !!chart);
            console.log('Chart object type:', typeof chart);
            console.log('Chart methods:', Object.keys(chart || {}));
            console.log('Has addCandlestickSeries:', typeof chart.addCandlestickSeries);
            console.log('Has addSeries:', typeof chart.addSeries);
            console.log('Chart prototype:', Object.getPrototypeOf(chart));
            console.log('Chart constructor:', chart.constructor.name);

            // Create candlestick series - using v3.8.0 API
            const candlestickSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });

            console.log('Candlestick series created successfully:', !!candlestickSeries);

            // Load data
            this.loadSimpleData(candlestickSeries, chart);

            // Store references
            this.chart = chart;
            this.candlestickSeries = candlestickSeries;

        } catch (error) {
            console.error('Error creating chart:', error);
            container.innerHTML = `<div class="alert alert-danger">创建图表失败: ${error.message}</div>`;
        }
    }

    async loadSimpleData(candlestickSeries, chart) {
        try {
            console.log('Loading data for stock:', this.currentStockCode);

            const period = document.querySelector('input[name="chartPeriod"]:checked').value;
            const url = `${this.apiBaseUrl}/stocks/${this.currentStockCode}/ohlc?period=${period}&limit=1000`;

            console.log('Fetching from:', url);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Data received:', data.data?.length, 'points');

            if (!data.data || data.data.length === 0) {
                throw new Error('No data available');
            }

            // Set data
            candlestickSeries.setData(data.data);
            chart.timeScale().fitContent();

            console.log('Data loaded successfully');

        } catch (error) {
            console.error('Error loading data:', error);
            const container = document.getElementById('chartContainer');
            if (container) {
                container.innerHTML = `<div class="alert alert-warning">加载数据失败: ${error.message}</div>`;
            }
        }
    }
    


    destroyChart() {
        console.log('Destroying chart...');

        if (this.chart) {
            try {
                // For TradingView chart, use remove method
                if (typeof this.chart.remove === 'function') {
                    this.chart.remove();
                } else if (typeof this.chart.destroy === 'function') {
                    this.chart.destroy();
                }
            } catch (error) {
                console.warn('Error destroying chart:', error);
            }
            this.chart = null;
            this.candlestickSeries = null;
        }

        // Clear container
        const container = document.getElementById('chartContainer');
        if (container) {
            container.innerHTML = '';
        }

        // Reset displays
        this.showLoading(false);
        this.showError(null);
        this.updatePriceDisplay(null);

        console.log('Chart destroyed');
    }
    
    showLoading(show) {
        const loadingEl = document.getElementById('chartLoading');
        const chartContainer = document.getElementById('chartContainer');
        
        if (show) {
            loadingEl.style.display = 'block';
            chartContainer.style.opacity = '0.5';
        } else {
            loadingEl.style.display = 'none';
            chartContainer.style.opacity = '1';
        }
    }
    
    showError(message) {
        const errorEl = document.getElementById('chartError');
        const errorMessageEl = document.getElementById('chartErrorMessage');
        
        if (message) {
            errorMessageEl.textContent = message;
            errorEl.style.display = 'block';
        } else {
            errorEl.style.display = 'none';
        }
    }
    
    updatePriceDisplay(data) {
        const elements = {
            open: document.getElementById('priceOpen'),
            high: document.getElementById('priceHigh'),
            low: document.getElementById('priceLow'),
            close: document.getElementById('priceClose'),
            date: document.getElementById('priceDate')
        };
        
        if (data) {
            elements.open.textContent = data.open.toFixed(2);
            elements.high.textContent = data.high.toFixed(2);
            elements.low.textContent = data.low.toFixed(2);
            elements.close.textContent = data.close.toFixed(2);
            elements.date.textContent = data.time;
            
            // Update close price color
            elements.close.className = 'fw-bold ' + (data.close >= data.open ? 'text-success' : 'text-danger');
        } else {
            // Reset to default
            Object.values(elements).forEach(el => {
                el.textContent = '--';
                el.className = 'fw-bold';
            });
        }
    }
}
