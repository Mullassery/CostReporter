import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts';
import axios from 'axios';
import { format, parseISO } from 'date-fns';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Dashboard = ({ token }) => {
  const [costSummary, setCostSummary] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [trends, setTrends] = useState(null);
  const [budgetStatus, setBudgetStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('30d');
  const [forecastDays, setForecastDays] = useState(30);

  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  useEffect(() => {
    fetchDashboardData();
  }, [selectedPeriod, token]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, forecastRes, trendsRes, budgetRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/costs/summary`, { headers }),
        axios.get(`${API_BASE_URL}/api/forecast/costs`, {
          headers,
          params: { forecast_days: forecastDays, period: selectedPeriod, algorithm: 'ensemble' }
        }),
        axios.get(`${API_BASE_URL}/api/forecast/trends`, {
          headers,
          params: { period: selectedPeriod }
        }),
        axios.get(`${API_BASE_URL}/api/forecast/budget`, {
          headers,
          params: { forecast_days: forecastDays }
        })
      ]);

      setCostSummary(summaryRes.data);
      setForecast(forecastRes.data);
      setTrends(trendsRes.data);
      setBudgetStatus(budgetRes.data);
    } catch (err) {
      setError(err.message);
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!forecast || !forecast.forecast_points) return [];

    return forecast.forecast_points.map(point => ({
      date: format(parseISO(point.date), 'MMM dd'),
      predicted: Number(point.predicted_cost.toFixed(2)),
      lower: Number(point.lower_bound.toFixed(2)),
      upper: Number(point.upper_bound.toFixed(2))
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="animate-spin">
          <div className="h-12 w-12 border-t-2 border-blue-600 border-solid rounded-full"></div>
        </div>
        <p className="ml-4 text-gray-600">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">💰 PyCostAudit Dashboard</h1>
            <div className="flex gap-2">
              {['7d', '30d', '90d'].map(period => (
                <button
                  key={period}
                  onClick={() => setSelectedPeriod(period)}
                  className={`px-4 py-2 rounded font-medium transition ${
                    selectedPeriod === period
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                  }`}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            Error: {error}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <SummaryCard
            title="Today's Cost"
            value={`$${costSummary?.total_today.toFixed(2) || '0.00'}`}
            icon="📅"
          />
          <SummaryCard
            title="7-Day Total"
            value={`$${costSummary?.total_7d.toFixed(2) || '0.00'}`}
            icon="📊"
          />
          <SummaryCard
            title="30-Day Total"
            value={`$${costSummary?.total_30d.toFixed(2) || '0.00'}`}
            icon="📈"
          />
          <SummaryCard
            title="Projected Monthly"
            value={`$${forecast?.summary?.total_projected.toFixed(2) || '0.00'}`}
            icon="🎯"
            highlight={true}
          />
        </div>

        {/* Budget Status */}
        {budgetStatus && !budgetStatus.error && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">📍 Budget Status</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatBox label="Budget" value={`$${budgetStatus.budget_amount.toFixed(2)}`} />
              <StatBox label="Spent" value={`$${budgetStatus.current_spend.toFixed(2)}`} />
              <StatBox label="Projected" value={`$${budgetStatus.projected_total.toFixed(2)}`} />
              <StatBox
                label="Usage"
                value={`${budgetStatus.percent_of_budget.toFixed(1)}%`}
                color={budgetStatus.percent_of_budget > 90 ? 'red' : budgetStatus.percent_of_budget > 75 ? 'yellow' : 'green'}
              />
            </div>
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${
                    budgetStatus.percent_of_budget > 90
                      ? 'bg-red-600'
                      : budgetStatus.percent_of_budget > 75
                      ? 'bg-yellow-500'
                      : 'bg-green-600'
                  }`}
                  style={{ width: `${Math.min(budgetStatus.percent_of_budget, 100)}%` }}
                ></div>
              </div>
              <p className={`mt-2 text-sm font-semibold ${
                budgetStatus.will_exceed_budget ? 'text-red-600' : 'text-green-600'
              }`}>
                {budgetStatus.recommendation}
              </p>
            </div>
          </div>
        )}

        {/* Forecast Chart */}
        {forecast && forecast.forecast_points && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold">📈 Cost Forecast</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {forecast.algorithm.toUpperCase()} | MAPE: {(forecast.metrics.mape * 100).toFixed(1)}% | Trend: {forecast.metrics.trend}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Model Accuracy</p>
                <p className="text-lg font-bold">{((1 - forecast.metrics.mape) * 100).toFixed(1)}%</p>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={prepareChartData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="lower"
                  fill="#e0e7ff"
                  stroke="none"
                  name="95% Confidence Range"
                  isAnimationActive={false}
                />
                <Area
                  type="monotone"
                  dataKey="upper"
                  fill="none"
                  stroke="none"
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ fill: '#2563eb', r: 4 }}
                  activeDot={{ r: 6 }}
                  name="Predicted Cost"
                />
              </ComposedChart>
            </ResponsiveContainer>

            {/* Forecast Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <StatBox
                label="Avg Daily"
                value={`$${forecast.summary?.average_daily.toFixed(2) || '0.00'}`}
              />
              <StatBox
                label="Min Daily"
                value={`$${forecast.summary?.min_projected.toFixed(2) || '0.00'}`}
              />
              <StatBox
                label="Max Daily"
                value={`$${forecast.summary?.max_projected.toFixed(2) || '0.00'}`}
              />
              <StatBox
                label="Forecast Span"
                value={`${forecast.summary?.days_forecast || 0} days`}
              />
            </div>
          </div>
        )}

        {/* Trend Analysis */}
        {trends && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">📊 Trend Analysis</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <StatBox label="Total Cost" value={`$${trends.total_cost.toFixed(2)}`} />
              <StatBox label="Avg Daily" value={`$${trends.average_daily.toFixed(2)}`} />
              <StatBox label="Min Daily" value={`$${trends.min_daily.toFixed(2)}`} />
              <StatBox label="Max Daily" value={`$${trends.max_daily.toFixed(2)}`} />
              <StatBox
                label="Growth Rate"
                value={`${trends.growth_rate.toFixed(1)}%`}
                color={trends.growth_rate > 0 ? 'red' : 'green'}
              />
            </div>
            <div className="mt-4">
              <p className="text-lg font-semibold text-gray-900">{trends.trend}</p>
              {trends.week_over_week_change !== null && (
                <p className="text-sm text-gray-600 mt-1">
                  Week-over-week: {trends.week_over_week_change > 0 ? '+' : ''}{trends.week_over_week_change.toFixed(1)}%
                </p>
              )}
            </div>
          </div>
        )}

        {/* Anomalies */}
        {forecast?.anomalies && forecast.anomalies.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">⚠️ Cost Anomalies Detected</h2>
            <div className="space-y-2">
              {forecast.anomalies.map((anomaly, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <span className="font-medium text-gray-900">{anomaly.date}</span>
                  <span className="text-yellow-700">Z-score: {anomaly.anomaly_score.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const SummaryCard = ({ title, value, icon, highlight }) => (
  <div className={`rounded-lg p-6 ${highlight ? 'bg-blue-50 border-2 border-blue-200' : 'bg-white border border-gray-200 shadow'}`}>
    <p className="text-gray-600 text-sm font-medium">{title}</p>
    <p className="text-3xl font-bold text-gray-900 mt-2">{icon} {value}</p>
  </div>
);

const StatBox = ({ label, value, color }) => (
  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
    <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">{label}</p>
    <p className={`text-lg font-bold mt-1 ${
      color === 'red' ? 'text-red-600' :
      color === 'yellow' ? 'text-yellow-600' :
      color === 'green' ? 'text-green-600' :
      'text-gray-900'
    }`}>{value}</p>
  </div>
);

export default Dashboard;
