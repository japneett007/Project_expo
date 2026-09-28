import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { FiUser, FiMail, FiBook, FiTarget, FiSave } from 'react-icons/fi';

export default function Profile() {
  const { user, updateProfile } = useAuth();
  const [form, setForm] = useState({
    name: user?.name || '',
    degree: user?.degree || '',
    branch: user?.branch || '',
    semester: user?.semester || '',
    skillLevel: user?.skillLevel || 'beginner',
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function update(field, value) { setForm(f => ({ ...f, [field]: value })); }

  async function handleSave() {
    setSaving(true);
    try {
      await updateProfile(form);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      alert(err.message);
    }
    setSaving(false);
  }

  return (
    <div className="page-wrapper">
      <div className="container" style={{ maxWidth: 640 }}>
        <div className="section-header animate-in">
          <h1>👤 Profile</h1>
          <p>Manage your account settings</p>
        </div>

        <div className="card animate-in delay-1" style={{ padding: 'var(--space-xl)' }}>
          <div className="form-group">
            <label><FiUser style={{ marginRight: 6 }} /> Name</label>
            <input type="text" className="form-input" value={form.name} onChange={e => update('name', e.target.value)} />
          </div>
          <div className="form-group">
            <label><FiMail style={{ marginRight: 6 }} /> Email</label>
            <input type="email" className="form-input" value={user?.email || ''} disabled style={{ opacity: 0.6 }} />
          </div>
          <div className="form-group">
            <label><FiBook style={{ marginRight: 6 }} /> Degree</label>
            <select className="form-input" value={form.degree} onChange={e => update('degree', e.target.value)}>
              <option value="">Select</option>
              {['B.Tech', 'BCA', 'MCA', 'M.Tech', 'Diploma', 'B.Sc', 'M.Sc', 'Other'].map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Branch</label>
            <input className="form-input" value={form.branch} onChange={e => update('branch', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Semester</label>
            <select className="form-input" value={form.semester} onChange={e => update('semester', e.target.value)}>
              <option value="">Select</option>
              {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={`Semester ${s}`}>Semester {s}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label><FiTarget style={{ marginRight: 6 }} /> Skill Level</label>
            <select className="form-input" value={form.skillLevel} onChange={e => update('skillLevel', e.target.value)}>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>

          <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ width: '100%' }}>
            <FiSave /> {saving ? 'Saving...' : 'Save Changes'}
          </button>

          {saved && (
            <div style={{
              marginTop: 'var(--space-md)', padding: '10px 14px',
              background: 'var(--success-soft)', border: '1px solid rgba(16,185,129,0.3)',
              borderRadius: 'var(--radius-md)', color: 'var(--success)', fontSize: '0.875rem', textAlign: 'center',
            }}>
              ✅ Profile saved successfully
            </div>
          )}
        </div>

        {/* Account Info */}
        <div className="card animate-in delay-2" style={{ padding: 'var(--space-xl)', marginTop: 'var(--space-lg)' }}>
          <h4 style={{ marginBottom: 'var(--space-md)' }}>Account Info</h4>
          <div style={{ display: 'grid', gap: 'var(--space-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>XP</span>
              <strong>{user?.xp || 0}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Completed Projects</span>
              <strong>{user?.completedProjects?.length || 0}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>In Progress</span>
              <strong>{user?.currentProjects?.length || 0}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Achievements</span>
              <strong>{user?.achievements?.length || 0}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Member Since</span>
              <strong>{user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : '—'}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
