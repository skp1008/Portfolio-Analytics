import React from 'react';
import './MetricsOverview.css';

function MetricsOverview({ metrics }) {
  if (!metrics) return <div>Loading metrics...</div>;

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return typeof num === 'number' ? num.toFixed(2) : num;
  };

  const getTickers = () => {
    return Object.keys(metrics.annualized_return || {});
  };

  const tickers = getTickers();

  return (
    <div className="metrics-overview">
      <div className="metrics-grid">
        {tickers.map(ticker => (
          <div key={ticker} className="metric-card">
            <h3 className="metric-ticker">{ticker}</h3>
            <div className="metric-values">
              <div className="metric-item">
                <span className="metric-label">Total Return:</span>
                <span className={`metric-value ${metrics.total_return?.[ticker] >= 0 ? 'positive' : 'negative'}`}>
                  {formatNumber(metrics.total_return?.[ticker])}%
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Annualized Return:</span>
                <span className={`metric-value ${metrics.annualized_return?.[ticker] >= 0 ? 'positive' : 'negative'}`}>
                  {formatNumber(metrics.annualized_return?.[ticker])}%
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Volatility:</span>
                <span className="metric-value">
                  {formatNumber(metrics.volatility?.[ticker])}%
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Sharpe Ratio:</span>
                <span className="metric-value">
                  {formatNumber(metrics.sharpe_ratio?.[ticker])}
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Beta:</span>
                <span className="metric-value">
                  {formatNumber(metrics.beta?.[ticker])}
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Alpha:</span>
                <span className={`metric-value ${metrics.alpha?.[ticker] >= 0 ? 'positive' : 'negative'}`}>
                  {formatNumber(metrics.alpha?.[ticker])}%
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">VaR (95%):</span>
                <span className="metric-value negative">
                  {formatNumber(metrics.var_95?.[ticker])}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MetricsOverview;

