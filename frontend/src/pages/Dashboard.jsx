import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectsAPI, achievementsAPI } from '../services/api';
import { FiArrowRight, FiZap, FiAward, FiTrendingUp } from 'react-icons/fi';

export default function Dashboard() {
  const { user } = useAuth();
  const [recommended, setRecommended] = useState([]);
  const [xpData, setXpData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      projectsAPI.recommended().catch(() => ({ recommendations: [] })),
      achievementsAPI.xpSummary().catch(() => null),
    ]).then(([rec, xp]) => {
      setRecommended(rec.recommendations || []);
      setXpData(xp);
      setLoading(false);
    });
  }, []);

  const currentProject = user?.currentProjects?.[0];

  if (loading) return <div className="loading-spinner" />;

  return (
    <div className="page-wrapper">
      <div className="container">
        {/* Welcome */}
        <div className="animate-in" style={{ marginBottom: 'var(--space-2xl)' }}>
          <h1>Welcome back, {user?.name?.split(' ')[0]} 👋</h1>
          <p style={{ fontSize: '1.05rem' }}>Continue building your projects and leveling up</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--space-xl)', alignItems: 'start' }}>
          {/* Left Column */}
          <div>
            {/* Current Project */}
            {currentProject ? (
              <div className="card animate-in delay-1" style={{ marginBottom: 'var(--space-xl)', borderColor: 'var(--primary)', borderWidth: '1px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-md)' }}>
                  <div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>Current Project</p>
                    <h3>{currentProject.projectId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()).replace(/^(Web|Py|Java|Aiml|Ds|Da|Cyber|Fs) \d+/i, '')}</h3>
                  </div>
                  <span className="badge badge-domain" style={{ fontSize: '1.25rem' }}>{currentProject.progress}%</span>
                </div>
                <div className="progress-bar" style={{ marginBottom: 'var(--space-md)' }}>
                  <div className="progress-bar-fill" style={{ width: `${currentProject.progress}%` }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    {currentProject.completedMilestones?.length || 0} of {Object.keys(currentProject.milestones || {}).length} milestones
                  </span>
                  <Link to={`/workspace/${currentProject.projectId}`} className="btn btn-primary btn-sm">
                    Continue Building <FiArrowRight />
                  </Link>
                </div>
              </div>
            ) : (
              <div className="card animate-in delay-1" style={{ marginBottom: 'var(--space-xl)', textAlign: 'center', padding: 'var(--space-2xl)' }}>
                <h3 style={{ marginBottom: 'var(--space-sm)' }}>No Active Project</h3>
                <p style={{ marginBottom: 'var(--space-lg)' }}>Start a project to begin your building journey</p>
                <Link to="/discover" className="btn btn-primary">
                  Discover Projects <FiArrowRight />
                </Link>
              </div>
            )}

            {/* Recommended Projects */}
            <div className="animate-in delay-2">
              <div className="section-header">
                <h3>Recommended for You</h3>
                <p>Based on your interests and skill level</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-md)' }}>
                {recommended.slice(0, 4).map(p => (
                  <Link to={`/project/${p.id}`} key={p.id} className="card" style={{ textDecoration: 'none' }}>
                    <div style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-sm)' }}>
                      <span className={`badge badge-${p.difficulty}`}>{p.difficulty}</span>
                      <span className="badge badge-domain">{p.domain.replace(/-/g, ' ')}</span>
                    </div>
                    <h4 style={{ fontSize: '1rem', marginBottom: 'var(--space-xs)' }}>{p.title}</h4>
                    <p style={{ fontSize: '0.825rem', lineHeight: 1.5 }}>{p.description?.substring(0, 80)}...</p>
                    <div style={{ display: 'flex', gap: 4, marginTop: 'var(--space-sm)', flexWrap: 'wrap' }}>
                      {p.technologies?.slice(0, 3).map(t => <span key={t} className="tag">{t}</span>)}
                    </div>
                  </Link>
                ))}
              </div>
              {recommended.length > 0 && (
                <Link to="/discover" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 'var(--space-md)', fontSize: '0.9rem' }}>
                  View all projects <FiArrowRight size={14} />
                </Link>
              )}
            </div>
          </div>

          {/* Right Column */}
          <div>
            {/* XP Card */}
            <div className="card animate-in delay-2" style={{ marginBottom: 'var(--space-lg)', textAlign: 'center' }}>
              <FiZap size={28} style={{ color: 'var(--primary)', marginBottom: 'var(--space-sm)' }} />
              <h2 style={{ color: 'var(--primary-light)', marginBottom: 4 }}>{user?.xp || 0}</h2>
              <p style={{ fontSize: '0.85rem', marginBottom: 'var(--space-md)' }}>Experience Points</p>
              {xpData?.level && (
                <>
                  <div className="badge badge-domain" style={{ marginBottom: 'var(--space-md)' }}>
                    Level {xpData.level.level} — {xpData.level.name}
                  </div>
                  {xpData.nextLevel && (
                    <>
                      <div className="progress-bar" style={{ marginBottom: 'var(--space-xs)' }}>
                        <div className="progress-bar-fill" style={{ width: `${xpData.progressToNext}%` }} />
                      </div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {xpData.progressToNext}% to Level {xpData.nextLevel.level}
                      </p>
                    </>
                  )}
                </>
              )}
            </div>

            {/* Stats */}
            <div className="card animate-in delay-3" style={{ marginBottom: 'var(--space-lg)' }}>
              <h4 style={{ marginBottom: 'var(--space-md)' }}><FiTrendingUp style={{ marginRight: 6 }} /> Stats</h4>
              <div style={{ display: 'grid', gap: 'var(--space-sm)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Completed</span>
                  <strong>{user?.completedProjects?.length || 0} projects</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>In Progress</span>
                  <strong>{user?.currentProjects?.length || 0} projects</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Active Days</span>
                  <strong>{user?.activeDays?.length || 0} days</strong>
                </div>
              </div>
            </div>

            {/* Quick Links */}
            <div className="card animate-in delay-4">
              <h4 style={{ marginBottom: 'var(--space-md)' }}><FiAward style={{ marginRight: 6 }} /> Quick Links</h4>
              <div style={{ display: 'grid', gap: 'var(--space-sm)' }}>
                <Link to="/achievements" className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}>🏆 Achievements</Link>
                <Link to="/leaderboard" className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}>📊 Leaderboard</Link>
                <Link to="/showcase" className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}>🎨 Showcase</Link>
                <Link to="/profile" className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}>👤 Profile</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
