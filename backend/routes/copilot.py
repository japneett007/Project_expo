"""AI Development Copilot routes — proxies requests to Groq API."""
import os
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.helpers import read_json, write_json, generate_id, now_iso, sanitize_string
from middleware.rate_limit import rate_limit

copilot_bp = Blueprint('copilot', __name__)

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_API_URL = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')


def build_system_prompt(project, milestone, user_question):
    """Build a project-aware system prompt for the AI Copilot."""
    return f"""You are an AI Development Copilot for Project Hub — a project-based learning platform.

CURRENT CONTEXT:
- Project: {project.get('title', 'Unknown')}
- Domain: {project.get('domain', 'Unknown')}
- Technologies: {', '.join(project.get('technologies', []))}
- Current Milestone: {milestone.get('title', 'Unknown') if milestone else 'Not specified'}
- Difficulty: {project.get('difficulty', 'Unknown')}

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
    stage = data.get('stage', 'explanation')  # explanation, hint, solution

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    # Get project context
    projects = read_json('projects.json')
    project = next((p for p in projects if p['id'] == project_id), {})

    # Get milestone context
    milestone = {}
    if milestone_id:
        milestones = read_json('milestones.json')
        milestone = next((m for m in milestones if m.get('id') == milestone_id), {})

    # Build system prompt
    system_prompt = build_system_prompt(project, milestone, message)

    # Add stage instruction
    if stage == 'hint':
        system_prompt += "\n\nThe student is asking for a HINT. Give them a direction to think about, not the full solution."
    elif stage == 'solution':
        system_prompt += "\n\nThe student is asking for the SOLUTION. Provide the concrete implementation with full explanation."

    # Call Groq API
    ai_response = ""
    if GROQ_API_KEY:
        try:
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': 'gpt-oss-1-2.0',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': message}
                ],
                'max_tokens': 2000,
                'temperature': 0.7
            }

            # Include chat history if provided
            history = data.get('history', [])
            if history:
                messages_list = [{'role': 'system', 'content': system_prompt}]
                for h in history[-10:]:  # Last 10 messages for context
                    messages_list.append({'role': h.get('role', 'user'), 'content': h.get('content', '')})
                messages_list.append({'role': 'user', 'content': message})
                payload['messages'] = messages_list

            response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                ai_response = f"I'm having trouble connecting right now. Please try again in a moment. (Status: {response.status_code})"
        except requests.exceptions.Timeout:
            ai_response = "The request timed out. Please try again."
        except Exception as e:
            ai_response = "I'm temporarily unavailable. Please try again shortly."
    else:
        # Fallback when no API key is configured
        ai_response = _generate_fallback_response(message, project, milestone, stage)

    # Mark user as having used copilot (for achievements)
    users = read_json('users.json')
    user_idx = next((i for i, u in enumerate(users) if u['id'] == user_id), None)
    if user_idx is not None and not users[user_idx].get('copilotUsed', False):
        users[user_idx]['copilotUsed'] = True
        users[user_idx]['updatedAt'] = now_iso()
        write_json('users.json', users)

    return jsonify({
        'response': ai_response,
        'projectId': project_id,
        'milestoneId': milestone_id,
        'stage': stage
    }), 200


@copilot_bp.route('/history/<project_id>', methods=['GET'])
@jwt_required()
def get_history(project_id):
    """Get chat history for a project (stored client-side in V1)."""
    # In V1, chat history is managed client-side in localStorage
    # This endpoint is a placeholder for future server-side storage
    return jsonify({'history': [], 'projectId': project_id}), 200


def _generate_fallback_response(message, project, milestone, stage):
    """Generate a helpful fallback response when AI API is not configured."""
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

For the specific implementation, I recommend:
- Check the milestone instructions for exact requirements
- Use console.log/print statements to verify your logic
- Compare your output with the expected result

*Note: For more detailed AI assistance, configure the Groq API key in your backend .env file.*"""
