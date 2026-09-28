import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiZap, FiMail, FiLock } from 'react-icons/fi';

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
          <FiZap size={36} style={{ color: 'var(--primary)' }} />
          <h2 style={{ marginTop: 'var(--space-md)' }}>Welcome Back</h2>
          <p>Continue building your projects</p>
        </div>

        <div className="card" style={{ padding: 'var(--space-xl)' }}>
          {error && <div style={{ padding: '10px 14px', background: 'var(--error-soft)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-md)', color: 'var(--error)', fontSize: '0.875rem', marginBottom: 'var(--space-lg)' }}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label><FiMail style={{ marginRight: 6 }} />Email</label>
              <input type="email" className="form-input" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
            </div>
            <div className="form-group">
              <label><FiLock style={{ marginRight: 6 }} />Password</label>
              <input type="password" className="form-input" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: 'var(--space-lg)', fontSize: '0.875rem' }}>
            Don't have an account? <Link to="/register">Register</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
