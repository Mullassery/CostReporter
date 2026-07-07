import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import Dashboard from './Dashboard';
import LoginPage from './LoginPage';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [token, setToken] = useState(localStorage.getItem('pycostaudit_token'));
  const [isAuthenticated, setIsAuthenticated] = useState(!!token);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setLoading(false);
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Token verification failed:', error);
      localStorage.removeItem('pycostaudit_token');
      setToken(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (newToken, userData) => {
    localStorage.setItem('pycostaudit_token', newToken);
    setToken(newToken);
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('pycostaudit_token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="h-12 w-12 border-t-2 border-blue-600 border-solid rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/" />
            ) : (
              <LoginPage onLogin={handleLogin} />
            )
          }
        />
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <DashboardLayout user={user} onLogout={handleLogout} token={token} />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </Router>
  );
}

const DashboardLayout = ({ user, onLogout, token }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-600">PyCostAudit</h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm">
                <p className="text-gray-900 font-medium">{user?.name}</p>
                <p className="text-gray-600">{user?.email}</p>
              </div>
              <button
                onClick={onLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <Dashboard token={token} />
    </div>
  );
};

export default App;
