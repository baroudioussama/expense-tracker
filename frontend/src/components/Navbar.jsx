import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import './Navbar.css';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
           Expense Tracker
        </Link>
        
        <ul className="nav-menu">
          <li className="nav-item">
            <Link to="/" className="nav-link">Dashboard</Link>
          </li>
          <li className="nav-item">
            <Link to="/expenses" className="nav-link">Expenses</Link>
          </li>
          <li className="nav-item">
            <Link to="/income" className="nav-link">Income</Link>
          </li>
          <li className="nav-item">
            <Link to="/recommendations" className="nav-link">Recommendations</Link>
          </li>
        </ul>

        <div className="nav-user">
          <span className="user-name"> {user?.full_name}</span>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;