import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { FiClock, FiCheck, FiAlertTriangle, FiArrowRight, FiBookOpen, FiCode, FiTarget } from 'react-icons/fi';

export default function ProjectDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    projectsAPI.get(id).then(d => { setProject(d.project); setLoading(false); }).catch(() => { setLoading(false); });
  }, [id]);

  async function startProject() {
    setStarting(true);
    try {
      await projectsAPI.start(id);
      navigate(`/workspace/${id}`);
    } catch (err) {
      alert(err.message);
    } finally {
      setStarting(false);
    }
  }

  if (loading) return <div className="loading-spinner" />;
  if (!project) return <div className="empty-state"><h3>Project not found</h3></div>;

  const prereqs = project.prerequisiteDetails || { required: [], recommended: [] };

  return (
    <div className="page-wrapper">
      <div className="container" style={{ maxWidth: 900 }}>
        {/* Header */}
        <div className="animate-in" style={{ marginBottom: 'var(--space-2xl)' }}>
          <div style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-md)', flexWrap: 'wrap' }}>
            <span className={`badge badge-${project.difficulty}`}>{project.difficulty}</span>
            <span className="badge badge-domain">{project.type}</span>
            <span className="badge badge-domain">Level {project.level}</span>
          </div>
          <h1>{project.title}</h1>
          <p style={{ fontSize: '1.1rem', marginTop: 'var(--space-md)' }}>{project.description}</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--space-xl)', alignItems: 'start' }}>
          {/* Left */}
          <div>
            {/* Why Build This */}
            <div className="card animate-in delay-1" style={{ marginBottom: 'var(--space-lg)' }}>
              <h3 style={{ marginBottom: 'var(--space-md)' }}><FiTarget style={{ marginRight: 8, color: 'var(--primary)' }} />Why Build This?</h3>
              <p style={{ lineHeight: 1.7 }}>{project.whyBuildThis}</p>
            </div>

            {/* What You'll Learn */}
            <div className="card animate-in delay-2" style={{ marginBottom: 'var(--space-lg)' }}>
              <h3 style={{ marginBottom: 'var(--space-md)' }}><FiBookOpen style={{ marginRight: 8, color: 'var(--primary)' }} />What You'll Learn</h3>
              <ul style={{ listStyle: 'none', display: 'grid', gap: 'var(--space-sm)' }}>
                {project.whatYouLearn?.map((w, i) => (
                  <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', color: 'var(--text-secondary)' }}>
                    <FiCheck style={{ color: 'var(--success)', flexShrink: 0 }} /> {w}
                  </li>
                ))}
              </ul>
            </div>

            {/* Prerequisites */}
            {(prereqs.required.length > 0 || prereqs.recommended.length > 0) && (
              <div className="card animate-in delay-3" style={{ marginBottom: 'var(--space-lg)' }}>
                <h3 style={{ marginBottom: 'var(--space-md)' }}>Prerequisites</h3>
                {prereqs.required.length > 0 && (
                  <div style={{ marginBottom: 'var(--space-md)' }}>
                    <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-sm)' }}>Required:</p>
                    {prereqs.required.map((r, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, color: 'var(--success)', fontSize: '0.9rem' }}>
                        <FiCheck /> {r}
                      </div>
                    ))}
                  </div>
                )}
                {prereqs.recommended.length > 0 && (
                  <div>
                    <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-sm)' }}>Recommended:</p>
                    {prereqs.recommended.map((r, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, color: 'var(--warning)', fontSize: '0.9rem' }}>
                        <FiAlertTriangle size={14} /> {r}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Milestones / Roadmap */}
            <div className="card animate-in delay-4">
              <h3 style={{ marginBottom: 'var(--space-md)' }}><FiCode style={{ marginRight: 8, color: 'var(--primary)' }} />Project Roadmap</h3>
              <div style={{ display: 'grid', gap: 'var(--space-sm)' }}>
                {project.milestoneIds?.map((mid, i) => (
                  <div key={mid} style={{
                    display: 'flex', alignItems: 'center', gap: 'var(--space-md)',
                    padding: 'var(--space-sm) var(--space-md)',
                    background: 'var(--surface-2)', borderRadius: 'var(--radius-md)',
                  }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)', minWidth: 28 }}>{String(i + 1).padStart(2, '0')}</span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      {mid.split('-').slice(2).join(' ').replace(/^m\d+\s*/, '').replace(/\b\w/g, l => l.toUpperCase()) || `Milestone ${i + 1}`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div>
            <div className="card" style={{ position: 'sticky', top: 90 }}>
              <div style={{ textAlign: 'center', marginBottom: 'var(--space-lg)' }}>
                <button className="btn btn-primary btn-lg" onClick={startProject} disabled={starting} style={{ width: '100%' }}>
                  {starting ? 'Starting...' : 'Start Project'} <FiArrowRight />
                </button>
              </div>

              <div style={{ display: 'grid', gap: 'var(--space-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Domain</span>
                  <strong>{project.domain?.replace(/-/g, ' ')}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Difficulty</span>
                  <strong className={`badge badge-${project.difficulty}`}>{project.difficulty}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Estimated</span>
                  <strong><FiClock size={14} style={{ marginRight: 4 }} />{project.estimatedHours}h</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Milestones</span>
                  <strong>{project.milestoneIds?.length || 0}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Level</span>
                  <strong>{project.level}</strong>
                </div>
              </div>

              <div style={{ marginTop: 'var(--space-lg)' }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 'var(--space-sm)' }}>Technologies</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {project.technologies?.map(t => <span key={t} className="tag">{t}</span>)}
                </div>
              </div>

              <div style={{ marginTop: 'var(--space-lg)' }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 'var(--space-sm)' }}>Branches</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {project.branches?.map(b => <span key={b} className="tag">{b}</span>)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
