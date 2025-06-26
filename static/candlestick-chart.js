/**
 * Candlestick Chart Component using TradingView Lightweight Charts
 * 
 * This component provides an interactive candlestick chart for displaying
 * stock OHLC data with volume indicators and time period controls.
 */

class CandlestickChart {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.chart = null;
        this.candlestickSeries = null;
        this.volumeSeries = null;
        this.currentStockCode = null;
        this.currentPeriod = 'daily';
        this.apiBaseUrl = options.apiBaseUrl || 'http://localhost:8000/api';
        
        // Chart configuration
        this.chartOptions = {
            layout: {
                backgroundColor: '#ffffff',
                textColor: '#333333',
                fontSize: 12,
                fontFamily: 'Arial, sans-serif',
            },
            grid: {
                vertLines: {
                    color: '#f0f0f0',
                    style: 1,
                    visible: true,
                },
                horzLines: {
                    color: '#f0f0f0',
                    style: 1,
                    visible: true,
                },
            },
            crosshair: {
                mode: 0, // Normal crosshair mode
                vertLine: {
                    width: 1,
                    color: '#758696',
                    style: 3, // Dashed line
                },
                horzLine: {
                    width: 1,
                    color: '#758696',
                    style: 3, // Dashed line
                },
            },
            timeScale: {
                borderColor: '#D1D4DC',
                timeVisible: true,
                secondsVisible: false,
            },
            rightPriceScale: {
                borderColor: '#D1D4DC',
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.2,
                },
            },
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: true,
            },
            handleScale: {
                axisPressedMouseMove: true,
                mouseWheel: true,
                pinch: true,
            },
        };
        
        // Candlestick series options
        this.candlestickOptions = {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        };
        
        // Volume series options
        this.volumeOptions = {
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: 'volume',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        };
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error(`Container with ID '${this.containerId}' not found`);
            return;
        }

        // Check if TradingView library is loaded
        if (typeof window.LightweightCharts === 'undefined') {
            console.error('TradingView Lightweight Charts library not loaded');
            return;
        }

        // Create chart
        this.chart = window.LightweightCharts.createChart(this.container, {
            ...this.chartOptions,
            width: this.container.clientWidth,
            height: this.container.clientHeight || 400,
        });
        
        // Add candlestick series using v3.8.0 API
        this.candlestickSeries = this.chart.addCandlestickSeries(this.candlestickOptions);

        // Add volume series using v3.8.0 API
        this.volumeSeries = this.chart.addHistogramSeries({
            ...this.volumeOptions,
            priceScaleId: 'volume',
        });
        
        // Create volume price scale
        this.chart.priceScale('volume').applyOptions({
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });
        
        // Handle resize
        this.setupResizeObserver();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    setupResizeObserver() {
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver(entries => {
                if (entries.length === 0 || entries[0].target !== this.container) {
                    return;
                }
                
                const newRect = entries[0].contentRect;
                this.chart.applyOptions({
                    width: newRect.width,
                    height: newRect.height,
                });
            });
            
            resizeObserver.observe(this.container);
        } else {
            // Fallback for browsers without ResizeObserver
            window.addEventListener('resize', () => {
                this.chart.applyOptions({
                    width: this.container.clientWidth,
                    height: this.container.clientHeight,
                });
            });
        }
    }
    
    setupEventListeners() {
        // Add crosshair move listener for price display
        this.chart.subscribeCrosshairMove(param => {
            if (param.time) {
                const data = param.seriesPrices.get(this.candlestickSeries);
                if (data) {
                    this.updatePriceDisplay(data, param.time);
                }
            }
        });
    }
    
    updatePriceDisplay(ohlcData, time) {
        // This method can be overridden to update price display in UI
        const event = new CustomEvent('priceUpdate', {
            detail: {
                time: time,
                open: ohlcData.open,
                high: ohlcData.high,
                low: ohlcData.low,
                close: ohlcData.close,
            }
        });
        this.container.dispatchEvent(event);
    }
    
    async loadStockData(stockCode, period = 'daily', limit = 1000) {
        try {
            console.log(`Loading stock data for ${stockCode}, period: ${period}, limit: ${limit}`);
            this.showLoading(true);
            this.currentStockCode = stockCode;
            this.currentPeriod = period;

            const url = `${this.apiBaseUrl}/stocks/${stockCode}/ohlc?period=${period}&limit=${limit}`;
            console.log('Fetching from URL:', url);

            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Failed to load data: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Received data:', data);

            if (!data.data || data.data.length === 0) {
                throw new Error('No data available for this stock');
            }

            console.log(`Setting ${data.data.length} data points to chart`);
            this.setData(data.data);
            this.showLoading(false);

            return data;

        } catch (error) {
            console.error('Error loading stock data:', error);
            this.showError(error.message);
            this.showLoading(false);
            throw error;
        }
    }
    
    setData(ohlcData) {
        if (!this.candlestickSeries || !this.volumeSeries) {
            console.error('Chart series not initialized');
            return;
        }

        console.log('Setting data to chart, data length:', ohlcData.length);
        console.log('Sample data point:', ohlcData[0]);

        // Prepare candlestick data
        const candlestickData = ohlcData.map(item => ({
            time: item.time,
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
        }));

        // Prepare volume data
        const volumeData = ohlcData
            .filter(item => item.volume !== null && item.volume !== undefined)
            .map(item => ({
                time: item.time,
                value: item.volume,
                color: item.close >= item.open ? '#26a69a80' : '#ef535080', // Semi-transparent
            }));

        console.log('Candlestick data points:', candlestickData.length);
        console.log('Volume data points:', volumeData.length);

        // Set data to series
        this.candlestickSeries.setData(candlestickData);
        this.volumeSeries.setData(volumeData);

        console.log('Data set to series, fitting content...');

        // Fit content to show all data
        this.chart.timeScale().fitContent();

        console.log('Chart data loading complete');
    }
    
    changePeriod(period) {
        if (this.currentStockCode && period !== this.currentPeriod) {
            this.loadStockData(this.currentStockCode, period);
        }
    }
    
    showLoading(show) {
        const event = new CustomEvent('loadingStateChange', {
            detail: { loading: show }
        });
        this.container.dispatchEvent(event);
    }
    
    showError(message) {
        const event = new CustomEvent('chartError', {
            detail: { message: message }
        });
        this.container.dispatchEvent(event);
    }
    
    destroy() {
        if (this.chart) {
            this.chart.remove();
            this.chart = null;
            this.candlestickSeries = null;
            this.volumeSeries = null;
        }
    }
    
    // Utility methods for external control
    fitContent() {
        if (this.chart) {
            this.chart.timeScale().fitContent();
        }
    }
    
    scrollToPosition(position) {
        if (this.chart) {
            this.chart.timeScale().scrollToPosition(position, false);
        }
    }
    
    setVisibleRange(from, to) {
        if (this.chart) {
            this.chart.timeScale().setVisibleRange({ from, to });
        }
    }
    
    // Get current visible range
    getVisibleRange() {
        if (this.chart) {
            return this.chart.timeScale().getVisibleRange();
        }
        return null;
    }
}
