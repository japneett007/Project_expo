import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiZap, FiUser, FiMail, FiLock } from 'react-icons/fi';

export default function Register() {
  const { register } = useAuth();
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function update(field, value) { setForm(f => ({ ...f, [field]: value })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirmPassword) { setError('Passwords do not match'); return; }
    if (form.password.length < 8) { setError('Password must be at least 8 characters'); return; }
    setLoading(true);
    try {
      await register(form.name, form.email, form.password, form.confirmPassword);
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
          <h2 style={{ marginTop: 'var(--space-md)' }}>Create Account</h2>
          <p>Start building real projects today</p>
        </div>

        <div className="card" style={{ padding: 'var(--space-xl)' }}>
          {error && <div style={{ padding: '10px 14px', background: 'var(--error-soft)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-md)', color: 'var(--error)', fontSize: '0.875rem', marginBottom: 'var(--space-lg)' }}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label><FiUser style={{ marginRight: 6 }} />Full Name</label>
              <input type="text" className="form-input" value={form.name} onChange={e => update('name', e.target.value)} placeholder="Your name" required />
            </div>
            <div className="form-group">
              <label><FiMail style={{ marginRight: 6 }} />Email</label>
              <input type="email" className="form-input" value={form.email} onChange={e => update('email', e.target.value)} placeholder="you@example.com" required />
            </div>
            <div className="form-group">
              <label><FiLock style={{ marginRight: 6 }} />Password</label>
              <input type="password" className="form-input" value={form.password} onChange={e => update('password', e.target.value)} placeholder="Min 8 characters" required />
            </div>
            <div className="form-group">
              <label><FiLock style={{ marginRight: 6 }} />Confirm Password</label>
              <input type="password" className="form-input" value={form.confirmPassword} onChange={e => update('confirmPassword', e.target.value)} placeholder="Re-enter password" required />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Creating account...' : 'Start Building'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: 'var(--space-lg)', fontSize: '0.875rem' }}>
            Already have an account? <Link to="/login">Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
