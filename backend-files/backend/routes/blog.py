from flask import Blueprint, request, jsonify
from src.models.blog import BlogPost, db
import openai
import os

blog_bp = Blueprint("blog_bp", __name__)

@blog_bp.route("/blog/posts", methods=["GET"])
def get_blog_posts():
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])

@blog_bp.route("/blog/posts/<int:post_id>", methods=["GET"])
def get_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return jsonify(post.to_dict())

@blog_bp.route("/blog/posts", methods=["POST"])
def create_blog_post():
    data = request.json
    
    post = BlogPost(
        title=data.get('title'),
        content=data.get('content'),
        excerpt=data.get('excerpt'),
        author=data.get('author', 'Admin'),
        published=data.get('published', False),
        featured_image=data.get('featured_image'),
        tags=','.join(data.get('tags', []))
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify(post.to_dict()), 201

@blog_bp.route("/blog/generate", methods=["POST"])
def generate_blog_content():
    data = request.json
    topic = data.get('topic')
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    try:
        # Use OpenAI to generate blog content
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a compassionate expert writer specializing in premature baby health and support. Your writing should be deeply empathetic, understanding that parents reading this are likely experiencing fear, uncertainty, and overwhelming emotions. Write with warmth, hope, and genuine care. Provide practical advice while acknowledging the emotional journey. Always include reassurance and remind parents that they are not alone in this experience."},
                {"role": "user", "content": f"Write a detailed, compassionate blog post about: {topic}. Address both the practical and emotional aspects. Include expert insights, but deliver them with warmth and understanding. Make it around 1000-1500 words, and ensure it provides both information and emotional support for NICU families."}
            ],
            max_tokens=2000
        )
        
        generated_content = response.choices[0].message.content
        
        return jsonify({
            'title': topic,
            'content': generated_content,
            'excerpt': generated_content[:200] + '...'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_bp.route("/blog/posts/<int:post_id>", methods=["PUT"])
def update_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    data = request.json
    
    post.title = data.get('title', post.title)
    post.content = data.get('content', post.content)
    post.excerpt = data.get('excerpt', post.excerpt)
    post.published = data.get('published', post.published)
    post.featured_image = data.get('featured_image', post.featured_image)
    post.tags = ','.join(data.get('tags', [])) if data.get('tags') else post.tags
    
    db.session.commit()
    
    return jsonify(post.to_dict())

@blog_bp.route("/blog/posts/<int:post_id>", methods=["DELETE"])
def delete_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': 'Post deleted successfully'})

