import { useState, useEffect } from 'react';
import { showcaseAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FiExternalLink, FiGithub, FiPlus, FiX } from 'react-icons/fi';

export default function Showcase() {
  const { user } = useAuth();
  const [showcases, setShowcases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    projectId: '', projectName: '', description: '', technologies: '',
    demoUrl: '', githubUrl: '', whatILearned: '', challengesFaced: '',
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    showcaseAPI.list().then(d => { setShowcases(d.showcases || []); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  function updateForm(field, value) { setForm(f => ({ ...f, [field]: value })); }

  async function submitShowcase() {
    setSubmitting(true);
    try {
      await showcaseAPI.submit({
        ...form,
        technologies: form.technologies.split(',').map(t => t.trim()).filter(Boolean),
      });
      setShowForm(false);
      setForm({ projectId: '', projectName: '', description: '', technologies: '', demoUrl: '', githubUrl: '', whatILearned: '', challengesFaced: '' });
      const data = await showcaseAPI.list();
      setShowcases(data.showcases || []);
    } catch (err) { alert(err.message); }
    setSubmitting(false);
  }

  if (loading) return <div className="loading-spinner" />;

  return (
    <div className="page-wrapper">
      <div className="container">
        <div className="section-header animate-in" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1>🎨 Project Showcase</h1>
            <p>See what others have built and share your own work</p>
          </div>
          {user?.completedProjects?.length > 0 && (
            <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
              {showForm ? <><FiX /> Cancel</> : <><FiPlus /> Share Project</>}
            </button>
          )}
        </div>

        {/* Submit Form */}
        {showForm && (
          <div className="card animate-in" style={{ marginBottom: 'var(--space-xl)', padding: 'var(--space-xl)' }}>
            <h3 style={{ marginBottom: 'var(--space-lg)' }}>Share Your Completed Project</h3>
            <div className="grid-2">
              <div className="form-group">
                <label>Project ID (completed)</label>
                <select className="form-input" value={form.projectId} onChange={e => updateForm('projectId', e.target.value)}>
                  <option value="">Select project</option>
                  {user?.completedProjects?.map(pid => <option key={pid} value={pid}>{pid}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Project Name</label>
                <input className="form-input" value={form.projectName} onChange={e => updateForm('projectName', e.target.value)} placeholder="My Awesome Project" />
              </div>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea className="form-input" value={form.description} onChange={e => updateForm('description', e.target.value)} placeholder="What does your project do?" rows={3} />
            </div>
            <div className="form-group">
              <label>Technologies (comma-separated)</label>
              <input className="form-input" value={form.technologies} onChange={e => updateForm('technologies', e.target.value)} placeholder="React, Python, Flask" />
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label>Demo URL</label>
                <input className="form-input" value={form.demoUrl} onChange={e => updateForm('demoUrl', e.target.value)} placeholder="https://..." />
              </div>
              <div className="form-group">
                <label>GitHub URL</label>
                <input className="form-input" value={form.githubUrl} onChange={e => updateForm('githubUrl', e.target.value)} placeholder="https://github.com/..." />
              </div>
            </div>
            <div className="form-group">
              <label>What I Learned</label>
              <textarea className="form-input" value={form.whatILearned} onChange={e => updateForm('whatILearned', e.target.value)} placeholder="Key takeaways..." rows={2} />
            </div>
            <div className="form-group">
              <label>Challenges Faced</label>
              <textarea className="form-input" value={form.challengesFaced} onChange={e => updateForm('challengesFaced', e.target.value)} placeholder="Biggest challenges..." rows={2} />
            </div>
            <button className="btn btn-primary" onClick={submitShowcase} disabled={submitting || !form.projectId}>
              {submitting ? 'Submitting...' : 'Submit to Showcase'}
            </button>
          </div>
        )}

        {/* Showcase Grid */}
        {showcases.length === 0 ? (
          <div className="empty-state animate-in delay-1">
            <h3>No showcases yet</h3>
            <p>Complete a project and be the first to share your work!</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: 'var(--space-lg)' }}>
            {showcases.map((s, i) => (
              <div key={s.id} className="card animate-in" style={{ animationDelay: `${i * 80}ms` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-md)' }}>
                  <div>
                    <h3 style={{ fontSize: '1.125rem' }}>{s.projectName || s.projectId}</h3>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>by {s.userName}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                    {s.demoUrl && <a href={s.demoUrl} target="_blank" rel="noopener noreferrer" title="Demo"><FiExternalLink /></a>}
                    {s.githubUrl && <a href={s.githubUrl} target="_blank" rel="noopener noreferrer" title="GitHub"><FiGithub /></a>}
                  </div>
                </div>
                <p style={{ fontSize: '0.9rem', lineHeight: 1.6, marginBottom: 'var(--space-md)' }}>{s.description}</p>
                {s.technologies?.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 'var(--space-md)' }}>
                    {s.technologies.map(t => <span key={t} className="tag">{t}</span>)}
                  </div>
                )}
                {s.whatILearned && (
                  <div style={{ padding: 'var(--space-sm) var(--space-md)', background: 'var(--surface-2)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-sm)' }}>
                    <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>💡 What I Learned</p>
                    <p style={{ fontSize: '0.825rem' }}>{s.whatILearned}</p>
                  </div>
                )}
                {s.challengesFaced && (
                  <div style={{ padding: 'var(--space-sm) var(--space-md)', background: 'var(--surface-2)', borderRadius: 'var(--radius-md)' }}>
                    <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>🔥 Challenges</p>
                    <p style={{ fontSize: '0.825rem' }}>{s.challengesFaced}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
