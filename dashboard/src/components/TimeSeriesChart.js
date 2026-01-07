import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import './TimeSeriesChart.css';

function TimeSeriesChart({ data, type = 'prices' }) {
  if (!data || !data.dates) return <div>Loading chart data...</div>;

  const tickers = Object.keys(data[type === 'prices' ? 'prices' : 'returns'] || {});
  
  // Prepare data for Recharts
  const chartData = data.dates.map((date, index) => {
    const point = { date };
    tickers.forEach(ticker => {
      const values = data[type === 'prices' ? 'prices' : 'returns'][ticker];
      if (values && values[index] !== undefined) {
        point[ticker] = values[index];
      }
    });
    return point;
  });

  // Limit data points for performance (show every Nth point)
  const step = Math.max(1, Math.floor(chartData.length / 500));
  const displayData = chartData.filter((_, index) => index % step === 0);

  const colors = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe',
    '#43e97b', '#fa709a', '#fee140', '#30cfd0', '#330867'
  ];

  return (
    <div className="time-series-chart">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={displayData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
            label={{ value: type === 'prices' ? 'Price ($)' : 'Return (%)', angle: -90, position: 'insideLeft' }}
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
            <Line
              key={ticker}
              type="monotone"
              dataKey={ticker}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TimeSeriesChart;

