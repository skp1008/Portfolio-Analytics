// Main application logic
let appData = null;
let selectedTicker = null;
let selectedPeriod = 'Max';

const periods = {
    '1 Day': 1,
    '15 Days': 15,
    '1 Month': 30,
    '5 Years': 1825,
    'Max': null
};

// Load data from JSON file - SIMPLIFIED VERSION
async function loadData() {
    console.log('🔄 Starting to load data...');
    
    try {
        // Fetch the JSON file
        console.log('📡 Fetching /cached_results.json...');
        const response = await fetch('/cached_results.json');
        
        console.log('📥 Response status:', response.status, response.statusText);
        console.log('📥 Content-Type:', response.headers.get('content-type'));
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Get the text
        const text = await response.text();
        console.log('✅ Got response text, length:', text.length);
        console.log('📄 First 100 chars:', text.substring(0, 100));
        
        // Parse JSON
        console.log('🔍 Parsing JSON...');
        appData = JSON.parse(text);
        console.log('✅ JSON parsed successfully!');
        console.log('📊 Data keys:', Object.keys(appData));
        console.log('📊 Predictions count:', appData.predictions?.length || 0);
        
        // Validate we have predictions
        if (!appData.predictions || !Array.isArray(appData.predictions) || appData.predictions.length === 0) {
            console.error('❌ No predictions found in data');
            console.error('📊 Full data structure:', appData);
            throw new Error('No predictions in data file');
        }
        
        // Initialize with first ticker
        const tickers = [...new Set(appData.predictions.map(p => p.Ticker))].sort();
        selectedTicker = tickers[0];
        console.log('✅ Data loaded successfully! Tickers:', tickers);
        console.log('📊 First prediction:', appData.predictions[0]);

        // Hide loading, show content
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'none';
        document.getElementById('content').style.display = 'block';
        
        // Render everything
        renderAll();
        
    } catch (error) {
        console.error('❌ ERROR loading data:', error);
        console.error('❌ Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
        
        // Show error
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('content').style.display = 'none';
        
        document.getElementById('error').innerHTML = `
            <div style="color: #ef4444; font-weight: 600; margin-bottom: 1rem;">
                Error loading data: ${error.message}
            </div>
            <div style="color: #94a3b8; font-size: 0.875rem;">
                Check the browser console (F12) for details.
            </div>
        `;
    }
}

function renderAll() {
    console.log('🎨 Rendering all components...');
    
    if (!appData) {
        console.error('❌ Cannot render: appData is null');
        return;
    }
    
    // Model run date
    if (appData.model_run_date) {
        document.getElementById('modelRunDate').textContent = `Model run: ${appData.model_run_date}`;
    }
    
    try {
        renderStockSelection();
        renderStockSummary();
        renderPeriodButtons();
        renderPriceChart();
        renderPrediction();
        renderMarketChart();
        renderBacktestMetrics();
        renderStockMetrics();
        renderEconomicMetrics();
        console.log('✅ All components rendered successfully!');
    } catch (error) {
        console.error('❌ Error rendering components:', error);
        throw error;
    }
}

function renderStockSelection() {
    const container = document.getElementById('stockSelection');
    const tickers = [...new Set(appData.predictions.map(p => p.Ticker))].sort();
    
    container.innerHTML = '';
    
    tickers.forEach(ticker => {
        const wrapper = document.createElement('div');
        wrapper.style.textAlign = 'center';
        
        const icon = document.createElement('div');
        icon.className = `stock-icon-circle ${ticker === selectedTicker ? 'selected' : ''}`;
        icon.textContent = ticker[0];
        
        const button = document.createElement('button');
        button.className = `stock-button ${ticker === selectedTicker ? 'selected' : ''}`;
        button.textContent = ticker;
        button.onclick = () => {
            selectedTicker = ticker;
            renderAll();
        };
        
        wrapper.appendChild(icon);
        wrapper.appendChild(button);
        container.appendChild(wrapper);
    });
}

function renderStockSummary() {
    const pred = appData.predictions.find(p => p.Ticker === selectedTicker);
    if (!pred) return;
    
    const stockData = appData.stock_data.filter(s => s.Ticker === selectedTicker);
    stockData.sort((a, b) => new Date(a.Date) - new Date(b.Date));
    
    const currentPrice = pred['Adj Close'];
    const currentDate = pred.Date;
    
    // Calculate daily change
    let dailyChangePct = 0;
    let dailyChangeDollar = 0;
    
    const currentIdx = stockData.findIndex(s => s.Date <= currentDate);
    if (currentIdx >= 1) {
        const prevPrice = stockData[currentIdx - 1]['Adj Close'];
        dailyChangePct = ((currentPrice / prevPrice) - 1) * 100;
        dailyChangeDollar = currentPrice - prevPrice;
    }
    
    const companyNames = {
        'NVDA': 'NVIDIA Corporation',
        'ORCL': 'Oracle Corporation',
        'THAR': 'Tharimmune Inc.',
        'SOFI': 'SoFi Technologies Inc.',
        'RR': 'Rolls-Royce Holdings plc',
        'RGTI': 'Rigetti Computing Inc.'
    };
    
    const changeClass = dailyChangePct >= 0 ? 'positive' : 'negative';
    const changeSign = dailyChangePct >= 0 ? '+' : '';
    
    document.getElementById('stockSummary').innerHTML = `
        <div class="summary-content">
            <div class="summary-left">
                <h3>${companyNames[selectedTicker] || selectedTicker}</h3>
                <h2>${selectedTicker}</h2>
            </div>
            <div class="summary-right">
                <div class="price">$${currentPrice.toFixed(2)}</div>
                <div class="change ${changeClass}">
                    ${changeSign}${dailyChangeDollar.toFixed(2)} (${changeSign}${dailyChangePct.toFixed(2)}%)
                </div>
                <div style="font-size: 0.75rem; color: #64748b;">
                    Updated: ${currentDate}
                </div>
            </div>
        </div>
    `;
}

function renderPeriodButtons() {
    const container = document.getElementById('periodButtons');
    container.innerHTML = '';
    
    Object.keys(periods).forEach(label => {
        const btn = document.createElement('button');
        btn.className = `period-btn ${selectedPeriod === label ? 'selected' : ''}`;
        btn.textContent = label;
        btn.onclick = () => {
            selectedPeriod = label;
            renderPriceChart();
        };
        container.appendChild(btn);
    });
}

function renderPriceChart() {
    const pred = appData.predictions.find(p => p.Ticker === selectedTicker);
    if (!pred) return;
    
    const stockData = appData.stock_data.filter(s => s.Ticker === selectedTicker);
    stockData.sort((a, b) => new Date(a.Date) - new Date(b.Date));
    
    const currentDate = new Date(pred.Date);
    const periodDays = periods[selectedPeriod];
    
    let filteredData = stockData;
    if (periodDays) {
        const startDate = new Date(currentDate);
        startDate.setDate(startDate.getDate() - periodDays);
        filteredData = stockData.filter(s => new Date(s.Date) >= startDate && new Date(s.Date) <= currentDate);
    }
    
    if (filteredData.length === 0) return;
    
    const dates = filteredData.map(d => d.Date);
    const prices = filteredData.map(d => d['Adj Close']);
    
    const startPrice = prices[0];
    const endPrice = prices[prices.length - 1];
    const pctChange = ((endPrice / startPrice) - 1) * 100;
    
    const lineColor = pctChange >= 0 ? '#10b981' : '#ef4444';
    
    // Calculate y-axis range for shorter periods
    let yaxisRange = null;
    if (periodDays && periodDays <= 30) {
        const priceMin = Math.min(...prices);
        const priceMax = Math.max(...prices);
        const priceRange = priceMax - priceMin;
        const padding = Math.max(priceRange * 0.05, priceMax * 0.01);
        yaxisRange = [priceMin - padding, priceMax + padding];
    }
    
    const trace = {
        x: dates,
        y: prices,
        type: 'scatter',
        mode: 'lines',
        name: selectedTicker,
        line: { color: lineColor, width: 2.5 },
        fill: 'tozeroy',
        fillcolor: pctChange >= 0 
            ? 'rgba(16, 185, 129, 0.1)' 
            : 'rgba(239, 68, 68, 0.1)',
        hovertemplate: '<b>%{fullData.name}</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
    };
    
    const latestTrace = {
        x: [dates[dates.length - 1]],
        y: [prices[prices.length - 1]],
        type: 'scatter',
        mode: 'markers',
        name: 'Latest',
        marker: { size: 10, color: lineColor, line: { width: 2, color: '#0f172a' } },
        showlegend: false,
        hovertemplate: '<b>Latest</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
    };
    
    const layout = {
        template: 'plotly_dark',
        height: 550,
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        xaxis: {
            showgrid: false,
            showline: true,
            linecolor: '#334155',
            tickfont: { color: '#94a3b8', size: 11 },
            type: 'date',
            tickformat: periodDays === 1 ? '%H:%M' : '%Y-%m-%d'
        },
        yaxis: {
            title: { text: 'Price ($)', font: { color: '#94a3b8', size: 12 } },
            showgrid: true,
            gridcolor: 'rgba(148, 163, 184, 0.1)',
            showline: true,
            linecolor: '#334155',
            tickfont: { color: '#94a3b8', size: 11 },
            range: yaxisRange
        },
        margin: { l: 60, r: 20, t: 60, b: 40 },
        hovermode: 'x unified',
        hoverlabel: {
            bgcolor: 'rgba(15, 23, 42, 0.95)',
            bordercolor: '#334155',
            font_size: 12
        }
    };
    
    Plotly.newPlot('priceChart', [trace, latestTrace], layout, {
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d']
    });
    
    // Show percentage change
    const changeClass = pctChange >= 0 ? 'positive' : 'negative';
    const changeSign = pctChange >= 0 ? '+' : '';
    document.getElementById('pctChange').innerHTML = 
        `<span class="${changeClass}">Change: ${changeSign}${pctChange.toFixed(2)}%</span>`;
}

function renderPrediction() {
    const pred = appData.predictions.find(p => p.Ticker === selectedTicker);
    if (!pred) return;
    
    const action = pred.Action;
    const upProb = pred.Up * 100;
    const flatProb = pred.Flat * 100;
    const downProb = pred.Down * 100;
    const maxProb = Math.max(upProb, flatProb, downProb);
    const confidence = maxProb;
    
    const signalMap = {
        'BUY': { label: 'LONG', class: 'BUY' },
        'SHORT': { label: 'SHORT', class: 'SHORT' },
        'HOLD': { label: 'HOLD', class: 'HOLD' }
    };
    
    const signal = signalMap[action] || signalMap['HOLD'];
    
    document.getElementById('signalBadge').innerHTML = `
        <div class="signal-badge ${signal.class}">
            <div class="signal-text">${signal.label}</div>
            <div class="signal-subtitle">Model Confidence: ${confidence.toFixed(1)}%</div>
        </div>
    `;
    
    // Pie chart
    const pieData = [{
        labels: ['Rise', 'Neutral', 'Fall'],
        values: [upProb, flatProb, downProb],
        type: 'pie',
        marker: { colors: ['#10b981', '#64748b', '#dc2626'] },
        textinfo: 'label+percent',
        hovertemplate: '<b>%{label}</b><br>Probability: %{percent}<extra></extra>'
    }];
    
    const pieLayout = {
        template: 'plotly_dark',
        height: 400,
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { color: 'white', size: 12 },
        showlegend: true,
        legend: {
            orientation: 'v',
            yanchor: 'middle',
            y: 0.5,
            xanchor: 'left',
            x: 1.1,
            font: { color: '#94a3b8', size: 12 }
        },
        margin: { l: 0, r: 0, t: 0, b: 0 }
    };
    
    Plotly.newPlot('pieChart', pieData, pieLayout, { displayModeBar: false });
    
    // Probability bars
    const probabilities = [
        { label: 'Rise', value: upProb, class: 'rise', color: '#10b981' },
        { label: 'Neutral', value: flatProb, class: 'neutral', color: '#64748b' },
        { label: 'Fall', value: downProb, class: 'fall', color: '#dc2626' }
    ];
    
    document.getElementById('probabilityList').innerHTML = `
        <h3 style="font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.25rem;">Probabilities</h3>
        ${probabilities.map(p => `
            <div class="probability-row">
                <div class="probability-label">${p.label}</div>
                <div class="probability-value" style="color: ${p.color};">${p.value.toFixed(1)}%</div>
                <div class="probability-bar">
                    <div class="probability-bar-fill ${p.class}" style="width: ${p.value}%;"></div>
                </div>
            </div>
        `).join('')}
    `;
}

function renderMarketChart() {
    if (!appData.market_data || !appData.market_data['^GSPC']) return;
    
    const spxData = appData.market_data['^GSPC'];
    const dates = spxData.dates;
    const prices = spxData.prices;
    
    if (prices.length === 0) return;
    
    const spxStart = prices[0];
    const spxEnd = prices[prices.length - 1];
    const spxChange = ((spxEnd / spxStart) - 1) * 100;
    const spxLineColor = spxChange >= 0 ? '#10b981' : '#ef4444';
    
    const trace = {
        x: dates,
        y: prices,
        type: 'scatter',
        mode: 'lines',
        name: 'S&P 500',
        line: { color: spxLineColor, width: 2.5 },
        fill: 'tozeroy',
        fillcolor: spxChange >= 0 
            ? 'rgba(16, 185, 129, 0.1)' 
            : 'rgba(239, 68, 68, 0.1)',
        hovertemplate: '<b>S&P 500</b><br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
    };
    
    const latestTrace = {
        x: [dates[dates.length - 1]],
        y: [prices[prices.length - 1]],
        type: 'scatter',
        mode: 'markers',
        marker: { size: 10, color: spxLineColor, line: { width: 2, color: '#0f172a' } },
        showlegend: false,
        hovertemplate: '<b>Latest</b><br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
    };
    
    const layout = {
        template: 'plotly_dark',
        height: 550,
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        xaxis: {
            showgrid: false,
            showline: true,
            linecolor: '#334155',
            tickfont: { color: '#94a3b8', size: 11 },
            type: 'date',
            tickformat: '%Y-%m-%d'
        },
        yaxis: {
            title: { text: 'Price', font: { color: '#94a3b8', size: 12 } },
            showgrid: true,
            gridcolor: 'rgba(148, 163, 184, 0.1)',
            showline: true,
            linecolor: '#334155',
            tickfont: { color: '#94a3b8', size: 11 }
        },
        margin: { l: 60, r: 20, t: 80, b: 40 },
        hovermode: 'x unified',
        hoverlabel: {
            bgcolor: 'rgba(15, 23, 42, 0.95)',
            bordercolor: '#334155',
            font_size: 12
        }
    };
    
    Plotly.newPlot('marketChart', [trace, latestTrace], layout, {
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d']
    });
}

function renderBacktestMetrics() {
    const backtest = appData.backtest_results[selectedTicker];
    if (!backtest) {
        document.getElementById('backtestMetrics').innerHTML = '<h3>Backtest Results</h3><p>No data available</p>';
        return;
    }
    
    document.getElementById('backtestMetrics').innerHTML = `
        <h3>Backtest Results</h3>
        <div class="metric-item">
            <span class="metric-label">Accuracy</span>
            <span class="metric-value">${(backtest.accuracy * 100).toFixed(1)}%</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">F1 Score (Macro)</span>
            <span class="metric-value">${backtest.f1_macro.toFixed(3)}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">Log Loss</span>
            <span class="metric-value">${backtest.log_loss.toFixed(3)}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">Number of Folds</span>
            <span class="metric-value">${backtest.n_folds}</span>
        </div>
    `;
}

function renderStockMetrics() {
    const pred = appData.predictions.find(p => p.Ticker === selectedTicker);
    if (!pred) return;
    
    const stockData = appData.stock_data.filter(s => s.Ticker === selectedTicker);
    stockData.sort((a, b) => new Date(a.Date) - new Date(b.Date));
    
    const currentDate = new Date(pred.Date);
    const currentPrice = pred['Adj Close'];
    
    // Calculate stats
    const oneYearAgo = new Date(currentDate);
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    
    const oneYearData = stockData.filter(s => new Date(s.Date) >= oneYearAgo);
    const oneYearReturn = oneYearData.length > 0 
        ? ((currentPrice / oneYearData[0]['Adj Close']) - 1) * 100 
        : null;
    
    // Volatility
    const returns = [];
    for (let i = 1; i < stockData.length; i++) {
        const ret = (stockData[i]['Adj Close'] / stockData[i-1]['Adj Close']) - 1;
        returns.push(ret);
    }
    const volatility = returns.length > 0 
        ? Math.sqrt(returns.reduce((a, b) => a + b * b, 0) / returns.length) * Math.sqrt(252) * 100 
        : null;
    
    // 52-week high/low
    const fiftyTwoWeeks = stockData.filter(s => new Date(s.Date) >= oneYearAgo);
    const weekHigh = fiftyTwoWeeks.length > 0 ? Math.max(...fiftyTwoWeeks.map(s => s['Adj Close'])) : null;
    const weekLow = fiftyTwoWeeks.length > 0 ? Math.min(...fiftyTwoWeeks.map(s => s['Adj Close'])) : null;
    const vs52wHigh = weekHigh ? ((currentPrice / weekHigh) - 1) * 100 : null;
    
    document.getElementById('stockMetrics').innerHTML = `
        <h3>Stock Statistics</h3>
        ${oneYearReturn !== null ? `
            <div class="metric-item">
                <span class="metric-label">1 Year Return</span>
                <span class="metric-value">${oneYearReturn.toFixed(2)}%</span>
            </div>
        ` : ''}
        ${volatility !== null ? `
            <div class="metric-item">
                <span class="metric-label">Volatility (Annualized)</span>
                <span class="metric-value">${volatility.toFixed(2)}%</span>
            </div>
        ` : ''}
        ${weekHigh !== null ? `
            <div class="metric-item">
                <span class="metric-label">52-Week High</span>
                <span class="metric-value">$${weekHigh.toFixed(2)}</span>
            </div>
        ` : ''}
        ${weekLow !== null ? `
            <div class="metric-item">
                <span class="metric-label">52-Week Low</span>
                <span class="metric-value">$${weekLow.toFixed(2)}</span>
            </div>
        ` : ''}
        ${vs52wHigh !== null ? `
            <div class="metric-item">
                <span class="metric-label">vs 52-Week High</span>
                <span class="metric-value">${vs52wHigh.toFixed(2)}%</span>
            </div>
        ` : ''}
    `;
}

function renderEconomicMetrics() {
    const econ = appData.economic_data;
    if (!econ) return;
    
    const unemployment = econ.Unemployment_Rate;
    const interest = econ.Interest_Rate;
    const inflationYoy = econ.Inflation_YoY;
    const inflationRaw = econ.Inflation_Rate;
    
    const unemploymentStr = unemployment !== null && unemployment !== undefined ? `${unemployment.toFixed(2)}%` : 'N/A';
    const interestStr = interest !== null && interest !== undefined ? `${interest.toFixed(2)}%` : 'N/A';
    const inflationStr = inflationYoy !== null && inflationYoy !== undefined 
        ? `${inflationYoy.toFixed(2)}%` 
        : (inflationRaw !== null && inflationRaw !== undefined ? `${inflationRaw.toFixed(2)}` : 'N/A');
    const inflationLabel = inflationYoy !== null && inflationYoy !== undefined 
        ? 'Inflation Rate (YoY)' 
        : 'Inflation Rate (Index)';
    
    document.getElementById('economicMetrics').innerHTML = `
        <div class="economic-metric-card">
            <div class="economic-metric-label">Unemployment Rate</div>
            <div class="economic-metric-value">${unemploymentStr}</div>
        </div>
        <div class="economic-metric-card">
            <div class="economic-metric-label">Interest Rate</div>
            <div class="economic-metric-value">${interestStr}</div>
        </div>
        <div class="economic-metric-card">
            <div class="economic-metric-label">${inflationLabel}</div>
            <div class="economic-metric-value">${inflationStr}</div>
        </div>
    `;
}

// Initialize app
loadData();
