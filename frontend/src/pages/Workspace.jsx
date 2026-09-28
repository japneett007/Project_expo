import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { milestonesAPI, copilotAPI, projectsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FiCheck, FiLock, FiPlay, FiMessageCircle, FiX, FiSend, FiChevronRight } from 'react-icons/fi';

export default function Workspace() {
  const { id } = useParams();
  const { refreshUser } = useAuth();
  const [project, setProject] = useState(null);
  const [milestones, setMilestones] = useState([]);
  const [progress, setProgress] = useState(0);
  const [selectedMilestone, setSelectedMilestone] = useState(null);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [toast, setToast] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => { loadData(); }, [id]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatMessages]);

  async function loadData() {
    try {
      const [projData, msData] = await Promise.all([
        projectsAPI.get(id),
        milestonesAPI.getForProject(id),
      ]);
      setProject(projData.project);
      setMilestones(msData.milestones || []);
      setProgress(msData.progress || 0);
      // Auto-select first available milestone
      const available = msData.milestones?.find(m => m.status === 'available' || m.status === 'in-progress');
      if (available) setSelectedMilestone(available);
    } catch (err) {
      console.error(err);
    }
  }

  async function completeMilestone(milestoneId) {
    setCompleting(true);
    try {
      const result = await milestonesAPI.complete(milestoneId);
      showToast(result.motivationMessage, 'success');
      await loadData();
      await refreshUser();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setCompleting(false);
    }
  }

  async function sendChat() {
    if (!chatInput.trim() || chatLoading) return;
    const message = chatInput;
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: message }]);
    setChatLoading(true);

    try {
      const result = await copilotAPI.chat({
        message,
        projectId: id,
        milestoneId: selectedMilestone?.id || '',
        stage: 'explanation',
        history: chatMessages,
      });
      setChatMessages(prev => [...prev, { role: 'assistant', content: result.response }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I had trouble responding. Please try again.' }]);
    } finally {
      setChatLoading(false);
    }
  }

  function showToast(message, type = 'success') {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  }

  function getStatusIcon(status) {
    switch (status) {
      case 'completed': return <FiCheck className="status-completed" />;
      case 'available': return <FiPlay className="status-available" />;
      case 'in-progress': return <FiPlay className="status-in-progress" />;
      default: return <FiLock className="status-locked" />;
    }
  }

  if (!project) return <div className="loading-spinner" />;

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 70px)', overflow: 'hidden' }}>
      {/* Milestone Sidebar */}
      <div style={{
        width: 300, background: 'var(--bg-dark)', borderRight: '1px solid var(--border)',
        overflowY: 'auto', flexShrink: 0, padding: 'var(--space-lg)',
      }}>
        <h4 style={{ marginBottom: 'var(--space-sm)' }}>{project.title}</h4>
        <div className="progress-bar" style={{ marginBottom: 'var(--space-xs)' }}>
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 'var(--space-lg)' }}>{progress}% complete</p>

        <div style={{ display: 'grid', gap: 2 }}>
          {milestones.map((m, i) => (
            <button key={m.id}
              onClick={() => m.status !== 'locked' && setSelectedMilestone(m)}
              disabled={m.status === 'locked'}
              style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-sm)',
                padding: '10px 12px', background: selectedMilestone?.id === m.id ? 'var(--surface-3)' : 'transparent',
                border: 'none', borderRadius: 'var(--radius-md)', cursor: m.status === 'locked' ? 'not-allowed' : 'pointer',
                width: '100%', textAlign: 'left', color: m.status === 'locked' ? 'var(--text-muted)' : 'var(--text-primary)',
                fontFamily: 'var(--font-main)', fontSize: '0.85rem', transition: 'background 0.15s',
                opacity: m.status === 'locked' ? 0.5 : 1,
              }}
            >
              {getStatusIcon(m.status)}
              <span style={{ flex: 1 }}>{m.title || `Milestone ${i + 1}`}</span>
              {selectedMilestone?.id === m.id && <FiChevronRight size={14} />}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-xl)' }}>
        {selectedMilestone ? (
          <div style={{ maxWidth: 800 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-xl)' }}>
              <div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
                  Current Milestone
                </p>
                <h2>{selectedMilestone.title || 'Milestone'}</h2>
              </div>
              {selectedMilestone.status !== 'completed' && (
                <button className="btn btn-primary" onClick={() => completeMilestone(selectedMilestone.id)} disabled={completing}>
                  {completing ? 'Completing...' : 'Mark Complete'} <FiCheck />
                </button>
              )}
              {selectedMilestone.status === 'completed' && (
                <span className="badge badge-beginner" style={{ fontSize: '0.85rem', padding: '8px 16px' }}>✅ Completed</span>
              )}
            </div>

            {/* Milestone Content */}
            <div style={{ display: 'grid', gap: 'var(--space-lg)' }}>
              {selectedMilestone.objective && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--primary-light)' }}>🎯 Objective</h4>
                  <p>{selectedMilestone.objective}</p>
                </div>
              )}
              {selectedMilestone.why && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--primary-light)' }}>❓ Why?</h4>
                  <p>{selectedMilestone.why}</p>
                </div>
              )}
              {selectedMilestone.concept && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--primary-light)' }}>💡 Concept</h4>
                  <p>{selectedMilestone.concept}</p>
                </div>
              )}
              {selectedMilestone.explanation && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--primary-light)' }}>📖 Explanation</h4>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{selectedMilestone.explanation}</p>
                </div>
              )}
              {selectedMilestone.implementation && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--primary-light)' }}>🔨 Implementation</h4>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{selectedMilestone.implementation}</p>
                </div>
              )}
              {selectedMilestone.expectedResult && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--primary-light)' }}>✅ Expected Result</h4>
                  <p>{selectedMilestone.expectedResult}</p>
                </div>
              )}
              {selectedMilestone.verification && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--primary-light)' }}>🔍 Verification</h4>
                  <p>{selectedMilestone.verification}</p>
                </div>
              )}
              {selectedMilestone.commonErrors && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--warning)' }}>⚠️ Common Errors</h4>
                  <ul style={{ listStyle: 'none', display: 'grid', gap: 6 }}>
                    {(Array.isArray(selectedMilestone.commonErrors) ? selectedMilestone.commonErrors : [selectedMilestone.commonErrors]).map((e, i) => (
                      <li key={i} style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>• {e}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Fallback when no detailed content */}
              {!selectedMilestone.objective && !selectedMilestone.concept && (
                <div className="card" style={{ textAlign: 'center', padding: 'var(--space-2xl)' }}>
                  <h3 style={{ marginBottom: 'var(--space-sm)' }}>Ready to build this milestone</h3>
                  <p style={{ marginBottom: 'var(--space-lg)' }}>
                    Open your project in VS Code and implement this step. When done, click "Mark Complete" above.
                  </p>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Need help? Open the AI Copilot →
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <h3>Select a milestone</h3>
            <p>Click a milestone from the sidebar to view its content</p>
          </div>
        )}
      </div>

      {/* Copilot Toggle Button */}
      {!copilotOpen && (
        <button onClick={() => setCopilotOpen(true)}
          style={{
            position: 'fixed', right: 24, bottom: 24,
            width: 56, height: 56, borderRadius: '50%',
            background: 'var(--primary)',
            border: 'none', cursor: 'pointer', color: '#fff',
            boxShadow: 'var(--shadow-lg)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'transform 0.2s', zIndex: 50,
          }}
          title="Open AI Copilot"
        >
          <FiMessageCircle size={24} />
        </button>
      )}

      {/* AI Copilot Panel */}
      {copilotOpen && (
        <div style={{
          width: 380, background: 'var(--bg-dark)', borderLeft: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', flexShrink: 0,
        }}>
          {/* Header */}
          <div style={{
            padding: 'var(--space-md) var(--space-lg)', borderBottom: '1px solid var(--border)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <h4 style={{ fontSize: '0.95rem' }}>🤖 AI Copilot</h4>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Project-aware assistance</p>
            </div>
            <button onClick={() => setCopilotOpen(false)} style={{
              background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer',
            }}><FiX size={20} /></button>
          </div>

          {/* Chat Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-md)' }}>
            {chatMessages.length === 0 && (
              <div style={{ textAlign: 'center', padding: 'var(--space-2xl) var(--space-md)', color: 'var(--text-muted)' }}>
                <FiMessageCircle size={32} style={{ marginBottom: 'var(--space-md)', opacity: 0.5 }} />
                <p style={{ fontSize: '0.9rem', marginBottom: 'var(--space-sm)' }}>Ask me anything about your project</p>
                <p style={{ fontSize: '0.8rem' }}>I understand your current project context and can help with code, concepts, and debugging.</p>
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div key={i} style={{
                marginBottom: 'var(--space-md)',
                display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}>
                <div style={{
                  maxWidth: '85%', padding: '10px 14px',
                  background: msg.role === 'user' ? 'var(--primary)' : 'var(--surface-3)',
                  borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                  fontSize: '0.875rem', lineHeight: 1.6,
                  color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                  whiteSpace: 'pre-wrap',
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 'var(--space-md)' }}>
                <div style={{ padding: '10px 14px', background: 'var(--surface-3)', borderRadius: '14px', fontSize: '0.875rem' }}>
                  <span style={{ animation: 'pulse 1.5s infinite' }}>Thinking...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat Input */}
          <div style={{
            padding: 'var(--space-md)', borderTop: '1px solid var(--border)',
            display: 'flex', gap: 'var(--space-sm)',
          }}>
            <input
              type="text" className="form-input" placeholder="Ask about your project..."
              value={chatInput} onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendChat()}
              style={{ flex: 1, fontSize: '0.85rem' }}
            />
            <button className="btn btn-primary btn-sm" onClick={sendChat} disabled={chatLoading || !chatInput.trim()}>
              <FiSend size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
