from flask import Blueprint, request, jsonify
import os
import requests
from datetime import datetime
import json

social_media_bp = Blueprint("social_media_bp", __name__)

# Configuration for different social media platforms
SOCIAL_MEDIA_CONFIG = {
    'facebook': {
        'api_base': 'https://graph.facebook.com/v18.0',
        'required_env_vars': ['FACEBOOK_ACCESS_TOKEN', 'FACEBOOK_PAGE_ID']
    },
    'instagram': {
        'api_base': 'https://graph.instagram.com/v18.0',
        'required_env_vars': ['INSTAGRAM_ACCESS_TOKEN', 'INSTAGRAM_USER_ID']
    },
    'tiktok': {
        'api_base': 'https://open-api.tiktok.com',
        'required_env_vars': ['TIKTOK_CLIENT_KEY', 'TIKTOK_CLIENT_SECRET', 'TIKTOK_ACCESS_TOKEN']
    }
}

def check_platform_credentials(platform):
    """Check if required environment variables are set for a platform"""
    if platform not in SOCIAL_MEDIA_CONFIG:
        return False, f"Unknown platform: {platform}"
    
    config = SOCIAL_MEDIA_CONFIG[platform]
    missing_vars = []
    
    for var in config['required_env_vars']:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        return False, f"Missing environment variables: {', '.join(missing_vars)}"
    
    return True, "All credentials available"

@social_media_bp.route("/social-media/status", methods=["GET"])
def get_platform_status():
    """Get the status of all social media platform integrations"""
    status = {}
    
    for platform in SOCIAL_MEDIA_CONFIG.keys():
        is_configured, message = check_platform_credentials(platform)
        status[platform] = {
            'configured': is_configured,
            'message': message,
            'last_checked': datetime.utcnow().isoformat()
        }
    
    return jsonify(status)

@social_media_bp.route("/social-media/post", methods=["POST"])
def post_to_social_media():
    """Post content to selected social media platforms"""
    data = request.json
    
    content = data.get('content', '')
    platforms = data.get('platforms', [])
    media_url = data.get('media_url')  # Optional image/video URL
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    if not platforms:
        return jsonify({'error': 'At least one platform must be specified'}), 400
    
    results = {}
    
    for platform in platforms:
        try:
            if platform == 'facebook':
                result = post_to_facebook(content, media_url)
            elif platform == 'instagram':
                result = post_to_instagram(content, media_url)
            elif platform == 'tiktok':
                result = post_to_tiktok(content, media_url)
            else:
                result = {'success': False, 'error': f'Unknown platform: {platform}'}
            
            results[platform] = result
            
        except Exception as e:
            results[platform] = {
                'success': False,
                'error': str(e)
            }
    
    return jsonify(results)

def post_to_facebook(content, media_url=None):
    """Post content to Facebook page"""
    is_configured, message = check_platform_credentials('facebook')
    if not is_configured:
        return {'success': False, 'error': message}
    
    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    
    url = f"{SOCIAL_MEDIA_CONFIG['facebook']['api_base']}/{page_id}/feed"
    
    payload = {
        'message': content,
        'access_token': access_token
    }
    
    if media_url:
        payload['link'] = media_url
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        result = response.json()
        return {
            'success': True,
            'post_id': result.get('id'),
            'platform': 'facebook'
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Facebook API error: {str(e)}'
        }

def post_to_instagram(content, media_url=None):
    """Post content to Instagram"""
    is_configured, message = check_platform_credentials('instagram')
    if not is_configured:
        return {'success': False, 'error': message}
    
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_USER_ID')
    
    # Instagram requires media for posts
    if not media_url:
        return {
            'success': False,
            'error': 'Instagram posts require media (image or video)'
        }
    
    try:
        # Step 1: Create media container
        container_url = f"{SOCIAL_MEDIA_CONFIG['instagram']['api_base']}/{user_id}/media"
        container_payload = {
            'image_url': media_url,
            'caption': content,
            'access_token': access_token
        }
        
        container_response = requests.post(container_url, data=container_payload)
        container_response.raise_for_status()
        container_id = container_response.json()['id']
        
        # Step 2: Publish the media
        publish_url = f"{SOCIAL_MEDIA_CONFIG['instagram']['api_base']}/{user_id}/media_publish"
        publish_payload = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, data=publish_payload)
        publish_response.raise_for_status()
        
        result = publish_response.json()
        return {
            'success': True,
            'post_id': result.get('id'),
            'platform': 'instagram'
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Instagram API error: {str(e)}'
        }

def post_to_tiktok(content, media_url=None):
    """Post content to TikTok (placeholder - requires video upload)"""
    is_configured, message = check_platform_credentials('tiktok')
    if not is_configured:
        return {'success': False, 'error': message}
    
    # TikTok Content Posting API is more complex and requires video upload
    # This is a placeholder implementation
    return {
        'success': False,
        'error': 'TikTok posting requires video upload implementation - coming soon!'
    }

@social_media_bp.route("/social-media/schedule", methods=["POST"])
def schedule_social_media_post():
    """Schedule a post for future publishing"""
    data = request.json
    
    content = data.get('content', '')
    platforms = data.get('platforms', [])
    schedule_time = data.get('schedule_time')  # ISO format datetime
    media_url = data.get('media_url')
    
    if not content or not platforms or not schedule_time:
        return jsonify({'error': 'Content, platforms, and schedule_time are required'}), 400
    
    # In a real implementation, you would store this in a database
    # and have a background job processor to handle scheduled posts
    
    scheduled_post = {
        'id': f"scheduled_{datetime.utcnow().timestamp()}",
        'content': content,
        'platforms': platforms,
        'media_url': media_url,
        'schedule_time': schedule_time,
        'status': 'scheduled',
        'created_at': datetime.utcnow().isoformat()
    }
    
    return jsonify({
        'success': True,
        'scheduled_post': scheduled_post,
        'message': 'Post scheduled successfully'
    })

@social_media_bp.route("/social-media/test-connection/<platform>", methods=["GET"])
def test_platform_connection(platform):
    """Test connection to a specific social media platform"""
    is_configured, message = check_platform_credentials(platform)
    if not is_configured:
        return jsonify({'success': False, 'error': message}), 400
    
    try:
        if platform == 'facebook':
            access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
            url = f"{SOCIAL_MEDIA_CONFIG['facebook']['api_base']}/me"
            response = requests.get(url, params={'access_token': access_token})
            
        elif platform == 'instagram':
            access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
            user_id = os.getenv('INSTAGRAM_USER_ID')
            url = f"{SOCIAL_MEDIA_CONFIG['instagram']['api_base']}/{user_id}"
            response = requests.get(url, params={'access_token': access_token})
            
        elif platform == 'tiktok':
            # TikTok connection test would be more complex
            return jsonify({
                'success': True,
                'message': 'TikTok credentials configured (connection test not implemented yet)'
            })
        
        response.raise_for_status()
        return jsonify({
            'success': True,
            'message': f'{platform.title()} connection successful',
            'data': response.json()
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'{platform.title()} connection failed: {str(e)}'
        }), 400

# Compassionate content generation for NICU families
@social_media_bp.route("/social-media/generate-content", methods=["POST"])
def generate_compassionate_content():
    """Generate compassionate social media content using AI"""
    data = request.json
    
    topic = data.get('topic', '')
    platform = data.get('platform', 'general')
    tone = data.get('tone', 'supportive')
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    # This would integrate with OpenAI API to generate content
    # For now, return a placeholder
    
    generated_content = {
        'content': f"Compassionate content about {topic} for {platform} - Generated with love and understanding for NICU families 💜",
        'hashtags': ['#NICUFamily', '#PrematureBaby', '#NICUSupport', '#PremieParents'],
        'platform': platform,
        'tone': tone,
        'generated_at': datetime.utcnow().isoformat()
    }
    
    return jsonify(generated_content)

