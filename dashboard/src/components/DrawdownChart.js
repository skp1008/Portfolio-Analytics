import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import './DrawdownChart.css';

function DrawdownChart({ data }) {
  if (!data || !data.dates) return <div>Loading drawdown data...</div>;

  const tickers = Object.keys(data.drawdown || {});
  
  // Prepare data for Recharts
  const chartData = data.dates.map((date, index) => {
    const point = { date };
    tickers.forEach(ticker => {
      const values = data.drawdown[ticker];
      if (values && values[index] !== undefined) {
        point[ticker] = values[index];
      }
    });
    return point;
  });

  // Limit data points for performance
  const step = Math.max(1, Math.floor(chartData.length / 500));
  const displayData = chartData.filter((_, index) => index % step === 0);

  const colors = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe',
    '#43e97b', '#fa709a', '#fee140', '#30cfd0', '#330867'
  ];

  return (
    <div className="drawdown-chart">
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={displayData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <defs>
            {tickers.map((ticker, index) => (
              <linearGradient key={ticker} id={`color${index}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors[index % colors.length]} stopOpacity={0.8}/>
                <stop offset="95%" stopColor={colors[index % colors.length]} stopOpacity={0.1}/>
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getFullYear()}`;
            }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            label={{ value: 'Drawdown (%)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
            labelFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleDateString();
            }}
          />
          <Legend />
          {tickers.map((ticker, index) => (
            <Area
              key={ticker}
              type="monotone"
              dataKey={ticker}
              stroke={colors[index % colors.length]}
              fillOpacity={0.6}
              fill={`url(#color${index})`}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default DrawdownChart;

