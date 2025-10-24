from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to threads
    threads = db.relationship('ForumThread', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'thread_count': len(self.threads)
        }

class ForumThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pinned = db.Column(db.Boolean, default=False)
    locked = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=True)  # For moderation
    
    # Relationships
    posts = db.relationship('ForumPost', backref='thread', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'author_name': self.author.username if self.author else 'Unknown',
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Unknown',
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'pinned': self.pinned,
            'locked': self.locked,
            'approved': self.approved,
            'post_count': len(self.posts),
            'last_post_at': max([post.created_at for post in self.posts], default=self.created_at).isoformat() if self.posts else self.created_at.isoformat()
        }

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('forum_thread.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved = db.Column(db.Boolean, default=True)  # For moderation
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author_id': self.author_id,
            'author_name': self.author.username if self.author else 'Unknown',
            'thread_id': self.thread_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'approved': self.approved
        }

