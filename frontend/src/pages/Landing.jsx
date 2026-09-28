import { Link } from 'react-router-dom';
import { FiZap, FiCode, FiTarget, FiCpu, FiTrendingUp, FiShield, FiLayers, FiDatabase, FiBarChart2, FiArrowRight, FiCheck } from 'react-icons/fi';
import './Landing.css';

const domains = [
  { icon: <FiCode />, name: 'Web Development', desc: 'Build interactive websites and web apps', color: '#7B2CBF' },
  { icon: <FiZap />, name: 'Python Development', desc: 'Create powerful apps and APIs with Python', color: '#3C096C' },
  { icon: <FiDatabase />, name: 'Java Development', desc: 'Build robust OOP applications', color: '#5A189A' },
  { icon: <FiCpu />, name: 'AI/ML', desc: 'Explore AI with hands-on ML projects', color: '#9D4EDD' },
  { icon: <FiBarChart2 />, name: 'Data Science', desc: 'Analyze datasets and build models', color: '#C77DFF' },
  { icon: <FiTrendingUp />, name: 'Data Analytics', desc: 'Create dashboards and BI reports', color: '#E0AAFF' },
  { icon: <FiShield />, name: 'Cybersecurity', desc: 'Learn defensive security practices', color: '#240046' },
  { icon: <FiLayers />, name: 'Full Stack', desc: 'Build complete applications end-to-end', color: '#7B2CBF' },
];

const steps = [
  { num: '01', title: 'Choose', desc: 'Pick a project that fits your level and interests' },
  { num: '02', title: 'Learn', desc: 'Understand concepts as you need them' },
  { num: '03', title: 'Build', desc: 'Implement in VS Code step by step' },
  { num: '04', title: 'Debug', desc: 'AI Copilot helps when you get stuck' },
  { num: '05', title: 'Complete', desc: 'Track progress through milestones' },
  { num: '06', title: 'Showcase', desc: 'Share your finished project' },
];

const features = [
  'Zero-level friendly — start with no prior knowledge',
  '80 structured projects across 8 domains',
  'AI Development Copilot for contextual help',
  'Milestone-based progress tracking',
  'XP, achievements and leaderboards',
  'Community discussions and project showcase',
];

export default function Landing() {
  return (
    <div className="landing">
      {/* Hero */}
      <section className="hero">
        <div className="container">
          <div className="hero-content animate-in">
            <div className="hero-badge">🚀 Project-Based Learning Platform</div>
            <h1>Build Projects.<br />Learn While Building.<br /><span className="hero-gradient">Become a Developer.</span></h1>
            <p className="hero-desc">
              Don't just watch tutorials. Choose a project, learn concepts as you build,
              get AI assistance when stuck, and track your progress from zero to completion.
            </p>
            <div className="hero-actions">
              <Link to="/register" className="btn btn-primary btn-lg">
                Start Building <FiArrowRight />
              </Link>
              <a href="#how-it-works" className="btn btn-ghost btn-lg">How It Works</a>
            </div>
            <div className="hero-stats">
              <div className="hero-stat"><strong>80</strong><span>Projects</span></div>
              <div className="hero-stat"><strong>8</strong><span>Domains</span></div>
              <div className="hero-stat"><strong>10</strong><span>Levels</span></div>
              <div className="hero-stat"><strong>∞</strong><span>Learning</span></div>
            </div>
          </div>
        </div>
        <div className="hero-glow" />
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="section">
        <div className="container">
          <div className="section-header" style={{ textAlign: 'center' }}>
            <h2>How It Works</h2>
            <p>From choosing a project to showcasing your work — guided every step</p>
          </div>
          <div className="steps-grid">
            {steps.map((step, i) => (
              <div key={i} className={`step-card animate-in delay-${i % 4 + 1}`}>
                <div className="step-num">{step.num}</div>
                <h4>{step.title}</h4>
                <p>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Domains */}
      <section className="section">
        <div className="container">
          <div className="section-header" style={{ textAlign: 'center' }}>
            <h2>8 Technology Domains</h2>
            <p>Explore projects across the most in-demand technology areas</p>
          </div>
          <div className="domains-grid">
            {domains.map((d, i) => (
              <div key={i} className="domain-card card" style={{ borderColor: d.color + '40' }}>
                <div className="domain-icon" style={{ color: d.color }}>{d.icon}</div>
                <h4>{d.name}</h4>
                <p>{d.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="section">
        <div className="container">
          <div className="value-section">
            <div className="value-content">
              <h2>Why Project Hub?</h2>
              <p style={{ marginBottom: 'var(--space-xl)' }}>
                Most learning platforms give you tutorials. We give you a guided project building experience
                with an AI mentor that understands your exact context.
              </p>
              <ul className="value-list">
                {features.map((f, i) => (
                  <li key={i}><FiCheck className="check-icon" /> {f}</li>
                ))}
              </ul>
              <Link to="/register" className="btn btn-primary" style={{ marginTop: 'var(--space-xl)' }}>
                Start Your First Project <FiArrowRight />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section cta-section">
        <div className="container" style={{ textAlign: 'center' }}>
          <h2>Ready to Build Something Real?</h2>
          <p style={{ maxWidth: 500, margin: '0 auto var(--space-xl)' }}>
            Join Project Hub and start building projects that matter. No prior experience needed.
          </p>
          <Link to="/register" className="btn btn-primary btn-lg">
            Start Building — It's Free <FiArrowRight />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-inner">
            <div className="footer-brand">
              <FiZap size={20} /> <span>Project Hub V2</span>
            </div>
            <p>Build Projects. Learn While Building. Become a Developer.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
