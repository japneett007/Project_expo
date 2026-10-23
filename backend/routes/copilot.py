"""AI Development Copilot routes — proxies requests to Groq API — SQLite."""
import json
import os

import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_db
from middleware.rate_limit import rate_limit
from models import Milestone, Project, User
from utils.helpers import now_iso, sanitize_string

copilot_bp = Blueprint('copilot', __name__)

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_API_URL = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')


def _parse(value, default=None):
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


def build_system_prompt(project_data: dict, milestone_data: dict, user_question: str) -> str:
    """Build a project-aware system prompt for the AI Copilot."""
    return f"""You are an AI Development Copilot for Project Hub — a project-based learning platform.

CURRENT CONTEXT:
- Project: {project_data.get('title', 'Unknown')}
- Domain: {project_data.get('domain', 'Unknown')}
- Technologies: {', '.join(project_data.get('technologies', []))}
- Current Milestone: {milestone_data.get('title', 'Unknown') if milestone_data else 'Not specified'}
- Difficulty: {project_data.get('difficulty', 'Unknown')}

YOUR ROLE:
You are a patient, knowledgeable mentor helping a student build this project. You:
1. EXPLAIN concepts in the context of this specific project
2. HELP debug errors with clear explanations
3. SUGGEST improvements and explain WHY they work
4. REVIEW code for correctness, readability, and security
5. Provide ARCHITECTURE guidance for this project

THREE-STAGE ASSISTANCE:
- First: Explain the problem and relevant concept
- Then: Provide a direction/hint for the student to solve it
- Finally: Provide concrete implementation if the student still needs help

The student can request direct solutions. The staged model supports learning but doesn't force it.

IMPORTANT RULES:
- Always relate explanations to the current project context
- Explain WHY each solution works, not just WHAT to do
- Point out common mistakes related to this technology stack
- Be encouraging but honest about errors
- Never provide solutions without explaining the underlying concept

Student's question: {user_question}"""


@copilot_bp.route('/chat', methods=['POST'])
@rate_limit('copilot')
@jwt_required()
def chat():
    """Send a message to the AI Copilot with project context."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    message = sanitize_string(data.get('message', ''))
    project_id = data.get('projectId', '')
    milestone_id = data.get('milestoneId', '')
    stage = data.get('stage', 'explanation')

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    # ── Fetch context from DB ──────────────────────────────────────────────────
    with get_db() as db:
        project_obj = db.get(Project, project_id) if project_id else None
        project_data = {
            'title': project_obj.title if project_obj else '',
            'domain': project_obj.domain_id if project_obj else '',
            'technologies': _parse(project_obj.technologies) if project_obj else [],
            'difficulty': project_obj.difficulty if project_obj else '',
        }

        milestone_data = {}
        if milestone_id:
            ms = db.get(Milestone, milestone_id)
            if ms:
                milestone_data = {'title': ms.title}

        # Mark copilot as used (for achievements) — only if not already set
        user = db.get(User, user_id)
        if user and not user.copilot_used:
            user.copilot_used = 1
            user.updated_at = now_iso()

    # ── Build prompt and call Groq ─────────────────────────────────────────────
    system_prompt = build_system_prompt(project_data, milestone_data, message)

    if stage == 'hint':
        system_prompt += "\n\nThe student is asking for a HINT. Give them a direction to think about, not the full solution."
    elif stage == 'solution':
        system_prompt += "\n\nThe student is asking for the SOLUTION. Provide the concrete implementation with full explanation."

    ai_response = ''
    if GROQ_API_KEY:
        try:
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json',
            }
            payload = {
                'model': 'gpt-oss-1-2.0',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': message},
                ],
                'max_tokens': 2000,
                'temperature': 0.7,
            }
            history = data.get('history', [])
            if history:
                msgs = [{'role': 'system', 'content': system_prompt}]
                for h in history[-10:]:
                    msgs.append({'role': h.get('role', 'user'), 'content': h.get('content', '')})
                msgs.append({'role': 'user', 'content': message})
                payload['messages'] = msgs

            response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                ai_response = f"I'm having trouble connecting right now. Please try again. (Status: {response.status_code})"
        except requests.exceptions.Timeout:
            ai_response = "The request timed out. Please try again."
        except Exception:
            ai_response = "I'm temporarily unavailable. Please try again shortly."
    else:
        ai_response = _generate_fallback_response(message, project_data, milestone_data, stage)

    return jsonify({
        'response': ai_response,
        'projectId': project_id,
        'milestoneId': milestone_id,
        'stage': stage,
    }), 200


@copilot_bp.route('/history/<project_id>', methods=['GET'])
@jwt_required()
def get_history(project_id):
    """Chat history placeholder (managed client-side in V1)."""
    return jsonify({'history': [], 'projectId': project_id}), 200


def _generate_fallback_response(message: str, project: dict, milestone: dict, stage: str) -> str:
    """Generate a helpful fallback response when the AI API is not configured."""
    project_title = project.get('title', 'your project')
    technologies = ', '.join(project.get('technologies', ['the required technologies']))

    if stage == 'explanation':
        return f"""Great question about **{project_title}**!

Here's what you should understand:

This project uses **{technologies}**. The concept you're asking about is fundamental to how these technologies work together.

**Key concepts to review:**
1. Look at the official documentation for {technologies}
2. Break down the problem into smaller parts
3. Think about what each part of your code needs to do

Would you like me to give you a **hint** on how to approach this, or would you prefer the **full solution**?"""

    elif stage == 'hint':
        return f"""Here's a hint for your **{project_title}** question:

Think about the data flow:
1. Where does the input come from?
2. What transformation needs to happen?
3. Where should the output go?

Try implementing this step by step. If you're still stuck, ask me for the **solution** and I'll walk you through it with a full explanation."""

    else:
        return f"""For your **{project_title}** question, here's how to approach the solution:

Since this project uses **{technologies}**, you'll want to:

1. **Set up** the basic structure first
2. **Implement** the core logic step by step
3. **Test** each piece before moving on
4. **Debug** by checking inputs and outputs at each step

*Note: For more detailed AI assistance, configure the Groq API key in your backend .env file.*"""
