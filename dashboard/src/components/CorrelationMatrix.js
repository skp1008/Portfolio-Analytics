import React from 'react';
import './CorrelationMatrix.css';

function CorrelationMatrix({ data }) {
  if (!data) return <div>Loading correlation matrix...</div>;

  const tickers = Object.keys(data);
  
  const getColor = (value) => {
    // Red for negative, blue for positive
    const intensity = Math.abs(value);
    if (value < 0) {
      // Negative: light red to dark red
      const red = Math.round(255 - (intensity * 100));
      const green = Math.round(200 - (intensity * 150));
      const blue = Math.round(200 - (intensity * 150));
      return `rgb(${red}, ${green}, ${blue})`;
    } else {
      // Positive: light blue to dark blue
      const red = Math.round(200 - (intensity * 150));
      const green = Math.round(220 - (intensity * 100));
      const blue = Math.round(255 - (intensity * 50));
      return `rgb(${red}, ${green}, ${blue})`;
    }
  };

  const getTextColor = (value) => {
    return Math.abs(value) > 0.5 ? 'white' : '#333';
  };

  return (
    <div className="correlation-matrix">
      <div className="matrix-container">
        <table className="correlation-table">
          <thead>
            <tr>
              <th></th>
              {tickers.map(ticker => (
                <th key={ticker}>{ticker}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tickers.map(ticker1 => (
              <tr key={ticker1}>
                <th>{ticker1}</th>
                {tickers.map(ticker2 => {
                  const value = data[ticker1]?.[ticker2] || 0;
                  const bgColor = getColor(value);
                  const textColor = getTextColor(value);
                  return (
                    <td
                      key={`${ticker1}-${ticker2}`}
                      style={{
                        backgroundColor: bgColor,
                        color: textColor
                      }}
                    >
                      {value.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="color-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: 'rgb(200, 150, 150)' }}></span>
          <span>Strong Negative</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: 'rgb(240, 240, 240)' }}></span>
          <span>No Correlation</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: 'rgb(150, 200, 255)' }}></span>
          <span>Strong Positive</span>
        </div>
      </div>
    </div>
  );
}

export default CorrelationMatrix;

