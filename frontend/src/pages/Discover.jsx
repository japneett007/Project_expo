import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { FiSearch, FiFilter, FiClock } from 'react-icons/fi';

export default function Discover() {
  const [projects, setProjects] = useState([]);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ domain: '', difficulty: '', branch: '', type: '', search: '' });

  useEffect(() => {
    projectsAPI.domains().then(d => setDomains(d.domains)).catch(() => {});
    loadProjects();
  }, []);

  useEffect(() => { loadProjects(); }, [filters]);

  async function loadProjects() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.domain) params.set('domain', filters.domain);
      if (filters.difficulty) params.set('difficulty', filters.difficulty);
      if (filters.branch) params.set('branch', filters.branch);
      if (filters.type) params.set('type', filters.type);
      if (filters.search) params.set('search', filters.search);
      const data = await projectsAPI.list(params.toString());
      setProjects(data.projects || []);
    } catch { setProjects([]); }
    setLoading(false);
  }

  function updateFilter(key, value) {
    setFilters(f => ({ ...f, [key]: value }));
  }

  return (
    <div className="page-wrapper">
      <div className="container">
        <div className="section-header animate-in">
          <h1>Discover Projects</h1>
          <p>Find your next project across 8 technology domains</p>
        </div>

        {/* Search & Filters */}
        <div className="animate-in delay-1" style={{ marginBottom: 'var(--space-xl)' }}>
          <div style={{ display: 'flex', gap: 'var(--space-md)', marginBottom: 'var(--space-md)', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 250, position: 'relative' }}>
              <FiSearch style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input type="text" className="form-input" placeholder="Search projects, technologies..." value={filters.search}
                onChange={e => updateFilter('search', e.target.value)}
                style={{ paddingLeft: 40 }}
              />
            </div>
            <select className="form-input" style={{ width: 180 }} value={filters.domain} onChange={e => updateFilter('domain', e.target.value)}>
              <option value="">All Domains</option>
              {domains.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
            <select className="form-input" style={{ width: 180 }} value={filters.difficulty} onChange={e => updateFilter('difficulty', e.target.value)}>
              <option value="">All Levels</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
            <select className="form-input" style={{ width: 180 }} value={filters.type} onChange={e => updateFilter('type', e.target.value)}>
              <option value="">All Types</option>
              <option value="Mini Project">Mini Project</option>
              <option value="Academic Project">Academic Project</option>
              <option value="Portfolio Project">Portfolio Project</option>
              <option value="Industry-style Project">Industry-style</option>
              <option value="Capstone">Capstone</option>
            </select>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <FiFilter style={{ marginRight: 4 }} /> {projects.length} projects found
          </p>
        </div>

        {/* Domain Quick Filters */}
        <div className="animate-in delay-2" style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-xl)', flexWrap: 'wrap' }}>
          <button className={`btn btn-sm ${!filters.domain ? 'btn-primary' : 'btn-ghost'}`} onClick={() => updateFilter('domain', '')}>
            All
          </button>
          {domains.map(d => (
            <button key={d.id} className={`btn btn-sm ${filters.domain === d.id ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => updateFilter('domain', d.id)}>
              {d.icon} {d.name}
            </button>
          ))}
        </div>

        {/* Project Grid */}
        {loading ? (
          <div className="loading-spinner" />
        ) : projects.length === 0 ? (
          <div className="empty-state">
            <h3>No projects found</h3>
            <p>Try adjusting your filters</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 'var(--space-lg)' }}>
            {projects.map((p, i) => (
              <Link to={`/project/${p.id}`} key={p.id} className="card animate-in" style={{ textDecoration: 'none', animationDelay: `${(i % 6) * 50}ms` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-md)' }}>
                  <div style={{ display: 'flex', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
                    <span className={`badge badge-${p.difficulty}`}>{p.difficulty}</span>
                    <span className="badge badge-domain">{p.type || p.domain.replace(/-/g, ' ')}</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Lv.{p.level}</span>
                </div>
                <h3 style={{ fontSize: '1.125rem', marginBottom: 'var(--space-sm)' }}>{p.title}</h3>
                <p style={{ fontSize: '0.875rem', lineHeight: 1.6, marginBottom: 'var(--space-md)' }}>
                  {p.description?.substring(0, 120)}...
                </p>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 'var(--space-md)' }}>
                  {p.technologies?.map(t => <span key={t} className="tag">{t}</span>)}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  <FiClock size={14} /> ~{p.estimatedHours}h • {p.milestoneIds?.length || 0} milestones
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
