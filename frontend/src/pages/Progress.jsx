import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { achievementsAPI } from '../services/api';
import { FiAward, FiZap, FiTrendingUp } from 'react-icons/fi';

export default function Progress() {
  const { user } = useAuth();
  const [xpData, setXpData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    achievementsAPI.xpSummary().then(d => { setXpData(d); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner" />;

  const currentProjects = user?.currentProjects || [];
  const completedProjects = user?.completedProjects || [];

  return (
    <div className="page-wrapper">
      <div className="container">
        <div className="section-header animate-in">
          <h1>Your Progress</h1>
          <p>Track your journey from beginner to developer</p>
        </div>

        {/* XP Overview */}
        <div className="grid-3 animate-in delay-1" style={{ marginBottom: 'var(--space-2xl)' }}>
          <div className="card" style={{ textAlign: 'center' }}>
            <FiZap size={28} style={{ color: 'var(--primary)', marginBottom: 'var(--space-sm)' }} />
            <h2 style={{ color: 'var(--primary-light)' }}>{user?.xp || 0}</h2>
            <p style={{ fontSize: '0.85rem' }}>Total XP</p>
            {xpData?.level && <div className="badge badge-domain" style={{ marginTop: 'var(--space-sm)' }}>Level {xpData.level.level} — {xpData.level.name}</div>}
          </div>
          <div className="card" style={{ textAlign: 'center' }}>
            <FiAward size={28} style={{ color: 'var(--success)', marginBottom: 'var(--space-sm)' }} />
            <h2 style={{ color: 'var(--success)' }}>{completedProjects.length}</h2>
            <p style={{ fontSize: '0.85rem' }}>Projects Completed</p>
          </div>
          <div className="card" style={{ textAlign: 'center' }}>
            <FiTrendingUp size={28} style={{ color: 'var(--warning)', marginBottom: 'var(--space-sm)' }} />
            <h2 style={{ color: 'var(--warning)' }}>{user?.activeDays?.length || 0}</h2>
            <p style={{ fontSize: '0.85rem' }}>Active Days</p>
          </div>
        </div>

        {/* Level Progress */}
        {xpData?.nextLevel && (
          <div className="card animate-in delay-2" style={{ marginBottom: 'var(--space-2xl)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-sm)' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{xpData.level?.name}</span>
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{xpData.nextLevel.name}</span>
            </div>
            <div className="progress-bar" style={{ height: 12 }}>
              <div className="progress-bar-fill" style={{ width: `${xpData.progressToNext}%` }} />
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 'var(--space-xs)', textAlign: 'center' }}>
              {xpData.progressToNext}% to next level • {xpData.nextLevel.minXP - (user?.xp || 0)} XP needed
            </p>
          </div>
        )}

        {/* Current Projects */}
        {currentProjects.length > 0 && (
          <div className="animate-in delay-3">
            <h3 style={{ marginBottom: 'var(--space-lg)' }}>In Progress ({currentProjects.length})</h3>
            <div className="grid-2" style={{ marginBottom: 'var(--space-2xl)' }}>
              {currentProjects.map(cp => (
                <div key={cp.projectId} className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)' }}>
                    {cp.projectId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h4>
                  <div className="progress-bar" style={{ marginBottom: 'var(--space-xs)' }}>
                    <div className="progress-bar-fill" style={{ width: `${cp.progress}%` }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <span>{cp.completedMilestones?.length || 0}/{Object.keys(cp.milestones || {}).length} milestones</span>
                    <span>{cp.progress}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Completed Projects */}
        {completedProjects.length > 0 && (
          <div className="animate-in delay-4">
            <h3 style={{ marginBottom: 'var(--space-lg)' }}>Completed ({completedProjects.length})</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
              {completedProjects.map(pid => (
                <div key={pid} className="badge badge-beginner" style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
                  ✅ {pid.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {currentProjects.length === 0 && completedProjects.length === 0 && (
          <div className="empty-state">
            <h3>No projects yet</h3>
            <p>Start a project from the Discover page to begin tracking your progress</p>
          </div>
        )}
      </div>
    </div>
  );
}
