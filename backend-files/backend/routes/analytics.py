from flask import Blueprint, request, jsonify
from src.models.user import db
from datetime import datetime, timedelta
import uuid

analytics_bp = Blueprint("analytics_bp", __name__)

# Simple analytics model (you could expand this with a proper analytics database)
class PageView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_url = db.Column(db.String(500), nullable=False)
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    referrer = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))

class ShareEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(50), nullable=False)  # 'blog', 'forum', 'page'
    content_id = db.Column(db.Integer)
    platform = db.Column(db.String(50), nullable=False)  # 'facebook', 'instagram', 'tiktok'
    share_url = db.Column(db.String(500))
    referral_code = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    clicks = db.Column(db.Integer, default=0)

class ReferralTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referral_code = db.Column(db.String(100), unique=True, nullable=False)
    original_url = db.Column(db.String(500), nullable=False)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)  # Could track sign-ups, forum posts, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Track page views
@analytics_bp.route("/analytics/pageview", methods=["POST"])
def track_pageview():
    data = request.json
    
    pageview = PageView(
        page_url=data.get('page_url'),
        user_agent=request.headers.get('User-Agent'),
        ip_address=request.remote_addr,
        referrer=data.get('referrer'),
        session_id=data.get('session_id')
    )
    
    db.session.add(pageview)
    db.session.commit()
    
    return jsonify({'status': 'success'})

# Create viral sharing link
@analytics_bp.route("/analytics/create-share-link", methods=["POST"])
def create_share_link():
    data = request.json
    
    # Generate unique referral code
    referral_code = str(uuid.uuid4())[:8]
    
    # Create share event
    share_event = ShareEvent(
        content_type=data.get('content_type'),
        content_id=data.get('content_id'),
        platform=data.get('platform'),
        share_url=data.get('url'),
        referral_code=referral_code
    )
    
    # Create referral tracking
    referral = ReferralTracking(
        referral_code=referral_code,
        original_url=data.get('url')
    )
    
    db.session.add(share_event)
    db.session.add(referral)
    db.session.commit()
    
    # Create viral sharing URL
    share_url = f"https://prematurebabys.com/share/{referral_code}"
    
    return jsonify({
        'share_url': share_url,
        'referral_code': referral_code,
        'platform_specific_url': generate_platform_share_url(data.get('platform'), share_url, data.get('title', ''))
    })

def generate_platform_share_url(platform, url, title):
    """Generate platform-specific sharing URLs"""
    encoded_url = url.replace(':', '%3A').replace('/', '%2F')
    encoded_title = title.replace(' ', '%20')
    
    if platform == 'facebook':
        return f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
    elif platform == 'instagram':
        # Instagram doesn't support direct URL sharing, return instructions
        return "instagram://share"
    elif platform == 'tiktok':
        # TikTok doesn't support direct URL sharing, return instructions
        return "tiktok://share"
    else:
        return url

# Track referral clicks
@analytics_bp.route("/share/<referral_code>", methods=["GET"])
def track_referral_click(referral_code):
    referral = ReferralTracking.query.filter_by(referral_code=referral_code).first()
    
    if referral:
        referral.clicks += 1
        
        # Also update the share event
        share_event = ShareEvent.query.filter_by(referral_code=referral_code).first()
        if share_event:
            share_event.clicks += 1
        
        db.session.commit()
        
        # Redirect to original URL
        return jsonify({
            'redirect_url': referral.original_url,
            'message': 'Welcome to our supportive community!'
        })
    else:
        return jsonify({'error': 'Invalid referral code'}), 404

# Analytics dashboard data
@analytics_bp.route("/analytics/dashboard", methods=["GET"])
def get_dashboard_data():
    # Get date range (default to last 30 days)
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Page views
    total_pageviews = PageView.query.filter(PageView.timestamp >= start_date).count()
    
    # Top pages
    top_pages = db.session.query(
        PageView.page_url, 
        db.func.count(PageView.id).label('views')
    ).filter(
        PageView.timestamp >= start_date
    ).group_by(PageView.page_url).order_by(db.desc('views')).limit(10).all()
    
    # Share events
    total_shares = ShareEvent.query.filter(ShareEvent.timestamp >= start_date).count()
    
    # Platform breakdown
    platform_shares = db.session.query(
        ShareEvent.platform,
        db.func.count(ShareEvent.id).label('shares'),
        db.func.sum(ShareEvent.clicks).label('clicks')
    ).filter(
        ShareEvent.timestamp >= start_date
    ).group_by(ShareEvent.platform).all()
    
    # Referral performance
    top_referrals = ReferralTracking.query.filter(
        ReferralTracking.created_at >= start_date
    ).order_by(ReferralTracking.clicks.desc()).limit(10).all()
    
    return jsonify({
        'total_pageviews': total_pageviews,
        'total_shares': total_shares,
        'top_pages': [{'url': page[0], 'views': page[1]} for page in top_pages],
        'platform_breakdown': [
            {
                'platform': platform[0], 
                'shares': platform[1], 
                'clicks': platform[2] or 0
            } for platform in platform_shares
        ],
        'top_referrals': [
            {
                'code': ref.referral_code,
                'url': ref.original_url,
                'clicks': ref.clicks,
                'conversions': ref.conversions
            } for ref in top_referrals
        ]
    })

# Auto-posting to social media (placeholder - requires actual API integration)
@analytics_bp.route("/analytics/auto-post", methods=["POST"])
def auto_post_to_social():
    data = request.json
    
    # This would integrate with actual social media APIs
    # For now, we'll just log the intent and return success
    
    content = data.get('content')
    platforms = data.get('platforms', [])
    
    results = {}
    
    for platform in platforms:
        # Create share link for tracking
        share_response = create_share_link_internal(
            content_type=data.get('content_type', 'blog'),
            content_id=data.get('content_id'),
            platform=platform,
            url=data.get('url'),
            title=data.get('title', '')
        )
        
        # In a real implementation, you would:
        # 1. Use platform APIs (Facebook Graph API, Instagram Basic Display API, etc.)
        # 2. Handle authentication and permissions
        # 3. Format content appropriately for each platform
        # 4. Handle rate limits and errors
        
        results[platform] = {
            'status': 'scheduled',  # Would be 'posted' in real implementation
            'share_url': share_response['share_url'],
            'message': f'Content scheduled for {platform}'
        }
    
    return jsonify(results)

def create_share_link_internal(content_type, content_id, platform, url, title):
    """Internal function to create share links"""
    referral_code = str(uuid.uuid4())[:8]
    
    share_event = ShareEvent(
        content_type=content_type,
        content_id=content_id,
        platform=platform,
        share_url=url,
        referral_code=referral_code
    )
    
    referral = ReferralTracking(
        referral_code=referral_code,
        original_url=url
    )
    
    db.session.add(share_event)
    db.session.add(referral)
    db.session.commit()
    
    return {
        'share_url': f"https://prematurebabys.com/share/{referral_code}",
        'referral_code': referral_code
    }

