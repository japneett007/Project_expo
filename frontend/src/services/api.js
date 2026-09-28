const API_BASE = 'http://localhost:5000/api';

async function request(endpoint, options = {}) {
  const config = {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };

  if (options.body && typeof options.body === 'object') {
    config.body = JSON.stringify(options.body);
  }

  const res = await fetch(`${API_BASE}${endpoint}`, config);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || 'Something went wrong');
  }
  return data;
}

// Auth
export const authAPI = {
  register: (body) => request('/auth/register', { method: 'POST', body }),
  login: (body) => request('/auth/login', { method: 'POST', body }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  updateProfile: (body) => request('/auth/profile', { method: 'PUT', body }),
};

// Projects
export const projectsAPI = {
  list: (params = '') => request(`/projects${params ? '?' + params : ''}`),
  get: (id) => request(`/projects/${id}`),
  start: (id) => request(`/projects/${id}/start`, { method: 'POST' }),
  recommended: () => request('/projects/recommended'),
  domains: () => request('/projects/domains'),
  branches: () => request('/projects/branches'),
};

// Milestones
export const milestonesAPI = {
  getForProject: (projectId) => request(`/milestones/project/${projectId}`),
  complete: (milestoneId) => request(`/milestones/${milestoneId}/complete`, { method: 'PUT' }),
  get: (milestoneId) => request(`/milestones/${milestoneId}`),
};

// Copilot
export const copilotAPI = {
  chat: (body) => request('/copilot/chat', { method: 'POST', body }),
  history: (projectId) => request(`/copilot/history/${projectId}`),
};

// Community
export const communityAPI = {
  getDiscussions: (projectId) => request(`/community/${projectId}`),
  post: (projectId, body) => request(`/community/${projectId}`, { method: 'POST', body }),
  upvote: (discussionId) => request(`/community/upvote/${discussionId}`, { method: 'POST' }),
};

// Showcase
export const showcaseAPI = {
  list: () => request('/showcase'),
  submit: (body) => request('/showcase', { method: 'POST', body }),
  userShowcases: (userId) => request(`/showcase/user/${userId}`),
};

// Achievements
export const achievementsAPI = {
  list: () => request('/achievements'),
  xpSummary: () => request('/achievements/xp'),
};

// Leaderboard
export const leaderboardAPI = {
  get: (params = '') => request(`/leaderboard${params ? '?' + params : ''}`),
};
