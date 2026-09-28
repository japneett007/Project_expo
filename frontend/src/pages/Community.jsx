import { useState, useEffect } from 'react';
import { communityAPI, projectsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FiMessageCircle, FiThumbsUp, FiSend } from 'react-icons/fi';

export default function Community() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [discussions, setDiscussions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newPost, setNewPost] = useState({ title: '', content: '' });
  const [posting, setPosting] = useState(false);
  const [replyTo, setReplyTo] = useState(null);
  const [replyContent, setReplyContent] = useState('');

  useEffect(() => {
    // Load projects for filter
    projectsAPI.list().then(d => setProjects(d.projects || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedProject) loadDiscussions();
  }, [selectedProject]);

  async function loadDiscussions() {
    setLoading(true);
    try {
      const data = await communityAPI.getDiscussions(selectedProject);
      setDiscussions(data.discussions || []);
    } catch { setDiscussions([]); }
    setLoading(false);
  }

  async function submitPost() {
    if (!newPost.content || !selectedProject) return;
    setPosting(true);
    try {
      await communityAPI.post(selectedProject, { title: newPost.title, content: newPost.content });
      setNewPost({ title: '', content: '' });
      loadDiscussions();
    } catch (err) { alert(err.message); }
    setPosting(false);
  }

  async function submitReply(parentId) {
    if (!replyContent) return;
    try {
      await communityAPI.post(selectedProject, { content: replyContent, parentId });
      setReplyTo(null);
      setReplyContent('');
      loadDiscussions();
    } catch (err) { alert(err.message); }
  }

  async function handleUpvote(discussionId) {
    try {
      await communityAPI.upvote(discussionId);
      loadDiscussions();
    } catch (err) { alert(err.message); }
  }

  const topLevel = discussions.filter(d => !d.parentId);
  const getReplies = (parentId) => discussions.filter(d => d.parentId === parentId);

  return (
    <div className="page-wrapper">
      <div className="container" style={{ maxWidth: 800 }}>
        <div className="section-header animate-in">
          <h1>💬 Community</h1>
          <p>Discuss projects, share solutions, and help each other</p>
        </div>

        {/* Project Selector */}
        <div className="animate-in delay-1" style={{ marginBottom: 'var(--space-xl)' }}>
          <select className="form-input" value={selectedProject} onChange={e => setSelectedProject(e.target.value)}>
            <option value="">Select a project to view discussions</option>
            {projects.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
          </select>
        </div>

        {selectedProject && (
          <>
            {/* New Post */}
            <div className="card animate-in delay-2" style={{ marginBottom: 'var(--space-xl)' }}>
              <h4 style={{ marginBottom: 'var(--space-md)' }}>Start a Discussion</h4>
              <div className="form-group">
                <input type="text" className="form-input" placeholder="Question title" value={newPost.title}
                  onChange={e => setNewPost(p => ({ ...p, title: e.target.value }))} />
              </div>
              <div className="form-group" style={{ marginBottom: 'var(--space-md)' }}>
                <textarea className="form-input" placeholder="Describe your question or share your insight..."
                  value={newPost.content} onChange={e => setNewPost(p => ({ ...p, content: e.target.value }))}
                  rows={3} />
              </div>
              <button className="btn btn-primary btn-sm" onClick={submitPost} disabled={posting || !newPost.content}>
                <FiSend size={14} /> {posting ? 'Posting...' : 'Post'}
              </button>
            </div>

            {/* Discussions */}
            {loading ? <div className="loading-spinner" /> : topLevel.length === 0 ? (
              <div className="empty-state">
                <FiMessageCircle size={36} style={{ marginBottom: 'var(--space-md)', opacity: 0.5 }} />
                <h3>No discussions yet</h3>
                <p>Be the first to start a discussion for this project!</p>
              </div>
            ) : (
              <div className="animate-in delay-3" style={{ display: 'grid', gap: 'var(--space-md)' }}>
                {topLevel.map(d => (
                  <div key={d.id} className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-sm)' }}>
                      <div>
                        {d.title && <h4 style={{ marginBottom: 4 }}>{d.title}</h4>}
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {d.userName} • {new Date(d.createdAt).toLocaleDateString()}
                        </span>
                      </div>
                      <button onClick={() => handleUpvote(d.id)}
                        style={{
                          background: 'none', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                          padding: '4px 10px', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex',
                          alignItems: 'center', gap: 4, fontSize: '0.85rem', fontFamily: 'var(--font-main)',
                        }}>
                        <FiThumbsUp size={14} /> {d.upvotes || 0}
                      </button>
                    </div>
                    <p style={{ fontSize: '0.925rem', lineHeight: 1.7, marginBottom: 'var(--space-md)' }}>{d.content}</p>

                    {/* Replies */}
                    {getReplies(d.id).map(reply => (
                      <div key={reply.id} style={{
                        marginLeft: 'var(--space-lg)', padding: 'var(--space-md)',
                        borderLeft: '2px solid var(--border)', marginBottom: 'var(--space-sm)',
                      }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {reply.userName} • {new Date(reply.createdAt).toLocaleDateString()}
                        </span>
                        <p style={{ fontSize: '0.9rem', marginTop: 4 }}>{reply.content}</p>
                      </div>
                    ))}

                    {/* Reply Form */}
                    {replyTo === d.id ? (
                      <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-sm)' }}>
                        <input type="text" className="form-input" placeholder="Write a reply..." style={{ flex: 1, fontSize: '0.85rem' }}
                          value={replyContent} onChange={e => setReplyContent(e.target.value)}
                          onKeyDown={e => e.key === 'Enter' && submitReply(d.id)} />
                        <button className="btn btn-primary btn-sm" onClick={() => submitReply(d.id)}>Reply</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => { setReplyTo(null); setReplyContent(''); }}>Cancel</button>
                      </div>
                    ) : (
                      <button onClick={() => setReplyTo(d.id)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary-light)', fontSize: '0.85rem', fontFamily: 'var(--font-main)', marginTop: 4 }}>
                        Reply
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {!selectedProject && (
          <div className="empty-state animate-in delay-2">
            <FiMessageCircle size={48} style={{ marginBottom: 'var(--space-md)', opacity: 0.3 }} />
            <h3>Select a Project</h3>
            <p>Choose a project above to see and join its discussions</p>
          </div>
        )}
      </div>
    </div>
  );
}
