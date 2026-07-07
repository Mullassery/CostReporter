import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const LoginPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        // Login
        const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
          email,
          password
        });
        onLogin(response.data.token, response.data.user);
      } else {
        // Register
        const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
          email,
          password,
          name
        });
        // Auto-login after registration
        onLogin(response.data.id, response.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-blue-600 mb-2">💰 PyCostAudit</h1>
            <p className="text-gray-600">Real-time LLM cost tracking & ML forecasting</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Your name"
                  required={!isLogin}
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg transition"
            >
              {loading ? 'Loading...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Toggle */}
          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError(null);
                }}
                className="text-blue-600 hover:text-blue-700 font-semibold"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>

          {/* Demo Credentials */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm">
            <p className="font-semibold text-blue-900 mb-2">Demo Credentials:</p>
            <p className="text-blue-800 text-xs">
              Email: demo@pycostaudit.com<br/>
              Password: demo123
            </p>
          </div>
        </div>

        {/* Features */}
        <div className="mt-8 text-white text-center">
          <h3 className="text-lg font-semibold mb-4">Features</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-2xl mb-2">📊</p>
              <p>Real-time Cost Tracking</p>
            </div>
            <div>
              <p className="text-2xl mb-2">🤖</p>
              <p>ML Cost Forecasting</p>
            </div>
            <div>
              <p className="text-2xl mb-2">📈</p>
              <p>Budget Projections</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
