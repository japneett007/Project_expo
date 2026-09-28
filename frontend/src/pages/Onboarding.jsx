import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectsAPI } from '../services/api';
import { FiArrowRight, FiArrowLeft, FiCheck } from 'react-icons/fi';

const degrees = ['B.Tech', 'BCA', 'MCA', 'M.Tech', 'Diploma', 'B.Sc', 'M.Sc', 'Other'];
const skillLevels = [
  { id: 'beginner', name: 'Beginner', desc: 'I am just starting with programming' },
  { id: 'intermediate', name: 'Intermediate', desc: 'I know basics and have built some small projects' },
  { id: 'advanced', name: 'Advanced', desc: 'I have significant project experience' },
];
const goals = [
  'Learn programming', 'Build college projects', 'Build portfolio',
  'Prepare for internships', 'Prepare for placements',
];

export default function Onboarding() {
  const { updateProfile } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [branches, setBranches] = useState([]);
  const [domains, setDomains] = useState([]);
  const [form, setForm] = useState({
    degree: '', branch: '', semester: '', skillLevel: 'beginner',
    interestedDomains: [], goals: [],
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    projectsAPI.branches().then(d => setBranches(d.branches)).catch(() => {});
    projectsAPI.domains().then(d => setDomains(d.domains)).catch(() => {});
  }, []);

  function update(field, value) { setForm(f => ({ ...f, [field]: value })); }

  function toggleArray(field, value) {
    setForm(f => {
      const arr = f[field];
      return { ...f, [field]: arr.includes(value) ? arr.filter(v => v !== value) : [...arr, value] };
    });
  }

  async function finish() {
    setLoading(true);
    try {
      await updateProfile({ ...form, onboardingComplete: true });
      navigate('/dashboard');
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  }

  const totalSteps = 4;

  return (
    <div className="page-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '100%', maxWidth: 560 }}>
        {/* Progress */}
        <div style={{ marginBottom: 'var(--space-xl)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <span>Step {step} of {totalSteps}</span>
            <span>{Math.round(step / totalSteps * 100)}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${step / totalSteps * 100}%` }} />
          </div>
        </div>

        <div className="card" style={{ padding: 'var(--space-xl)' }}>
          {/* Step 1: Academic */}
          {step === 1 && (
            <>
              <h3 style={{ marginBottom: 'var(--space-lg)' }}>📚 Academic Background</h3>
              <div className="form-group">
                <label>Degree</label>
                <select className="form-input" value={form.degree} onChange={e => update('degree', e.target.value)}>
                  <option value="">Select degree</option>
                  {degrees.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Branch</label>
                <select className="form-input" value={form.branch} onChange={e => update('branch', e.target.value)}>
                  <option value="">Select branch</option>
                  {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Semester / Year</label>
                <select className="form-input" value={form.semester} onChange={e => update('semester', e.target.value)}>
                  <option value="">Select</option>
                  {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={`Semester ${s}`}>Semester {s}</option>)}
                </select>
              </div>
            </>
          )}

          {/* Step 2: Skill Level */}
          {step === 2 && (
            <>
              <h3 style={{ marginBottom: 'var(--space-lg)' }}>🎯 Skill Level</h3>
              <div style={{ display: 'grid', gap: 'var(--space-md)' }}>
                {skillLevels.map(s => (
                  <div key={s.id}
                    onClick={() => update('skillLevel', s.id)}
                    className="card"
                    style={{
                      cursor: 'pointer',
                      borderColor: form.skillLevel === s.id ? 'var(--primary)' : 'var(--border)',
                      background: form.skillLevel === s.id ? 'var(--surface-3)' : 'var(--surface-card)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h4>{s.name}</h4>
                        <p style={{ fontSize: '0.875rem' }}>{s.desc}</p>
                      </div>
                      {form.skillLevel === s.id && <FiCheck size={20} style={{ color: 'var(--primary)' }} />}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Step 3: Interests */}
          {step === 3 && (
            <>
              <h3 style={{ marginBottom: 'var(--space-lg)' }}>💡 Interested Domains</h3>
              <p style={{ marginBottom: 'var(--space-md)', fontSize: '0.875rem' }}>Select all that interest you</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-sm)' }}>
                {domains.map(d => (
                  <div key={d.id}
                    onClick={() => toggleArray('interestedDomains', d.id)}
                    className="card"
                    style={{
                      cursor: 'pointer', padding: 'var(--space-md)',
                      borderColor: form.interestedDomains.includes(d.id) ? 'var(--primary)' : 'var(--border)',
                      background: form.interestedDomains.includes(d.id) ? 'var(--surface-3)' : 'var(--surface-card)',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontSize: '1.5rem', marginBottom: 4 }}>{d.icon}</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>{d.name}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Step 4: Goals */}
          {step === 4 && (
            <>
              <h3 style={{ marginBottom: 'var(--space-lg)' }}>🚀 Your Goals</h3>
              <div style={{ display: 'grid', gap: 'var(--space-sm)' }}>
                {goals.map(g => (
                  <div key={g}
                    onClick={() => toggleArray('goals', g)}
                    className="card"
                    style={{
                      cursor: 'pointer', padding: 'var(--space-md)',
                      borderColor: form.goals.includes(g) ? 'var(--primary)' : 'var(--border)',
                      background: form.goals.includes(g) ? 'var(--surface-3)' : 'var(--surface-card)',
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    }}
                  >
                    <span style={{ color: 'var(--text-primary)' }}>{g}</span>
                    {form.goals.includes(g) && <FiCheck size={18} style={{ color: 'var(--primary)' }} />}
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-xl)' }}>
            {step > 1 ? (
              <button className="btn btn-ghost" onClick={() => setStep(s => s - 1)}>
                <FiArrowLeft /> Back
              </button>
            ) : <div />}
            {step < totalSteps ? (
              <button className="btn btn-primary" onClick={() => setStep(s => s + 1)}>
                Next <FiArrowRight />
              </button>
            ) : (
              <button className="btn btn-primary" onClick={finish} disabled={loading}>
                {loading ? 'Setting up...' : 'Complete Setup'} <FiCheck />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
