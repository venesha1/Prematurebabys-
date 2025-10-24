from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    author = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published = db.Column(db.Boolean, default=False)
    featured_image = db.Column(db.String(500))
    tags = db.Column(db.String(500))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'excerpt': self.excerpt,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'published': self.published,
            'featured_image': self.featured_image,
            'tags': self.tags.split(',') if self.tags else []
        }

