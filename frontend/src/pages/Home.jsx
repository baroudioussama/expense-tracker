import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { financialAPI, expenseAPI } from '../services/api';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid
} from 'recharts';
import './Home.css';

/* ---------- Helpers ---------- */
const formatMoney = (value) =>
  typeof value === 'number' ? value.toFixed(2) : '0.00';

const formatMonth = (month) =>
  new Date(month).toLocaleString('default', {
    month: 'short',
    year: 'numeric'
  });

const COLORS = [
  '#667eea',
  '#764ba2',
  '#f093fb',
  '#4facfe',
  '#43e97b',
  '#fa709a',
  '#fee140',
  '#30cfd0'
];

function Home() {
  const [overview, setOverview] = useState(null);
  const [summary, setSummary] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewRes, summaryRes, monthlyRes] = await Promise.all([
        financialAPI.getOverview(),
        expenseAPI.getSummary(),
        expenseAPI.getMonthlyStats()
      ]);

      setOverview(overviewRes.data);
      setSummary(summaryRes.data);
      setMonthlyStats(monthlyRes.data);
    } catch (err) {
      console.error(err);
      setError('Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  /* ---------- Memoized Chart Data ---------- */
  const pieData = useMemo(() => {
    return summary.map(item => ({
      name: item.category,
      value: item.total
    }));
  }, [summary]);

  /* ---------- UI States ---------- */
  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="loading">{error}</div>;
  }

  return (
    <div className="home-container">
      {/* Header */}
      <header>
        <h1>Dashboard</h1>
        <p>Your financial overview</p>
      </header>

      {/* Quick Actions at Top */}
      <section className="quick-actions">
        <Link to="/expenses">➕ Add Expense</Link>
        <Link to="/income">💵 Add Income</Link>
        <Link to="/recommendations">💡 View Recommendations</Link>
      </section>

      {/* Stats */}
      <section className="stats-section">
        <p>Total Income: ${formatMoney(overview?.total_income)}</p>
        <p>Total Expenses: ${formatMoney(overview?.total_expenses)}</p>
        <p>
          Balance: ${formatMoney(overview?.balance)}{' '}
          {overview?.balance >= 0 ? '📈' : '📉'}
        </p>
        <p>Savings Rate: {overview?.savings_rate?.toFixed(1) || 0}%</p>
      </section>

      {/* Charts */}
      <section>
        <h2>Expenses by Category</h2>
        {pieData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, percent }) =>
                  `${name}: ${(percent * 100).toFixed(0)}%`
                }
              >
                {pieData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => `$${formatMoney(v)}`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <p>No expense data available.</p>
        )}
      </section>

      <section>
        <h2>Monthly Spending Trend</h2>
        {monthlyStats.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tickFormatter={formatMonth} />
              <YAxis />
              <Tooltip formatter={(v) => `$${formatMoney(v)}`} />
              <Bar dataKey="total_expenses" fill="#667eea" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p>No monthly data available.</p>
        )}
      </section>

      {/* Table */}
      {summary.length > 0 && (
        <section>
          <h2>Category Breakdown</h2>
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Transactions</th>
                <th>Total</th>
                <th>% of Total</th>
              </tr>
            </thead>
            <tbody>
              {summary.map((item, index) => {
                const percentage =
                  overview?.total_expenses > 0
                    ? (item.total / overview.total_expenses) * 100
                    : 0;

                return (
                  <tr key={index}>
                    <td>{item.category}</td>
                    <td>{item.count}</td>
                    <td>${formatMoney(item.total)}</td>
                    <td>{percentage.toFixed(1)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

export default Home;