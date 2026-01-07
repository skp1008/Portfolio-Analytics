import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip
} from 'recharts';
import './ForecastChart.css';

function ForecastChart({ data }) {
  if (!data || !data.predictions) return <div>Loading forecast data...</div>;

  const timeframes = ['tomorrow', 'one_week', 'one_month'];
  const timeframeLabels = {
    'tomorrow': 'Tomorrow',
    'one_week': 'One Week',
    'one_month': 'One Month'
  };

  const getColor = (returnValue) => {
    const num = parseFloat(returnValue.replace('%', ''));
    if (num < 0) {
      // Negative: light red to dark red
      const intensity = Math.min(Math.abs(num) / 25, 1);
      const red = Math.round(255 - (intensity * 100));
      const green = Math.round(200 - (intensity * 150));
      const blue = Math.round(200 - (intensity * 150));
      return `rgb(${red}, ${green}, ${blue})`;
    } else {
      // Positive: light blue to dark blue
      const intensity = Math.min(num / 25, 1);
      const red = Math.round(200 - (intensity * 150));
      const green = Math.round(220 - (intensity * 100));
      const blue = Math.round(255 - (intensity * 50));
      return `rgb(${red}, ${green}, ${blue})`;
    }
  };

  const prepareChartData = (predictions) => {
    return Object.entries(predictions)
      .map(([returnValue, probability]) => ({
        name: returnValue,
        value: (probability * 100).toFixed(1),
        probability: probability
      }))
      .filter(item => item.probability > 0.01); // Only show probabilities > 1%
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="forecast-tooltip">
          <p className="tooltip-label">{`Return: ${payload[0].name}`}</p>
          <p className="tooltip-value">{`Probability: ${payload[0].value}%`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="forecast-chart">
      <div className="forecast-header">
        <h3>Forecast for {data.ticker}</h3>
      </div>
      <div className="forecast-charts-grid">
        {timeframes.map(timeframe => {
          const predictions = data.predictions[timeframe];
          const chartData = prepareChartData(predictions);
          
          return (
            <div key={timeframe} className="forecast-chart-item">
              <h4>{timeframeLabels[timeframe]}</h4>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getColor(entry.name)} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ForecastChart;

