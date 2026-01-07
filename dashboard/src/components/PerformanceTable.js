import React from 'react';
import './PerformanceTable.css';

function PerformanceTable({ data }) {
  if (!data || data.length === 0) return <div>Loading performance data...</div>;

  const periods = data.map(row => row.Period);
  const tickers = Object.keys(data[0]).filter(key => key !== 'Period');

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return typeof num === 'number' ? num.toFixed(2) + '%' : num;
  };

  const getColorClass = (value) => {
    if (value === null || value === undefined) return '';
    const num = typeof value === 'number' ? value : parseFloat(value);
    return num >= 0 ? 'positive' : 'negative';
  };

  return (
    <div className="performance-table">
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Period</th>
              {tickers.map(ticker => (
                <th key={ticker}>{ticker}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr key={index}>
                <td className="period-cell">{row.Period}</td>
                {tickers.map(ticker => (
                  <td
                    key={ticker}
                    className={`value-cell ${getColorClass(row[ticker])}`}
                  >
                    {formatNumber(row[ticker])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default PerformanceTable;

