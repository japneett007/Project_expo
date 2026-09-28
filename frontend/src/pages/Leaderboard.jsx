import { useState, useEffect } from 'react';
import { leaderboardAPI, projectsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FiAward, FiZap } from 'react-icons/fi';

export default function Leaderboard() {
  const { user } = useAuth();
  const [entries, setEntries] = useState([]);
  const [type, setType] = useState('global');
  const [branches, setBranches] = useState([]);
  const [domains, setDomains] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectsAPI.branches().then(d => setBranches(d.branches)).catch(() => {});
    projectsAPI.domains().then(d => setDomains(d.domains)).catch(() => {});
    loadLeaderboard();
  }, []);

  useEffect(() => { loadLeaderboard(); }, [type, selectedBranch, selectedDomain]);

  async function loadLeaderboard() {
    setLoading(true);
    try {
      const params = new URLSearchParams({ type });
      if (type === 'branch' && selectedBranch) params.set('branch', selectedBranch);
      if (type === 'domain' && selectedDomain) params.set('domain', selectedDomain);
      const data = await leaderboardAPI.get(params.toString());
      setEntries(data.leaderboard || []);
    } catch { setEntries([]); }
    setLoading(false);
  }

  function getRankStyle(rank) {
    if (rank === 1) return { color: '#FFD700', fontWeight: 800 };
    if (rank === 2) return { color: '#C0C0C0', fontWeight: 700 };
    if (rank === 3) return { color: '#CD7F32', fontWeight: 700 };
    return {};
  }

  function getRankEmoji(rank) {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  }

  return (
    <div className="page-wrapper">
      <div className="container" style={{ maxWidth: 800 }}>
        <div className="section-header animate-in">
          <h1>📊 Leaderboard</h1>
          <p>See how you rank against other builders</p>
        </div>

        {/* Filter Tabs */}
        <div className="animate-in delay-1" style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-lg)', flexWrap: 'wrap' }}>
          {['global', 'branch', 'domain'].map(t => (
            <button key={t} className={`btn btn-sm ${type === t ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setType(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
          {type === 'branch' && (
            <select className="form-input" style={{ width: 200, padding: '6px 12px', fontSize: '0.85rem' }}
              value={selectedBranch} onChange={e => setSelectedBranch(e.target.value)}>
              <option value="">All branches</option>
              {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          )}
          {type === 'domain' && (
            <select className="form-input" style={{ width: 200, padding: '6px 12px', fontSize: '0.85rem' }}
              value={selectedDomain} onChange={e => setSelectedDomain(e.target.value)}>
              <option value="">All domains</option>
              {domains.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          )}
        </div>

        {/* Leaderboard Table */}
        {loading ? <div className="loading-spinner" /> : entries.length === 0 ? (
          <div className="empty-state"><h3>No entries yet</h3><p>Complete projects to appear on the leaderboard</p></div>
        ) : (
          <div className="animate-in delay-2">
            {entries.map((entry, i) => (
              <div key={entry.userId} className="card" style={{
                marginBottom: 'var(--space-sm)', padding: 'var(--space-md) var(--space-lg)',
                display: 'flex', alignItems: 'center', gap: 'var(--space-md)',
                background: entry.userId === user?.id ? 'var(--surface-3)' : 'var(--surface-card)',
                borderColor: entry.userId === user?.id ? 'var(--primary)' : 'var(--border)',
              }}>
                <span style={{ ...getRankStyle(entry.rank), fontSize: '1.25rem', minWidth: 40, textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
                  {getRankEmoji(entry.rank)}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-bright)' }}>
                    {entry.name} {entry.userId === user?.id && <span style={{ fontSize: '0.75rem', color: 'var(--primary-light)' }}>(You)</span>}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Level {entry.level} — {entry.levelName} • {entry.completedProjects} projects
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--primary-light)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    <FiZap size={16} /> {entry.xp}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>XP</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
