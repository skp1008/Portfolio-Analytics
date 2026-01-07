import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import MetricsOverview from './components/MetricsOverview';
import TimeSeriesChart from './components/TimeSeriesChart';
import CorrelationMatrix from './components/CorrelationMatrix';
import ForecastChart from './components/ForecastChart';
import PerformanceTable from './components/PerformanceTable';
import DrawdownChart from './components/DrawdownChart';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [prices, setPrices] = useState(null);
  const [returns, setReturns] = useState(null);
  const [drawdown, setDrawdown] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [timeRange, setTimeRange] = useState({ start: '2020-01-01', end: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const tickers = ["AMZN", "AAPL", "META", "NVDA", "GOOGL", "MSFT", "TSLA", "NFLX", "ADBE", "ORCL"];

  useEffect(() => {
    fetchAllData();
  }, [timeRange]);

  useEffect(() => {
    if (selectedTicker) {
      fetchForecastData(selectedTicker);
    }
  }, [selectedTicker]);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [metricsRes, pricesRes, returnsRes, drawdownRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/portfolio/metrics`, {
          params: { start_date: timeRange.start, end_date: timeRange.end }
        }),
        axios.get(`${API_BASE_URL}/portfolio/prices`, {
          params: { start_date: timeRange.start, end_date: timeRange.end }
        }),
        axios.get(`${API_BASE_URL}/portfolio/returns`, {
          params: { start_date: timeRange.start, end_date: timeRange.end }
        }),
        axios.get(`${API_BASE_URL}/portfolio/drawdown`, {
          params: { start_date: timeRange.start, end_date: timeRange.end }
        })
      ]);

      setMetrics(metricsRes.data);
      setPrices(pricesRes.data);
      setReturns(returnsRes.data);
      setDrawdown(drawdownRes.data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchForecastData = async (ticker) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/forecast/predictions`, {
        params: { ticker }
      });
      setForecastData(response.data);
    } catch (err) {
      console.error('Error fetching forecast data:', err);
    }
  };

  const handleTimeRangeChange = (start, end) => {
    setTimeRange({ start, end });
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-error">
        <h2>Error Loading Data</h2>
        <p>{error}</p>
        <button onClick={fetchAllData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Portfolio Analytics Dashboard</h1>
        <div className="header-controls">
          <div className="time-range-selector">
            <label>Start Date:</label>
            <input
              type="date"
              value={timeRange.start}
              onChange={(e) => handleTimeRangeChange(e.target.value, timeRange.end)}
              min="2010-01-01"
            />
            <label>End Date:</label>
            <input
              type="date"
              value={timeRange.end || ''}
              onChange={(e) => handleTimeRangeChange(timeRange.start, e.target.value)}
              max={new Date().toISOString().split('T')[0]}
            />
          </div>
        </div>
      </header>

      <main className="app-main">
        <section className="metrics-section">
          <MetricsOverview metrics={metrics} />
        </section>

        <section className="charts-section">
          <div className="chart-container">
            <h2>Price Time Series</h2>
            <TimeSeriesChart data={prices} type="prices" />
          </div>

          <div className="chart-container">
            <h2>Returns Time Series</h2>
            <TimeSeriesChart data={returns} type="returns" />
          </div>

          <div className="chart-container">
            <h2>Drawdown</h2>
            <DrawdownChart data={drawdown} />
          </div>
        </section>

        <section className="correlation-section">
          <div className="chart-container full-width">
            <h2>Stock Correlation Matrix</h2>
            <CorrelationMatrix data={metrics?.correlation_matrix} />
          </div>
        </section>

        <section className="forecast-section">
          <div className="chart-container">
            <h2>Forecast Predictions</h2>
            <div className="ticker-selector">
              <label>Select Ticker:</label>
              <select
                value={selectedTicker}
                onChange={(e) => setSelectedTicker(e.target.value)}
              >
                {tickers.map(ticker => (
                  <option key={ticker} value={ticker}>{ticker}</option>
                ))}
              </select>
            </div>
            <ForecastChart data={forecastData} />
          </div>
        </section>

        <section className="performance-section">
          <div className="chart-container full-width">
            <h2>Performance Summary</h2>
            <PerformanceTable data={metrics?.performance_summary} />
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;

