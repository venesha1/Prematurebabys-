from flask import Blueprint, request, jsonify
from src.models.forum import ForumCategory, ForumThread, ForumPost, db
from src.models.user import User
import openai

forum_bp = Blueprint("forum_bp", __name__)

# Content moderation using AI
def moderate_content(content):
    """Use AI to check if content is appropriate and supportive"""
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a compassionate content moderator for a support forum for families with premature babies. Your role is to ensure all content is supportive, appropriate, and maintains a safe space for vulnerable families. Check if the content is: 1) Supportive and kind, 2) Appropriate for families in crisis, 3) Free from harmful advice, 4) Respectful of different experiences. Respond with 'APPROVED' if the content is appropriate, or 'NEEDS_REVIEW: [reason]' if it needs human review."},
                {"role": "user", "content": f"Please review this forum post content: {content}"}
            ],
            max_tokens=100
        )
        
        result = response.choices[0].message.content.strip()
        return result.startswith('APPROVED'), result
        
    except Exception as e:
        # If AI moderation fails, default to human review
        return False, f"NEEDS_REVIEW: AI moderation unavailable - {str(e)}"

# Forum Categories
@forum_bp.route("/forum/categories", methods=["GET"])
def get_categories():
    categories = ForumCategory.query.all()
    return jsonify([cat.to_dict() for cat in categories])

@forum_bp.route("/forum/categories", methods=["POST"])
def create_category():
    data = request.json
    category = ForumCategory(
        name=data.get('name'),
        description=data.get('description')
    )
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201

# Forum Threads
@forum_bp.route("/forum/threads", methods=["GET"])
def get_threads():
    category_id = request.args.get('category_id')
    query = ForumThread.query.filter_by(approved=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    threads = query.order_by(ForumThread.pinned.desc(), ForumThread.updated_at.desc()).all()
    return jsonify([thread.to_dict() for thread in threads])

@forum_bp.route("/forum/threads/<int:thread_id>", methods=["GET"])
def get_thread(thread_id):
    thread = ForumThread.query.get_or_404(thread_id)
    posts = ForumPost.query.filter_by(thread_id=thread_id, approved=True).order_by(ForumPost.created_at.asc()).all()
    
    return jsonify({
        'thread': thread.to_dict(),
        'posts': [post.to_dict() for post in posts]
    })

@forum_bp.route("/forum/threads", methods=["POST"])
def create_thread():
    data = request.json
    
    # Moderate content with compassion
    approved, moderation_result = moderate_content(data.get('content', ''))
    
    thread = ForumThread(
        title=data.get('title'),
        content=data.get('content'),
        author_id=data.get('author_id', 1),  # Default to admin for now
        category_id=data.get('category_id'),
        approved=approved
    )
    
    db.session.add(thread)
    db.session.commit()
    
    response_data = thread.to_dict()
    if not approved:
        response_data['moderation_note'] = 'Your post is being reviewed to ensure it provides the best support for our community.'
    
    return jsonify(response_data), 201

# Forum Posts
@forum_bp.route("/forum/posts", methods=["POST"])
def create_post():
    data = request.json
    
    # Moderate content with compassion
    approved, moderation_result = moderate_content(data.get('content', ''))
    
    post = ForumPost(
        content=data.get('content'),
        author_id=data.get('author_id', 1),  # Default to admin for now
        thread_id=data.get('thread_id'),
        approved=approved
    )
    
    db.session.add(post)
    
    # Update thread's updated_at timestamp
    thread = ForumThread.query.get(data.get('thread_id'))
    if thread:
        thread.updated_at = db.func.now()
    
    db.session.commit()
    
    response_data = post.to_dict()
    if not approved:
        response_data['moderation_note'] = 'Your message is being reviewed to ensure it provides the best support for our community.'
    
    return jsonify(response_data), 201

# Moderation endpoints
@forum_bp.route("/forum/moderation/threads", methods=["GET"])
def get_threads_for_moderation():
    threads = ForumThread.query.filter_by(approved=False).all()
    return jsonify([thread.to_dict() for thread in threads])

@forum_bp.route("/forum/moderation/posts", methods=["GET"])
def get_posts_for_moderation():
    posts = ForumPost.query.filter_by(approved=False).all()
    return jsonify([post.to_dict() for post in posts])

@forum_bp.route("/forum/moderation/approve/<string:content_type>/<int:content_id>", methods=["POST"])
def approve_content(content_type, content_id):
    if content_type == 'thread':
        content = ForumThread.query.get_or_404(content_id)
    elif content_type == 'post':
        content = ForumPost.query.get_or_404(content_id)
    else:
        return jsonify({'error': 'Invalid content type'}), 400
    
    content.approved = True
    db.session.commit()
    
    return jsonify({'message': 'Content approved successfully'})

# Initialize default categories
@forum_bp.route("/forum/init", methods=["POST"])
def initialize_forum():
    """Initialize forum with default categories"""
    default_categories = [
        {
            'name': 'NICU Support',
            'description': 'Share your NICU journey, ask questions, and find support from other families'
        },
        {
            'name': 'Coming Home',
            'description': 'Discuss the transition from NICU to home, equipment, and ongoing care'
        },
        {
            'name': 'Feeding & Growth',
            'description': 'Share experiences about feeding challenges, growth milestones, and nutrition'
        },
        {
            'name': 'Mental Health & Wellness',
            'description': 'A safe space to discuss the emotional aspects of the NICU journey'
        },
        {
            'name': 'Celebrations & Milestones',
            'description': 'Celebrate the victories, big and small, in your premature baby\'s journey'
        },
        {
            'name': 'Resources & Recommendations',
            'description': 'Share helpful resources, products, and recommendations for NICU families'
        }
    ]
    
    for cat_data in default_categories:
        existing = ForumCategory.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = ForumCategory(**cat_data)
            db.session.add(category)
    
    db.session.commit()
    return jsonify({'message': 'Forum initialized successfully'})

