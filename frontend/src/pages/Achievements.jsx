import { useState, useEffect } from 'react';
import { achievementsAPI } from '../services/api';
import { FiLock } from 'react-icons/fi';

export default function Achievements() {
  const [achievements, setAchievements] = useState([]);
  const [newlyUnlocked, setNewlyUnlocked] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    achievementsAPI.list().then(d => {
      setAchievements(d.achievements || []);
      setNewlyUnlocked(d.newlyUnlocked || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner" />;

  const unlocked = achievements.filter(a => a.unlocked);
  const locked = achievements.filter(a => !a.unlocked);

  return (
    <div className="page-wrapper">
      <div className="container">
        <div className="section-header animate-in">
          <h1>🏆 Achievements</h1>
          <p>{unlocked.length} of {achievements.length} unlocked</p>
        </div>

        {newlyUnlocked.length > 0 && (
          <div className="card animate-in delay-1" style={{
            marginBottom: 'var(--space-xl)', textAlign: 'center',
            background: 'var(--violet)',
            borderColor: 'var(--primary)',
          }}>
            <h3 style={{ marginBottom: 'var(--space-sm)', color: 'var(--primary-light)' }}>🎉 New Achievement{newlyUnlocked.length > 1 ? 's' : ''} Unlocked!</h3>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
              {newlyUnlocked.map(id => {
                const ach = achievements.find(a => a.id === id);
                return ach ? <span key={id} style={{ fontSize: '1.25rem' }}>{ach.icon} {ach.name}</span> : null;
              })}
            </div>
          </div>
        )}

        {/* Unlocked */}
        {unlocked.length > 0 && (
          <div className="animate-in delay-2" style={{ marginBottom: 'var(--space-2xl)' }}>
            <h3 style={{ marginBottom: 'var(--space-lg)' }}>Unlocked</h3>
            <div className="grid-3">
              {unlocked.map(a => (
                <div key={a.id} className="card" style={{ textAlign: 'center', borderColor: 'var(--primary)' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-sm)' }}>{a.icon}</div>
                  <h4 style={{ marginBottom: 4 }}>{a.name}</h4>
                  <p style={{ fontSize: '0.825rem', marginBottom: 'var(--space-sm)' }}>{a.description}</p>
                  <span className="badge badge-domain">+{a.xpReward} XP</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Locked */}
        {locked.length > 0 && (
          <div className="animate-in delay-3">
            <h3 style={{ marginBottom: 'var(--space-lg)', color: 'var(--text-muted)' }}>
              <FiLock style={{ marginRight: 6 }} /> Locked
            </h3>
            <div className="grid-3">
              {locked.map(a => (
                <div key={a.id} className="card" style={{ textAlign: 'center', opacity: 0.5 }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-sm)', filter: 'grayscale(1)' }}>{a.icon}</div>
                  <h4 style={{ marginBottom: 4 }}>{a.name}</h4>
                  <p style={{ fontSize: '0.825rem', marginBottom: 'var(--space-sm)' }}>{a.description}</p>
                  <span className="badge badge-domain">+{a.xpReward} XP</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
