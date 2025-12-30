import React, { useState, useEffect } from 'react';
import { incomeAPI } from '../services/api';
import './Income.css';

const INCOME_SOURCES = [
  "Salary", "Freelance", "Business", "Investment", 
  "Rental", "Gift", "Bonus", "Other"
];

function Income() {
  const [incomes, setIncomes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    amount: '',
    source: 'Salary',
    description: '',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchIncomes();
  }, []);

  const fetchIncomes = async () => {
    setLoading(true);
    try {
      const response = await incomeAPI.getAll();
      setIncomes(response.data);
    } catch (error) {
      console.error('Error fetching incomes:', error);
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
        date: new Date(formData.date).toISOString()
      };

      if (editingId) {
        await incomeAPI.update(editingId, dataToSend);
      } else {
        await incomeAPI.create(dataToSend);
      }

      resetForm();
      fetchIncomes();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to save income');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (income) => {
    setFormData({
      amount: income.amount,
      source: income.source,
      description: income.description || '',
      date: new Date(income.date).toISOString().split('T')[0]
    });
    setEditingId(income.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this income?')) return;

    try {
      await incomeAPI.delete(id);
      fetchIncomes();
    } catch (error) {
      alert('Failed to delete income');
    }
  };

  const resetForm = () => {
    setFormData({
      amount: '',
      source: 'Salary',
      description: '',
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

  return (
    <div className="income-container">
      <div className="page-header">
        <h1>Income</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? '✖ Cancel' : '➕ Add Income'}
        </button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="form-card">
          <h2>{editingId ? 'Edit Income' : 'Add New Income'}</h2>
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
              <label>Source *</label>
              <select
                name="source"
                value={formData.source}
                onChange={handleChange}
                required
              >
                {INCOME_SOURCES.map(source => (
                  <option key={source} value={source}>{source}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Description (Optional)</label>
              <input
                type="text"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="e.g., Monthly salary, Freelance project"
              />
            </div>

            <div className="form-actions">
              <button type="submit" disabled={loading} className="btn-primary">
                {loading ? 'Saving...' : editingId ? 'Update' : 'Add Income'}
              </button>
              <button type="button" onClick={resetForm} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Income List */}
      <div className="income-list">
        {loading && <div className="loading">Loading...</div>}
        
        {!loading && incomes.length === 0 && (
          <div className="no-data">
            <p>No income records yet. Add your first income!</p>
          </div>
        )}

        {!loading && incomes.length > 0 && (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Source</th>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {incomes.map(income => (
                  <tr key={income.id}>
                    <td>{new Date(income.date).toLocaleDateString()}</td>
                    <td><span className="source-badge">{income.source}</span></td>
                    <td>{income.description || '-'}</td>
                    <td className="amount-positive">${income.amount.toFixed(2)}</td>
                    <td className="actions">
                      <button onClick={() => handleEdit(income)} className="btn-edit">
                        ✏️
                      </button>
                      <button onClick={() => handleDelete(income.id)} className="btn-delete">
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
      {incomes.length > 0 && (
        <div className="total-card positive">
          <strong>Total Income:</strong> ${incomes.reduce((sum, inc) => sum + inc.amount, 0).toFixed(2)}
        </div>
      )}
    </div>
  );
}

export default Income;