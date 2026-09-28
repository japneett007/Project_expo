import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiZap, FiLogOut, FiMenu, FiX } from 'react-icons/fi';
import { useState } from 'react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (path) => location.pathname === path ? 'active' : '';

  if (!user) {
    return (
      <nav className="navbar">
        <div className="navbar-inner">
          <Link to="/" className="navbar-logo">
            <FiZap size={22} />
            <span>Project Hub</span>
          </Link>
          <div className="navbar-links">
            <Link to="/login" className={isActive('/login')}>Login</Link>
            <Link to="/register" className="btn btn-primary btn-sm">Start Building</Link>
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/dashboard" className="navbar-logo">
          <FiZap size={22} />
          <span>Project Hub</span>
        </Link>

        <div className={`navbar-links ${menuOpen ? 'open' : ''}`}>
          <Link to="/dashboard" className={isActive('/dashboard')}>Dashboard</Link>
          <Link to="/discover" className={isActive('/discover')}>Discover</Link>
          <Link to="/progress" className={isActive('/progress')}>Progress</Link>
          <Link to="/community" className={isActive('/community')}>Community</Link>
          <Link to="/showcase" className={isActive('/showcase')}>Showcase</Link>
          <Link to="/leaderboard" className={isActive('/leaderboard')}>Leaderboard</Link>
        </div>

        <div className="navbar-user">
          <div className="navbar-xp">
            <FiZap size={14} />
            {user.xp || 0} XP
          </div>
          <Link to="/profile" style={{ color: 'var(--text-primary)', fontSize: '0.875rem', fontWeight: 500 }}>
            {user.name?.split(' ')[0]}
          </Link>
          <button onClick={logout} className="btn btn-ghost btn-sm" title="Logout">
            <FiLogOut size={16} />
          </button>
        </div>

        <button className="mobile-menu-toggle" onClick={() => setMenuOpen(!menuOpen)}
          style={{ display: 'none', background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}>
          {menuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
        </button>
      </div>
    </nav>
  );
}
