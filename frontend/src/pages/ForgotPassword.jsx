import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../services/api';
import './Auth.css';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [step, setStep] = useState(1); // 1: request token, 2: reset password
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRequestToken = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const response = await authAPI.forgotPassword(email);
      setMessage(response.data.message);
      // In development, the token is returned in response
      if (response.data.reset_token) {
        setResetToken(response.data.reset_token);
        setMessage(`Reset token: ${response.data.reset_token} (In production, this would be sent via email)`);
      }
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      setLoading(false);
      return;
    }

    try {
      await authAPI.resetPassword({ token: resetToken, new_password: newPassword });
      setMessage('Password reset successfully! You can now login with your new password.');
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>💰 Expense Tracker</h1>
        <h2>Reset Password</h2>

        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}

        {step === 1 ? (
          // Step 1: Request Reset Token
          <form onSubmit={handleRequestToken}>
            <p className="reset-instruction">
              Enter your email address and we'll send you a reset token.
            </p>
            
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="your@email.com"
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Sending...' : 'Send Reset Token'}
            </button>
          </form>
        ) : (
          // Step 2: Reset Password with Token
          <form onSubmit={handleResetPassword}>
            <div className="form-group">
              <label>Reset Token</label>
              <input
                type="text"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                required
                placeholder="Enter the token you received"
              />
              <small>Copy the token from above or check your email (in production)</small>
            </div>

            <div className="form-group">
              <label>New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                placeholder="••••••••"
                minLength="8"
              />
              <small>At least 8 characters</small>
            </div>

            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>

            <button 
              type="button" 
              onClick={() => setStep(1)} 
              className="btn-secondary"
              style={{ marginTop: '10px' }}
            >
              Back to Email Entry
            </button>
          </form>
        )}

        <p className="auth-link">
          Remember your password? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
}

export default ForgotPassword;