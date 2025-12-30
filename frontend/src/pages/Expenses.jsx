import React, { useState, useEffect } from 'react';
import { expenseAPI } from '../services/api';
import './Expenses.css';

const CATEGORIES = [
  "Food", "Transport", "Utilities", "Rent/Mortgage", "Car", 
  "Insurance", "Debt/Loans", "School", "Kids", "Entertainment", 
  "Travel", "Saving", "Other"
];

function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    amount: '',
    description: '',
    merchant: '',
    category: '',
    date: new Date().toISOString().split('T')[0]
  });
  const [filters, setFilters] = useState({
    category: '',
    order_by: 'date',
    order_direction: 'desc'
  });

  useEffect(() => {
    fetchExpenses();
  }, [filters]);

  const fetchExpenses = async () => {
    setLoading(true);
    try {
      const response = await expenseAPI.getAll(filters);
      setExpenses(response.data);
    } catch (error) {
      console.error('Error fetching expenses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const dataToSend = {
        ...formData,
        amount: parseFloat(formData.amount),
        date: new Date(formData.date).toISOString(),
        category: formData.category || undefined // Let AI predict if empty
      };

      if (editingId) {
        await expenseAPI.update(editingId, dataToSend);
      } else {
        await expenseAPI.create(dataToSend);
      }

      resetForm();
      fetchExpenses();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to save expense');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (expense) => {
    setFormData({
      amount: expense.amount,
      description: expense.description || '',
      merchant: expense.merchant || '',
      category: expense.category || '',
      date: new Date(expense.date).toISOString().split('T')[0]
    });
    setEditingId(expense.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this expense?')) return;

    try {
      await expenseAPI.delete(id);
      fetchExpenses();
    } catch (error) {
      alert('Failed to delete expense');
    }
  };

  const resetForm = () => {
    setFormData({
      amount: '',
      description: '',
      merchant: '',
      category: '',
      date: new Date().toISOString().split('T')[0]
    });
    setEditingId(null);
    setShowForm(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleFilterChange = (e) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="expenses-container">
      <div className="page-header">
        <h1>Expenses</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? '✖ Cancel' : '➕ Add Expense'}
        </button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="form-card">
          <h2>{editingId ? 'Edit Expense' : 'Add New Expense'}</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Amount *</label>
                <input
                  type="number"
                  name="amount"
                  value={formData.amount}
                  onChange={handleChange}
                  required
                  step="0.01"
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label>Date *</label>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Description *</label>
              <input
                type="text"
                name="description"
                value={formData.description}
                onChange={handleChange}
                required
                placeholder="e.g., Grocery shopping"
              />
            </div>

            <div className="form-group">
              <label>Merchant (Optional)</label>
              <input
                type="text"
                name="merchant"
                value={formData.merchant}
                onChange={handleChange}
                placeholder="e.g., Walmart, Starbucks"
              />
            </div>

            <div className="form-group">
              <label>Category (Optional - AI will predict if empty)</label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
              >
                <option value=""> Let AI Categorize</option>
                {CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <small>Leave empty to let AI predict the category</small>
            </div>

            <div className="form-actions">
              <button type="submit" disabled={loading} className="btn-primary">
                {loading ? 'Saving...' : editingId ? 'Update' : 'Add Expense'}
              </button>
              <button type="button" onClick={resetForm} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="filters-card">
        <div className="filter-group">
          <label>Filter by Category</label>
          <select name="category" value={filters.category} onChange={handleFilterChange}>
            <option value="">All Categories</option>
            {CATEGORIES.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Sort by</label>
          <select name="order_by" value={filters.order_by} onChange={handleFilterChange}>
            <option value="date">Date</option>
            <option value="amount">Amount</option>
            <option value="category">Category</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Order</label>
          <select name="order_direction" value={filters.order_direction} onChange={handleFilterChange}>
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>
        </div>
      </div>

      {/* Expenses List */}
      <div className="expenses-list">
        {loading && <div className="loading">Loading...</div>}
        
        {!loading && expenses.length === 0 && (
          <div className="no-data">
            <p>No expenses yet. Add your first expense!</p>
          </div>
        )}

        {!loading && expenses.length > 0 && (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Merchant</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map(expense => (
                  <tr key={expense.id}>
                    <td>{new Date(expense.date).toLocaleDateString()}</td>
                    <td><strong>{expense.description}</strong></td>
                    <td>{expense.merchant || '-'}</td>
                    <td>
                      <span className="category-badge">{expense.category}</span>
                      {expense.predicted_category && expense.predicted_category !== expense.category && (
                        <span className="ai-badge" title={`AI predicted: ${expense.predicted_category}`}>
                          
                        </span>
                      )}
                    </td>
                    <td className="amount">${expense.amount.toFixed(2)}</td>
                    <td className="actions">
                      <button onClick={() => handleEdit(expense)} className="btn-edit">
                        ✏️
                      </button>
                      <button onClick={() => handleDelete(expense.id)} className="btn-delete">
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Total */}
      {expenses.length > 0 && (
        <div className="total-card">
          <strong>Total:</strong> ${expenses.reduce((sum, exp) => sum + exp.amount, 0).toFixed(2)}
        </div>
      )}
    </div>
  );
}

export default Expenses;