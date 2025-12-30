import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { financialAPI } from '../services/api';
import './Recommendations.css';

function Recommendations() {
  const [recommendations, setRecommendations] = useState(null);
  const [budgetSuggestions, setBudgetSuggestions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      const [recsRes, budgetRes] = await Promise.all([
        financialAPI.getRecommendations(),
        financialAPI.getBudgetSuggestions()
      ]);
      setRecommendations(recsRes.data);
      setBudgetSuggestions(budgetRes.data);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading recommendations...</div>;
  }

  // Check if user has no data
  const hasNoData = recommendations?.total_income === 0 && recommendations?.total_expenses === 0;

  if (hasNoData) {
    return (
      <div className="recommendations-container">
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h1>No Financial Data Yet</h1>
          <p>Start tracking your finances to get personalized AI-powered recommendations!</p>
          
          <div className="empty-steps">
            <div className="step-card">
              <div className="step-number">1</div>
              <h3>Add Your Income</h3>
              <p>Track your salary, freelance work, or other income sources</p>
              <Link to="/income" className="step-btn">
                💵 Add Income
              </Link>
            </div>

            <div className="step-card">
              <div className="step-number">2</div>
              <h3>Track Your Expenses</h3>
              <p>Log your daily expenses with AI auto-categorization</p>
              <Link to="/expenses" className="step-btn">
                💸 Add Expense
              </Link>
            </div>

            <div className="step-card">
              <div className="step-number">3</div>
              <h3>Get Insights</h3>
              <p>Receive personalized recommendations and budget suggestions</p>
              <button className="step-btn disabled" disabled>
                💡 Coming Soon
              </button>
            </div>
          </div>

          <div className="empty-tips">
            <h3>💡 Quick Tips</h3>
            <ul>
              <li>Start by adding your monthly income</li>
              <li>Track expenses for at least a week to get accurate insights</li>
              <li>Let AI categorize your expenses automatically</li>
              <li>Check back here for personalized recommendations</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'priority-high';
      case 'medium': return 'priority-medium';
      case 'low': return 'priority-low';
      default: return '';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'success': return '✅';
      case 'info': return 'ℹ️';
      case 'insight': return '💡';
      default: return '📌';
    }
  };

  const getHealthColor = (level) => {
    switch (level) {
      case 'Excellent': return 'health-excellent';
      case 'Good': return 'health-good';
      case 'Fair': return 'health-fair';
      default: return 'health-poor';
    }
  };

  return (
    <div className="recommendations-container">
      <div className="page-header">
        <h1>Financial Recommendations</h1>
        <p>AI-powered insights to improve your financial health</p>
      </div>

      {/* Financial Health Score */}
      {recommendations && (
        <div className={`health-card ${getHealthColor(recommendations.health_level)}`}>
          <div className="health-score">
            <div className="score-circle">
              <svg viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#e0e0e0" strokeWidth="10"/>
                <circle 
                  cx="50" 
                  cy="50" 
                  r="45" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="10"
                  strokeDasharray={`${recommendations.financial_health_score * 2.83} 283`}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div className="score-text">
                <span className="score-number">{recommendations.financial_health_score}</span>
                <span className="score-label">/100</span>
              </div>
            </div>
            <div className="health-info">
              <h2>Financial Health: {recommendations.health_level}</h2>
              <div className="health-stats">
                <div className="stat">
                  <span className="stat-label">Income:</span>
                  <span className="stat-value">${recommendations.total_income?.toFixed(2)}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Expenses:</span>
                  <span className="stat-value expense">${recommendations.total_expenses?.toFixed(2)}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Savings Rate:</span>
                  <span className="stat-value">{recommendations.savings_rate}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Spending Trend */}
      {recommendations?.spending_trend && (
        <div className="trend-card">
          <h3>📊 Spending Trend</h3>
          <div className="trend-comparison">
            <div className="trend-item">
              <span className="trend-label">Last Month:</span>
              <span className="trend-value">${recommendations.spending_trend.last_month?.toFixed(2)}</span>
            </div>
            <div className="trend-arrow">
              {recommendations.spending_trend.change_percentage > 0 ? '📈' : '📉'}
            </div>
            <div className="trend-item">
              <span className="trend-label">Previous Month:</span>
              <span className="trend-value">${recommendations.spending_trend.previous_month?.toFixed(2)}</span>
            </div>
          </div>
          <p className={`trend-change ${recommendations.spending_trend.change_percentage > 0 ? 'negative' : 'positive'}`}>
            {Math.abs(recommendations.spending_trend.change_percentage)}% 
            {recommendations.spending_trend.change_percentage > 0 ? ' increase' : ' decrease'}
          </p>
        </div>
      )}

      {/* Recommendations List */}
      <div className="recommendations-grid">
        {recommendations?.recommendations?.length > 0 ? (
          recommendations.recommendations.map((rec, index) => (
            <div key={index} className={`recommendation-card ${getPriorityColor(rec.priority)}`}>
              <div className="rec-header">
                <span className="rec-icon">{getTypeIcon(rec.type)}</span>
                <h3>{rec.title}</h3>
              </div>
              <p className="rec-message">{rec.message}</p>
              <div className="rec-action">
                <strong>Action:</strong> {rec.action}
              </div>
              <span className={`rec-priority ${rec.priority}`}>
                {rec.priority.toUpperCase()} PRIORITY
              </span>
            </div>
          ))
        ) : null}
      </div>

      {/* Budget Suggestions (50-30-20 Rule) */}
      {budgetSuggestions?.suggested_budget && (
        <div className="budget-card">
          <h2>💡 Suggested Budget Plan</h2>
          <p className="budget-subtitle">Based on the 50-30-20 Rule</p>
          
          <div className="budget-grid">
            <div className="budget-item needs">
              <div className="budget-percentage">50%</div>
              <h3>Needs</h3>
              <p className="budget-amount">${budgetSuggestions.suggested_budget.needs.amount.toFixed(2)}</p>
              <p className="budget-description">{budgetSuggestions.suggested_budget.needs.description}</p>
              <ul className="budget-categories">
                {budgetSuggestions.suggested_budget.needs.categories.map((cat, i) => (
                  <li key={i}>{cat}</li>
                ))}
              </ul>
            </div>

            <div className="budget-item wants">
              <div className="budget-percentage">30%</div>
              <h3>Wants</h3>
              <p className="budget-amount">${budgetSuggestions.suggested_budget.wants.amount.toFixed(2)}</p>
              <p className="budget-description">{budgetSuggestions.suggested_budget.wants.description}</p>
              <ul className="budget-categories">
                {budgetSuggestions.suggested_budget.wants.categories.map((cat, i) => (
                  <li key={i}>{cat}</li>
                ))}
              </ul>
            </div>

            <div className="budget-item savings">
              <div className="budget-percentage">20%</div>
              <h3>Savings</h3>
              <p className="budget-amount">${budgetSuggestions.suggested_budget.savings.amount.toFixed(2)}</p>
              <p className="budget-description">{budgetSuggestions.suggested_budget.savings.description}</p>
              <ul className="budget-categories">
                {budgetSuggestions.suggested_budget.savings.categories.map((cat, i) => (
                  <li key={i}>{cat}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recommendations;