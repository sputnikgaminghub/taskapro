from flask import Flask, request, jsonify, render_template, session as flask_session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index, func, distinct
from datetime import datetime, timedelta
import hashlib
import secrets
import random
import os
import json
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Load environment variables
load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL', 'sqlite:///airdrop.db')
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Initialize extensions
db.init_app(app)
CORS(app)

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Environment variables
ADMIN_WALLET = os.getenv('ADMIN_WALLET', '0x742d35Cc6634C0532925a3b844Bc9e90')
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'admin123')
MAX_WALLETS_PER_IP = int(os.getenv('MAX_WALLETS_PER_IP', 5))
IP_BAN_HOURS = int(os.getenv('IP_BAN_HOURS', 24))
PRESALE_WALLET = os.getenv('PRESALE_WALLET', '0xa84e6D0Fa3B35b18FF7C65568C711A85Ac1A9FC7')

# Achievement definitions
ACHIEVEMENTS = [
    {"id": "first_claim", "name": "Airdrop Pioneer", "icon": "🚀", "requirement": 0, "reward": 1},
    {"id": "first_ref", "name": "First Referral", "icon": "🥇", "requirement": 1, "reward": 11},
    {"id": "active_network", "name": "Network Builder", "icon": "🌐", "requirement": 3, "reward": 111},
    {"id": "five_ref", "name": "Referral Master", "icon": "🏆", "requirement": 5, "reward": 1111},
    {"id": "withdrawal_ready", "name": "Ready to Cash Out", "icon": "💰", "requirement": 6, "reward": 11111}
]

# Task definitions
TASKS = [
    # ========== SOCIAL MEDIA TASKS ==========
    {
        "id": "follow_twitter",
        "title": "Follow on Twitter/X",
        "description": "Follow our official Twitter account @GoKiteAI",
        "category": "social",
        "type": "one_time",
        "reward_apro": 50.0,
        "requires_verification": True,
        "verification_type": "twitter_follow",
        "twitter_username": "GoKiteAI",
        "is_active": True
    },
    {
        "id": "retweet_pinned",
        "title": "Retweet Pinned Post",
        "description": "Retweet our latest pinned tweet about APRO Token",
        "category": "social",
        "type": "one_time",
        "reward_apro": 75.0,
        "requires_verification": True,
        "verification_type": "tweet_retweet",
        "tweet_url": "https://twitter.com/GoKiteAI/status/XXXXX",
        "is_active": True
    },
    {
        "id": "join_telegram",
        "title": "Join Telegram Group",
        "description": "Join our official Telegram community",
        "category": "social",
        "type": "one_time",
        "reward_apro": 50.0,
        "requires_verification": True,
        "verification_type": "telegram_join",
        "telegram_link": "https://t.me/gokiteai",
        "is_active": True
    },
    {
        "id": "join_discord",
        "title": "Join Discord Server",
        "description": "Join our Discord community for updates",
        "category": "social",
        "type": "one_time",
        "reward_apro": 50.0,
        "requires_verification": True,
        "verification_type": "discord_join",
        "discord_link": "https://discord.gg/gokiteai",
        "is_active": True
    },
    {
        "id": "daily_checkin",
        "title": "Daily Check-in",
        "description": "Check in daily to maintain your streak",
        "category": "community",
        "type": "daily",
        "reward_apro": 10.0,
        "max_completions": 0,
        "requires_verification": False,
        "is_active": True
    },
    {
        "id": "visit_website",
        "title": "Visit Website Daily",
        "description": "Visit aprotoken.com and stay for 30+ seconds",
        "category": "platform",
        "type": "daily",
        "reward_apro": 5.0,
        "max_completions": 0,
        "requires_verification": True,
        "verification_type": "website_visit",
        "website_url": "https://aprotoken.com",
        "is_active": True
    },
    {
        "id": "read_whitepaper",
        "title": "Read Whitepaper",
        "description": "Read the APRO Token whitepaper (PDF)",
        "category": "platform",
        "type": "one_time",
        "reward_apro": 100.0,
        "requires_verification": True,
        "verification_type": "document_read",
        "document_url": "https://aprotoken.com/whitepaper.pdf",
        "is_active": True
    },
    {
        "id": "create_tweet",
        "title": "Create Tweet About APRO",
        "description": "Create an original tweet about APRO Token with #APRO",
        "category": "content",
        "type": "one_time",
        "reward_apro": 200.0,
        "requires_verification": True,
        "verification_type": "tweet_create",
        "hashtags": ["#APRO", "#Crypto"],
        "is_active": True
    },
    {
        "id": "invite_friends_bonus",
        "title": "Invite 3 Friends",
        "description": "Get 3 friends to join using your referral link",
        "category": "community",
        "type": "one_time",
        "reward_apro": 150.0,
        "requires_verification": False,
        "is_active": True
    },
    {
        "id": "youtube_subscribe",
        "title": "Subscribe to YouTube",
        "description": "Subscribe to our YouTube channel",
        "category": "social",
        "type": "one_time",
        "reward_apro": 50.0,
        "requires_verification": True,
        "verification_type": "youtube_subscribe",
        "youtube_channel": "https://youtube.com/@GoKiteAI",
        "is_active": True
    },
    {
        "id": "weekly_survey",
        "title": "Complete Weekly Survey",
        "description": "Complete this week's community survey",
        "category": "community",
        "type": "weekly",
        "reward_apro": 50.0,
        "max_completions": 0,
        "requires_verification": True,
        "verification_type": "survey_complete",
        "is_active": True
    },
    {
        "id": "like_facebook",
        "title": "Like Facebook Page",
        "description": "Like and follow our Facebook page",
        "category": "social",
        "type": "one_time",
        "reward_apro": 50.0,
        "requires_verification": True,
        "verification_type": "facebook_like",
        "facebook_page": "https://facebook.com/gokiteai",
        "is_active": True
    },
    {
        "id": "make_youtube_video",
        "title": "Make YouTube Video Review",
        "description": "Create a YouTube video reviewing APRO Token",
        "category": "content",
        "type": "one_time",
        "reward_apro": 500.0,
        "requires_verification": True,
        "verification_type": "youtube_video",
        "is_active": True
    },
    {
        "id": "write_blog_post",
        "title": "Write Blog Post",
        "description": "Write a blog post about APRO Token",
        "category": "content",
        "type": "one_time",
        "reward_apro": 300.0,
        "requires_verification": True,
        "verification_type": "blog_post",
        "is_active": True
    },
    {
        "id": "create_tiktok",
        "title": "Create TikTok/Reels Content",
        "description": "Create short-form video content about APRO",
        "category": "content",
        "type": "one_time",
        "reward_apro": 250.0,
        "requires_verification": True,
        "verification_type": "short_video",
        "is_active": True
    }
]

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    wallet = Column(String(42), primary_key=True, nullable=False)
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    referral_count = Column(Integer, default=0, nullable=False)
    link_clicks = Column(Integer, default=0, nullable=False)
    link_conversions = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    referrer = Column(String(42), nullable=True)
    active = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45), nullable=True)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_referrer', 'referrer'),
        Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'wallet': self.wallet,
            'referral_code': self.referral_code,
            'referral_count': self.referral_count,
            'link_clicks': self.link_clicks,
            'link_conversions': self.link_conversions,
            'created_at': self.created_at.isoformat(),
            'referrer': self.referrer,
            'active': self.active,
            'ip_address': self.ip_address,
            'last_active': self.last_active.isoformat()
        }

class AirdropClaim(db.Model):
    __tablename__ = 'airdrop_claims'
    
    id = Column(Integer, primary_key=True)
    wallet = Column(String(42), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    base_amount = Column(Float, nullable=False, default=1005.0)
    referral_bonus = Column(Float, nullable=False, default=0.0)
    achievement_rewards = Column(Float, nullable=False, default=0.0)
    referral_count = Column(Integer, nullable=False, default=0)
    referrer = Column(String(42), nullable=True)
    tx_hash = Column(String(66), unique=True, nullable=False)
    claimed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default='completed', nullable=False)
    
    __table_args__ = (
        Index('idx_claimed_at', 'claimed_at'),
        Index('idx_wallet_status', 'wallet', 'status'),
    )
    
    def to_dict(self):
        return {
            'amount': self.amount,
            'base_amount': self.base_amount,
            'referral_bonus': self.referral_bonus,
            'achievement_rewards': self.achievement_rewards,
            'referral_count': self.referral_count,
            'referrer': self.referrer,
            'tx_hash': self.tx_hash,
            'claimed_at': self.claimed_at.isoformat(),
            'status': self.status
        }

class Referral(db.Model):
    __tablename__ = 'referrals'
    
    id = Column(String(100), primary_key=True)
    referrer = Column(String(42), nullable=False, index=True)
    referee = Column(String(42), nullable=False, index=True)
    code_used = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_referrer_timestamp', 'referrer', 'timestamp'),
        Index('idx_code_used', 'code_used'),
    )

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = Column(Integer, primary_key=True)
    wallet = Column(String(42), nullable=False, index=True)
    achievement_id = Column(String(50), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_wallet_achievement', 'wallet', 'achievement_id', unique=True),
    )

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = Column(String(50), primary_key=True)
    wallet = Column(String(42), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        Index('idx_wallet_read', 'wallet', 'read'),
        Index('idx_timestamp', 'timestamp'),
    )

class IPRestriction(db.Model):
    __tablename__ = 'ip_restrictions'
    
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(45), nullable=False, index=True)
    wallet_count = Column(Integer, default=0, nullable=False)
    last_wallet_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    banned_until = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_ip_banned', 'ip_address', 'banned_until'),
    )

class PresaleContribution(db.Model):
    __tablename__ = 'presale_contributions'
    
    id = Column(String(100), primary_key=True)
    wallet = Column(String(42), nullable=False, index=True)
    amount_eth = Column(Float, nullable=False)
    amount_usd = Column(Float, nullable=False)
    tx_hash = Column(String(66), unique=True, nullable=False)
    chain_id = Column(Integer, nullable=False)
    contributed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    tokens_allocated = Column(Float, nullable=False, default=0.0)
    
    __table_args__ = (
        Index('idx_wallet_chain', 'wallet', 'chain_id'),
        Index('idx_contributed_at', 'contributed_at'),
    )

class WithdrawalAttempt(db.Model):
    __tablename__ = 'withdrawal_attempts'
    
    id = Column(Integer, primary_key=True)
    wallet = Column(String(42), nullable=False, index=True)
    referral_count = Column(Integer, nullable=False)
    eligible = Column(Boolean, nullable=False)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default='checked', nullable=False)
    notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_wallet_attempted', 'wallet', 'attempted_at'),
        Index('idx_eligible_status', 'eligible', 'status'),
    )

class PresaleTransaction(db.Model):
    __tablename__ = 'presale_transactions'
    
    id = Column(Integer, primary_key=True)
    user_address = Column(String(42), nullable=False, index=True)
    usd_amount = Column(Float, nullable=False)
    crypto_amount = Column(String(50), nullable=False)
    token = Column(String(20), nullable=False)
    token_name = Column(String(50), nullable=False)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    network = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    
    __table_args__ = (
        Index('idx_tx_hash', 'tx_hash', unique=True),
        Index('idx_user_timestamp', 'user_address', 'timestamp'),
        Index('idx_network_status', 'network', 'status'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_address': self.user_address,
            'usd_amount': self.usd_amount,
            'crypto_amount': self.crypto_amount,
            'token': self.token,
            'token_name': self.token_name,
            'tx_hash': self.tx_hash,
            'network': self.network,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status
        }

# NEW TASK SYSTEM MODELS
class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = Column(String(50), primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(30), nullable=False)
    type = Column(String(20), nullable=False)
    reward_apro = Column(Float, nullable=False, default=0.0)
    max_completions = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, nullable=False)
    requires_verification = Column(Boolean, default=False, nullable=False)
    verification_type = Column(String(30))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_category_type', 'category', 'type'),
        Index('idx_is_active', 'is_active'),
    )

class UserTask(db.Model):
    __tablename__ = 'user_tasks'
    
    id = Column(Integer, primary_key=True)
    wallet = Column(String(42), nullable=False, index=True)
    task_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default='pending', nullable=False)
    completions = Column(Integer, default=0, nullable=False)
    last_completed = Column(DateTime, nullable=True)
    next_available = Column(DateTime, nullable=True)
    verification_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_wallet_task', 'wallet', 'task_id', unique=True),
        Index('idx_status_next', 'status', 'next_available'),
        Index('idx_wallet_status', 'wallet', 'status'),
    )

class TaskVerification(db.Model):
    __tablename__ = 'task_verifications'
    
    id = Column(Integer, primary_key=True)
    user_task_id = Column(Integer, nullable=False, index=True)
    wallet = Column(String(42), nullable=False, index=True)
    task_id = Column(String(50), nullable=False, index=True)
    verification_type = Column(String(30), nullable=False)
    proof_data = Column(Text, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    reviewed_by = Column(String(42), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_wallet_task_status', 'wallet', 'task_id', 'status'),
        Index('idx_status_created', 'status', 'created_at'),
    )

class DailyStreak(db.Model):
    __tablename__ = 'daily_streaks'
    
    wallet = Column(String(42), primary_key=True)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_checkin = Column(DateTime, nullable=True)
    total_checkins = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# Helper class
class AirdropSystem:
    @staticmethod
    def generate_referral_code(wallet_address):
        return f"REF-{hashlib.md5(wallet_address.encode()).hexdigest()[:8].upper()}"
    
    @staticmethod
    def calculate_airdrop_amount(referral_count, achievement_rewards=0):
        base_amount = 1005.0
        referral_bonus = referral_count * 121
        return base_amount + referral_bonus + achievement_rewards
    
    @staticmethod
    def generate_tx_hash():
        return f"0x{secrets.token_hex(32)}"
    
    @staticmethod
    def generate_notification_id():
        return f"NOTIF_{secrets.token_hex(8)}"
    
    @staticmethod
    def generate_referral_id(referrer, referee):
        return f"{referrer}_{referee}"
    
    @staticmethod
    def validate_wallet_address(wallet_address):
        if not wallet_address:
            return False, "Wallet address is required"
        
        wallet = wallet_address.strip().lower()
        
        if not wallet.startswith('0x'):
            return False, "Wallet address must start with '0x'"
        
        if len(wallet) != 42:
            return False, "Wallet address must be 42 characters (including '0x')"
        
        hex_part = wallet[2:]
        if not all(c in '0123456789abcdef' for c in hex_part):
            return False, "Wallet address contains invalid characters"
        
        return True, wallet

# FIXED: Achievement calculation function
def check_and_award_achievements(wallet_address):
    user = User.query.get(wallet_address)
    if not user:
        return
    
    referral_count = user.referral_count
    
    current_achievements = Achievement.query.filter_by(wallet=wallet_address).all()
    current_achievement_ids = [a.achievement_id for a in current_achievements]
    
    for achievement in ACHIEVEMENTS:
        if achievement['id'] not in current_achievement_ids:
            should_award = False
            
            if achievement['id'] == 'first_claim':
                claim = AirdropClaim.query.filter_by(wallet=wallet_address).first()
                if claim:
                    should_award = True
            elif achievement['requirement'] <= referral_count:
                should_award = True
            
            if should_award:
                achievement_record = Achievement(
                    wallet=wallet_address,
                    achievement_id=achievement['id']
                )
                db.session.add(achievement_record)
                
                notification = Notification(
                    id=AirdropSystem.generate_notification_id(),
                    wallet=wallet_address,
                    type='achievement',
                    message=f'🏆 Achievement unlocked: {achievement["name"]}! +{achievement["reward"]} APRO',
                    timestamp=datetime.utcnow(),
                    read=False
                )
                db.session.add(notification)
    
    db.session.commit()

def calculate_achievement_rewards(wallet_address):
    user_achievements = Achievement.query.filter_by(wallet=wallet_address).all()
    achievement_ids = [a.achievement_id for a in user_achievements]
    
    achievement_rewards = 0
    for achievement in ACHIEVEMENTS:
        if achievement['id'] in achievement_ids:
            achievement_rewards += achievement['reward']
    
    return achievement_rewards

# ==================== TASK SYSTEM ENDPOINTS ====================

@app.route('/api/tasks/get-all', methods=['GET'])
def get_all_tasks():
    wallet_address = request.args.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({
            'success': False,
            'message': 'Wallet address required'
        })
    
    user_tasks = {}
    if wallet_address:
        tasks = UserTask.query.filter_by(wallet=wallet_address).all()
        for task in tasks:
            user_tasks[task.task_id] = {
                'status': task.status,
                'completions': task.completions,
                'last_completed': task.last_completed.isoformat() if task.last_completed else None,
                'next_available': task.next_available.isoformat() if task.next_available else None
            }
    
    tasks_list = []
    for task_def in TASKS:
        if not task_def.get('is_active', True):
            continue
            
        user_task = user_tasks.get(task_def['id'], {})
        
        can_complete = False
        next_available = None
        
        if user_task:
            if task_def['type'] in ['daily', 'weekly']:
                now = datetime.utcnow()
                if user_task['next_available']:
                    next_available_dt = datetime.fromisoformat(user_task['next_available'].replace('Z', '+00:00'))
                    can_complete = now >= next_available_dt
                    if not can_complete:
                        next_available = next_available_dt.isoformat()
                else:
                    can_complete = True
            else:
                can_complete = user_task['status'] in ['pending', 'verified']
        else:
            can_complete = True
        
        tasks_list.append({
            'id': task_def['id'],
            'title': task_def['title'],
            'description': task_def['description'],
            'category': task_def['category'],
            'type': task_def['type'],
            'reward_apro': task_def['reward_apro'],
            'requires_verification': task_def.get('requires_verification', False),
            'verification_type': task_def.get('verification_type'),
            'user_status': user_task.get('status', 'pending'),
            'user_completions': user_task.get('completions', 0),
            'can_complete': can_complete,
            'next_available': next_available,
            'max_completions': task_def.get('max_completions', 1)
        })
    
    grouped_tasks = {}
    for task in tasks_list:
        category = task['category']
        if category not in grouped_tasks:
            grouped_tasks[category] = []
        grouped_tasks[category].append(task)
    
    streak = DailyStreak.query.get(wallet_address)
    streak_data = {
        'current_streak': streak.current_streak if streak else 0,
        'longest_streak': streak.longest_streak if streak else 0,
        'total_checkins': streak.total_checkins if streak else 0,
        'last_checkin': streak.last_checkin.isoformat() if streak and streak.last_checkin else None
    }
    
    return jsonify({
        'success': True,
        'tasks': grouped_tasks,
        'streak': streak_data,
        'total_rewards_available': calculate_available_task_rewards(wallet_address)
    })

@app.route('/api/tasks/start', methods=['POST'])
@limiter.limit("10 per minute")
def start_task():
    data = request.json or {}
    wallet_address = data.get('wallet', '').strip().lower()
    task_id = data.get('task_id', '')
    
    if not wallet_address or not task_id:
        return jsonify({
            'success': False,
            'message': 'Wallet and task ID required'
        })
    
    task_def = next((t for t in TASKS if t['id'] == task_id), None)
    if not task_def:
        return jsonify({
            'success': False,
            'message': 'Task not found'
        })
    
    user_task = UserTask.query.filter_by(wallet=wallet_address, task_id=task_id).first()
    
    if not user_task:
        user_task = UserTask(
            wallet=wallet_address,
            task_id=task_id,
            status='pending'
        )
        db.session.add(user_task)
    else:
        if task_def['type'] in ['one_time'] and user_task.completions >= task_def.get('max_completions', 1):
            return jsonify({
                'success': False,
                'message': 'Task already completed'
            })
        
        if task_def['type'] in ['daily', 'weekly'] and user_task.next_available:
            now = datetime.utcnow()
            if now < user_task.next_available:
                return jsonify({
                    'success': False,
                    'message': f'Task available again at {user_task.next_available.strftime("%Y-%m-%d %H:%M UTC")}'
                })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Task started',
        'task_id': task_id,
        'requires_verification': task_def.get('requires_verification', False)
    })

@app.route('/api/tasks/complete', methods=['POST'])
@limiter.limit("10 per minute")
def complete_task():
    data = request.json or {}
    wallet_address = data.get('wallet', '').strip().lower()
    task_id = data.get('task_id', '')
    
    if not wallet_address or not task_id:
        return jsonify({
            'success': False,
            'message': 'Wallet and task ID required'
        })
    
    task_def = next((t for t in TASKS if t['id'] == task_id), None)
    if not task_def:
        return jsonify({
            'success': False,
            'message': 'Task not found'
        })
    
    if task_def.get('requires_verification', False):
        return jsonify({
            'success': False,
            'message': 'This task requires verification',
            'requires_verification': True
        })
    
    user = User.query.get(wallet_address)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        })
    
    if task_id == 'invite_friends_bonus':
        if user.referral_count < 3:
            return jsonify({
                'success': False,
                'message': f'Need {3 - user.referral_count} more referrals to complete this task'
            })
    
    return process_task_completion(wallet_address, task_id, task_def)

@app.route('/api/tasks/submit-verification', methods=['POST'])
@limiter.limit("5 per minute")
def submit_verification():
    data = request.json or {}
    wallet_address = data.get('wallet', '').strip().lower()
    task_id = data.get('task_id', '')
    proof_data = data.get('proof', {})
    verification_type = data.get('verification_type', '')
    
    if not wallet_address or not task_id or not proof_data:
        return jsonify({
            'success': False,
            'message': 'Missing required data'
        })
    
    task_def = next((t for t in TASKS if t['id'] == task_id), None)
    if not task_def:
        return jsonify({
            'success': False,
            'message': 'Task not found'
        })
    
    if not task_def.get('requires_verification', False):
        return jsonify({
            'success': False,
            'message': 'This task does not require verification'
        })
    
    user_task = UserTask.query.filter_by(wallet=wallet_address, task_id=task_id).first()
    if not user_task:
        return jsonify({
            'success': False,
            'message': 'Task not started'
        })
    
    verification = TaskVerification(
        user_task_id=user_task.id,
        wallet=wallet_address,
        task_id=task_id,
        verification_type=verification_type or task_def.get('verification_type', ''),
        proof_data=json.dumps(proof_data),
        status='pending',
        created_at=datetime.utcnow()
    )
    db.session.add(verification)
    
    user_task.status = 'pending_verification'
    user_task.verification_data = json.dumps(proof_data)
    
    notification = Notification(
        id=AirdropSystem.generate_notification_id(),
        wallet=wallet_address,
        type='task_verification',
        message=f'✅ Verification submitted for task: {task_def["title"]}',
        timestamp=datetime.utcnow(),
        read=False
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Verification submitted successfully. Our team will review it shortly.',
        'verification_id': verification.id
    })

@app.route('/api/tasks/claim-reward', methods=['POST'])
@limiter.limit("10 per minute")
def claim_task_reward():
    data = request.json or {}
    wallet_address = data.get('wallet', '').strip().lower()
    task_id = data.get('task_id', '')
    
    if not wallet_address or not task_id:
        return jsonify({
            'success': False,
            'message': 'Wallet and task ID required'
        })
    
    user_task = UserTask.query.filter_by(wallet=wallet_address, task_id=task_id).first()
    if not user_task:
        return jsonify({
            'success': False,
            'message': 'Task not found'
        })
    
    if user_task.status != 'completed':
        return jsonify({
            'success': False,
            'message': 'Task not completed or reward already claimed'
        })
    
    task_def = next((t for t in TASKS if t['id'] == task_id), None)
    if not task_def:
        return jsonify({
            'success': False,
            'message': 'Task definition not found'
        })
    
    reward_amount = task_def['reward_apro']
    
    claim = AirdropClaim(
        wallet=wallet_address,
        amount=reward_amount,
        base_amount=0.0,
        referral_bonus=0.0,
        achievement_rewards=0.0,
        referral_count=0,
        referrer=None,
        tx_hash=f"TASK_{task_id}_{secrets.token_hex(8)}",
        claimed_at=datetime.utcnow(),
        status='completed'
    )
    db.session.add(claim)
    
    user_task.status = 'claimed'
    
    notification = Notification(
        id=AirdropSystem.generate_notification_id(),
        wallet=wallet_address,
        type='task_reward',
        message=f'🎉 Claimed {reward_amount} APRO for completing: {task_def["title"]}',
        timestamp=datetime.utcnow(),
        read=False
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Successfully claimed {reward_amount} APRO!',
        'reward_amount': reward_amount,
        'task_id': task_id
    })

@app.route('/api/tasks/daily-checkin', methods=['POST'])
@limiter.limit("5 per minute")
def daily_checkin():
    data = request.json or {}
    wallet_address = data.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({
            'success': False,
            'message': 'Wallet address required'
        })
    
    user = User.query.get(wallet_address)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        })
    
    now = datetime.utcnow()
    
    streak = DailyStreak.query.get(wallet_address)
    if not streak:
        streak = DailyStreak(wallet=wallet_address)
        db.session.add(streak)
    
    if streak.last_checkin:
        last_checkin_date = streak.last_checkin.date()
        today = now.date()
        
        if last_checkin_date == today:
            return jsonify({
                'success': False,
                'message': 'Already checked in today'
            })
        
        yesterday = today - timedelta(days=1)
        if last_checkin_date == yesterday:
            streak.current_streak += 1
        else:
            streak.current_streak = 1
    
    else:
        streak.current_streak = 1
    
    streak.last_checkin = now
    streak.total_checkins += 1
    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    
    task_def = next((t for t in TASKS if t['id'] == 'daily_checkin'), None)
    if task_def:
        process_task_completion(wallet_address, 'daily_checkin', task_def)
    
    bonus_amount = 0
    if streak.current_streak % 7 == 0:
        bonus_amount = 50.0
    elif streak.current_streak % 30 == 0:
        bonus_amount = 200.0
    
    if bonus_amount > 0:
        bonus_claim = AirdropClaim(
            wallet=wallet_address,
            amount=bonus_amount,
            base_amount=0.0,
            referral_bonus=0.0,
            achievement_rewards=0.0,
            referral_count=0,
            referrer=None,
            tx_hash=f"STREAK_{streak.current_streak}_{secrets.token_hex(6)}",
            claimed_at=now,
            status='completed'
        )
        db.session.add(bonus_claim)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Daily check-in successful! Current streak: {streak.current_streak} days',
        'streak': {
            'current': streak.current_streak,
            'longest': streak.longest_streak,
            'total': streak.total_checkins,
            'bonus_earned': bonus_amount
        }
    })

# ==================== TASK HELPER FUNCTIONS ====================

def process_task_completion(wallet_address, task_id, task_def):
    user_task = UserTask.query.filter_by(wallet=wallet_address, task_id=task_id).first()
    if not user_task:
        user_task = UserTask(
            wallet=wallet_address,
            task_id=task_id,
            status='pending',
            completions=0
        )
        db.session.add(user_task)
    
    user_task.completions += 1
    user_task.last_completed = datetime.utcnow()
    user_task.status = 'completed'
    
    if task_def['type'] == 'daily':
        user_task.next_available = datetime.utcnow() + timedelta(days=1)
    elif task_def['type'] == 'weekly':
        user_task.next_available = datetime.utcnow() + timedelta(weeks=1)
    else:
        user_task.next_available = None
    
    notification = Notification(
        id=AirdropSystem.generate_notification_id(),
        wallet=wallet_address,
        type='task_complete',
        message=f'✅ Task completed: {task_def["title"]}! Earned {task_def["reward_apro"]} APRO',
        timestamp=datetime.utcnow(),
        read=False
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Task completed! You earned {task_def["reward_apro"]} APRO',
        'reward_amount': task_def['reward_apro'],
        'completions': user_task.completions,
        'next_available': user_task.next_available.isoformat() if user_task.next_available else None
    })

def calculate_available_task_rewards(wallet_address):
    user_tasks = UserTask.query.filter_by(
        wallet=wallet_address,
        status='completed'
    ).all()
    
    total_rewards = 0
    for user_task in user_tasks:
        task_def = next((t for t in TASKS if t['id'] == user_task.task_id), None)
        if task_def:
            total_rewards += task_def['reward_apro']
    
    return total_rewards

# ==================== ADMIN TASK MANAGEMENT ====================

@app.route('/api/admin/tasks/verify', methods=['POST'])
def admin_verify_task():
    data = request.json or {}
    admin_key = data.get('admin_key', '')
    verification_id = data.get('verification_id')
    status = data.get('status')
    notes = data.get('notes', '')
    
    if admin_key != ADMIN_API_KEY:
        return jsonify({
            'success': False,
            'error': 'Unauthorized'
        }), 401
    
    if not verification_id or not status:
        return jsonify({
            'success': False,
            'message': 'Verification ID and status required'
        })
    
    verification = TaskVerification.query.get(verification_id)
    if not verification:
        return jsonify({
            'success': False,
            'message': 'Verification not found'
        })
    
    verification.status = status
    verification.reviewed_by = ADMIN_WALLET
    verification.reviewed_at = datetime.utcnow()
    verification.notes = notes
    
    if status == 'approved':
        user_task = UserTask.query.get(verification.user_task_id)
        if user_task:
            user_task.status = 'completed'
            
            notification = Notification(
                id=AirdropSystem.generate_notification_id(),
                wallet=verification.wallet,
                type='task_approved',
                message=f'✅ Your task verification was approved!',
                timestamp=datetime.utcnow(),
                read=False
            )
            db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Verification {status}',
        'verification_id': verification_id
    })

@app.route('/api/admin/tasks/pending', methods=['GET'])
def get_pending_verifications():
    admin_key = request.args.get('admin_key', '')
    if admin_key != ADMIN_API_KEY:
        return jsonify({
            'success': False,
            'error': 'Unauthorized'
        }), 401
    
    pending = TaskVerification.query.filter_by(
        status='pending'
    ).order_by(
        TaskVerification.created_at.asc()
    ).all()
    
    verifications = []
    for v in pending:
        task_def = next((t for t in TASKS if t['id'] == v.task_id), None)
        
        verifications.append({
            'id': v.id,
            'wallet': v.wallet,
            'task_id': v.task_id,
            'task_title': task_def['title'] if task_def else 'Unknown Task',
            'verification_type': v.verification_type,
            'proof_data': json.loads(v.proof_data) if v.proof_data else {},
            'created_at': v.created_at.isoformat(),
            'display_wallet': f"{v.wallet[:6]}...{v.wallet[-4:]}"
        })
    
    return jsonify({
        'success': True,
        'pending_count': len(pending),
        'verifications': verifications
    })

# ==================== WEB3 PRESALE TRANSACTION ENDPOINTS ====================

@app.route('/api/transaction', methods=['POST'])
@limiter.limit("10 per minute")
def record_transaction():
    try:
        data = request.json or {}
        
        required_fields = ['user_address', 'usd_amount', 'crypto_amount', 
                          'token', 'token_name', 'tx_hash', 'network']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False, 
                    'error': f'Missing field: {field}'
                }), 400
        
        is_valid, wallet_or_error = AirdropSystem.validate_wallet_address(data['user_address'])
        if not is_valid:
            return jsonify({
                'success': False, 
                'error': wallet_or_error
            }), 400
        
        wallet_address = wallet_or_error
        
        existing = PresaleTransaction.query.filter_by(tx_hash=data['tx_hash']).first()
        if existing:
            return jsonify({
                'success': False, 
                'error': 'Transaction already recorded'
            }), 400
        
        transaction = PresaleTransaction(
            user_address=wallet_address,
            usd_amount=float(data['usd_amount']),
            crypto_amount=str(data['crypto_amount']),
            token=data['token'],
            token_name=data['token_name'],
            tx_hash=data['tx_hash'],
            network=data['network'],
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat())),
            status='confirmed'
        )
        
        db.session.add(transaction)
        
        user = User.query.get(wallet_address)
        if not user:
            referral_code = AirdropSystem.generate_referral_code(wallet_address)
            user = User(
                wallet=wallet_address,
                referral_code=referral_code,
                referral_count=0,
                link_clicks=0,
                link_conversions=0,
                referrer=None,
                active=False,
                ip_address=get_remote_address(),
                last_active=datetime.utcnow()
            )
            db.session.add(user)
        
        notification = Notification(
            id=AirdropSystem.generate_notification_id(),
            wallet=wallet_address,
            type='presale',
            message=f'✅ Presale contribution confirmed! ${float(data["usd_amount"]):.2f} USD via {data["token_name"]}',
            timestamp=datetime.utcnow(),
            read=False
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Transaction recorded successfully',
            'id': transaction.id,
            'data': transaction.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        admin_key = request.args.get('admin_key', '')
        if admin_key != ADMIN_API_KEY:
            return jsonify({
                'success': False, 
                'error': 'Unauthorized'
            }), 401
        
        transactions = PresaleTransaction.query.order_by(
            PresaleTransaction.timestamp.desc()
        ).all()
        
        total_usd = db.session.query(db.func.sum(PresaleTransaction.usd_amount)).scalar() or 0
        total_transactions = len(transactions)
        
        unique_users = db.session.query(
            db.func.count(db.func.distinct(PresaleTransaction.user_address))
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_transactions': total_transactions,
                'total_usd': float(total_usd),
                'unique_users': unique_users
            },
            'transactions': [t.to_dict() for t in transactions]
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/user-transactions/<wallet_address>', methods=['GET'])
def get_user_transactions(wallet_address):
    try:
        is_valid, wallet_or_error = AirdropSystem.validate_wallet_address(wallet_address)
        if not is_valid:
            return jsonify({
                'success': False, 
                'error': wallet_or_error
            }), 400
        
        wallet_address = wallet_or_error
        
        transactions = PresaleTransaction.query.filter_by(
            user_address=wallet_address
        ).order_by(
            PresaleTransaction.timestamp.desc()
        ).all()
        
        total_usd = sum(t.usd_amount for t in transactions)
        
        return jsonify({
            'success': True,
            'user_address': wallet_address,
            'total_contributions': len(transactions),
            'total_usd': total_usd,
            'transactions': [t.to_dict() for t in transactions]
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

# ==================== WITHDRAWAL ENDPOINTS ====================

@app.route('/api/check-withdrawal-eligibility', methods=['GET'])
def check_withdrawal_eligibility():
    wallet_address = request.args.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({'success': False, 'message': 'Wallet address required'})
    
    user = User.query.get(wallet_address)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    direct_referrals = Referral.query.filter_by(referrer=wallet_address).all()
    active_referrals_count = 0
    for referral in direct_referrals:
        claim = AirdropClaim.query.filter_by(wallet=referral.referee).first()
        if claim:
            active_referrals_count += 1
    
    is_eligible = active_referrals_count >= 7
    
    return jsonify({
        'success': True,
        'is_eligible': is_eligible,
        'referral_count': active_referrals_count,
        'required_count': 7,
        'remaining_needed': max(0, 7 - active_referrals_count),
        'message': 'Eligible for withdrawal' if is_eligible else f'Need {7 - active_referrals_count} more active referrals'
    })

@app.route('/api/simulate-withdrawal', methods=['POST'])
@limiter.limit("5 per minute")
def simulate_withdrawal():
    data = request.json or {}
    wallet_address = data.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({'success': False, 'message': 'Wallet address required'})
    
    user = User.query.get(wallet_address)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    direct_referrals = Referral.query.filter_by(referrer=wallet_address).all()
    active_referrals_count = 0
    for referral in direct_referrals:
        claim = AirdropClaim.query.filter_by(wallet=referral.referee).first()
        if claim:
            active_referrals_count += 1
    
    withdrawal_attempt = WithdrawalAttempt(
        wallet=wallet_address,
        referral_count=active_referrals_count,
        eligible=(active_referrals_count >= 7),
        attempted_at=datetime.utcnow(),
        status='checked',
        notes='User checked withdrawal eligibility'
    )
    db.session.add(withdrawal_attempt)
    db.session.commit()
    
    if active_referrals_count < 7:
        return jsonify({
            'success': True,
            'is_eligible': False,
            'referral_count': active_referrals_count,
            'required_count': 7,
            'remaining_needed': 7 - active_referrals_count,
            'message': '❌ You are not yet eligible for withdrawals. Ensure you invite at least 7 friends or more to be eligible to withdraw ✨',
            'progress_message': f'📈 Progress to Unlock Withdrawals\nYou need {7 - active_referrals_count} more referrals to unlock withdrawal access.\nInvite friends now to secure your airdrop position!\nCurrent Referrals: [{active_referrals_count}/7]'
        })
    
    return jsonify({
        'success': True,
        'is_eligible': True,
        'referral_count': active_referrals_count,
        'message': f'🎉 Congratulations! You\'ve unlocked withdrawal eligibility!\n\nWithdrawals will be available starting January 15th. Keep inviting friends to maximize your airdrop rewards!\nCurrent Referrals: [{active_referrals_count}/7]',
        'withdrawal_date': '2026-01-15',
        'note': 'Withdrawals will be processed automatically after January 15th, 2026'
    })

# ==================== EXISTING API ENDPOINTS ====================

@app.route('/api/get-referral-stats', methods=['GET'])
def get_referral_stats():
    wallet_address = request.args.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({
            'success': False,
            'message': 'Wallet address is required'
        })
    
    user = User.query.get(wallet_address)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        })
    
    conversion_rate = 0
    if user.link_clicks > 0:
        conversion_rate = round((user.link_conversions / user.link_clicks) * 100, 1)
    
    return jsonify({
        'success': True,
        'data': {
            'referral_count': user.referral_count,
            'link_clicks': user.link_clicks,
            'link_conversions': user.link_conversions,
            'conversion_rate': conversion_rate,
            'total_bonus': user.referral_count * 121,
            'referral_code': user.referral_code,
            'is_active': user.active
        }
    })

@app.route('/api/get-network-analysis', methods=['GET'])
def get_network_analysis():
    wallet_address = request.args.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({
            'success': False,
            'message': 'Wallet address is required'
        })
    
    user = User.query.get(wallet_address)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        })
    
    direct_referrals = Referral.query.filter_by(referrer=wallet_address).all()
    direct_referrals_count = len(direct_referrals)
    
    active_referrals_count = 0
    for referral in direct_referrals:
        claim = AirdropClaim.query.filter_by(wallet=referral.referee).first()
        if claim:
            active_referrals_count += 1
    
    inactive_referrals_count = direct_referrals_count - active_referrals_count
    
    total_amount = 1005.0 + (user.referral_count * 121) + calculate_achievement_rewards(wallet_address)
    
    can_withdraw = active_referrals_count >= 7
    available_for_withdrawal = total_amount if can_withdraw else 0
    
    return jsonify({
        'success': True,
        'data': {
            'direct_referrals_count': direct_referrals_count,
            'active_referrals_count': active_referrals_count,
            'inactive_referrals_count': inactive_referrals_count,
            'total_amount': total_amount,
            'can_withdraw': can_withdraw,
            'available_for_withdrawal': available_for_withdrawal,
            'withdrawal_message': f'Need {7 - active_referrals_count} more active referrals to withdraw' if not can_withdraw else 'Eligible for withdrawal'
        }
    })

@app.route('/api/get-achievements', methods=['GET'])
def get_achievements():
    wallet_address = request.args.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({
            'success': False,
            'message': 'Wallet address is required'
        })
    
    user = User.query.get(wallet_address)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        })
    
    unlocked_achievements = Achievement.query.filter_by(wallet=wallet_address).all()
    unlocked_ids = [a.achievement_id for a in unlocked_achievements]
    
    achievements_list = []
    total_unlocked = 0
    total_rewards = 0
    
    for achievement_def in ACHIEVEMENTS:
        unlocked = achievement_def['id'] in unlocked_ids
        if unlocked:
            total_unlocked += 1
            total_rewards += achievement_def['reward']
        
        achievements_list.append({
            'id': achievement_def['id'],
            'name': achievement_def['name'],
            'icon': achievement_def['icon'],
            'requirement': achievement_def['requirement'],
            'reward': achievement_def['reward'],
            'unlocked': unlocked,
            'description': f"Earn {achievement_def['reward']} APRO bonus for {achievement_def['name'].lower()}"
        })
    
    return jsonify({
        'success': True,
        'data': {
            'achievements': achievements_list,
            'total_unlocked': total_unlocked,
            'total_rewards': total_rewards,
            'referral_count': user.referral_count,
            'progress_percentage': round((total_unlocked / len(ACHIEVEMENTS)) * 100)
        }
    })

@app.route('/api/track-link-click', methods=['POST'])
@limiter.limit("50 per minute")
def track_link_click():
    data = request.json or {}
    referral_code = data.get('referral_code', '').strip().upper()
    
    if not referral_code:
        return jsonify({
            'success': False,
            'message': 'Referral code is required'
        })
    
    user = User.query.filter_by(referral_code=referral_code).first()
    if not user:
        return jsonify({
            'success': False,
            'message': 'Invalid referral code'
        })
    
    user.link_clicks += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Link click tracked',
        'data': {
            'referral_code': referral_code,
            'total_clicks': user.link_clicks
        }
    })

# In app.py, add:
@app.route('/api/get-total-balance', methods=['GET'])
def get_total_balance():
    wallet_address = request.args.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({'success': False, 'message': 'Wallet required'})
    
    total = 0
    
    # 1. Original airdrop claim
    claim = AirdropClaim.query.filter_by(wallet=wallet_address, status='completed').first()
    if claim:
        total += claim.amount
    
    # 2. Task rewards (claimed)
    task_claims = AirdropClaim.query.filter(
        AirdropClaim.wallet == wallet_address,
        AirdropClaim.tx_hash.like('TASK_%')
    ).all()
    for tc in task_claims:
        total += tc.amount
    
    # 3. Streak bonuses (claimed)
    streak_claims = AirdropClaim.query.filter(
        AirdropClaim.wallet == wallet_address,
        AirdropClaim.tx_hash.like('STREAK_%')
    ).all()
    for sc in streak_claims:
        total += sc.amount
    
    return jsonify({
        'success': True,
        'total_balance': total,
        'breakdown': {
            'airdrop': claim.amount if claim else 0,
            'task_rewards': sum(tc.amount for tc in task_claims),
            'streak_bonuses': sum(sc.amount for sc in streak_claims)
        }
    })

@app.route('/api/get-notifications', methods=['GET'])
def get_notifications():
    wallet_address = request.args.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({
            'success': False,
            'message': 'Wallet address is required'
        })
    
    notifications = Notification.query.filter_by(wallet=wallet_address)\
        .order_by(Notification.timestamp.desc())\
        .limit(50)\
        .all()
    
    unread_count = Notification.query.filter_by(wallet=wallet_address, read=False).count()
    
    return jsonify({
        'success': True,
        'data': {
            'notifications': [{
                'id': n.id,
                'type': n.type,
                'message': n.message,
                'timestamp': n.timestamp.isoformat(),
                'read': n.read
            } for n in notifications],
            'unread_count': unread_count,
            'total_count': len(notifications)
        }
    })

@app.route('/api/mark-notification-read', methods=['POST'])
@limiter.limit("20 per minute")
def mark_notification_read():
    data = request.json or {}
    notification_id = data.get('notification_id', '')
    
    if not notification_id:
        return jsonify({
            'success': False,
            'message': 'Notification ID is required'
        })
    
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({
            'success': False,
            'message': 'Notification not found'
        })
    
    notification.read = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Notification marked as read'
    })

# ==================== PRESALE ENDPOINTS ====================

@app.route('/api/get-presale-address', methods=['GET'])
def get_presale_address():
    return jsonify({
        'success': True,
        'address': PRESALE_WALLET,
        'network': 'Ethereum Mainnet',
        'chain_id': 1,
        'note': 'Send ETH only from personal wallet (not exchange)'
    })

@app.route('/api/record-presale-contribution', methods=['POST'])
@limiter.limit("5 per minute")
def record_presale_contribution():
    data = request.json or {}
    wallet_address = data.get('wallet_address', '').strip().lower()
    amount_eth = float(data.get('amount_eth', 0.0))
    tx_hash = data.get('tx_hash', '')
    chain_id = int(data.get('chain_id', 1))
    
    if not wallet_address or amount_eth <= 0 or not tx_hash:
        return jsonify({
            'success': False,
            'message': 'Invalid data'
        })
    
    return jsonify({
        'success': False,
        'message': 'This endpoint is deprecated. Use Web3 payment gateway instead.'
    })

@app.route('/api/get-presale-contributions', methods=['GET'])
def get_presale_contributions():
    wallet_address = request.args.get('wallet', '').strip().lower()
    
    if not wallet_address:
        return jsonify({'success': False, 'message': 'Wallet address required'})
    
    old_contributions = PresaleContribution.query.filter_by(
        wallet=wallet_address
    ).order_by(
        PresaleContribution.contributed_at.desc()
    ).all()
    
    new_transactions = PresaleTransaction.query.filter_by(
        user_address=wallet_address
    ).order_by(
        PresaleTransaction.timestamp.desc()
    ).all()
    
    total_eth = sum(c.amount_eth for c in old_contributions)
    total_tokens = sum(c.tokens_allocated for c in old_contributions)
    total_usd_new = sum(t.usd_amount for t in new_transactions)
    
    return jsonify({
        'success': True,
        'data': {
            'old_contributions': [{
                'amount_eth': c.amount_eth,
                'amount_usd': c.amount_usd,
                'tokens_allocated': c.tokens_allocated,
                'tx_hash': c.tx_hash,
                'chain_id': c.chain_id,
                'timestamp': c.contributed_at.isoformat(),
                'status': c.status
            } for c in old_contributions],
            'web3_transactions': [{
                'usd_amount': t.usd_amount,
                'crypto_amount': t.crypto_amount,
                'token': t.token,
                'token_name': t.token_name,
                'tx_hash': t.tx_hash,
                'network': t.network,
                'timestamp': t.timestamp.isoformat(),
                'status': t.status
            } for t in new_transactions],
            'total_eth': total_eth,
            'total_tokens': total_tokens,
            'total_usd_web3': total_usd_new,
            'total_contributions': len(old_contributions) + len(new_transactions)
        }
    })

# ==================== EXISTING AIRDROP ENDPOINTS ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.before_request
def check_ip_restriction():
    if request.endpoint in ['check_wallet', 'claim_airdrop']:
        ip_address = get_remote_address()
        
        wallet_address = None
        if request.is_json:
            data = request.get_json(silent=True) or {}
            wallet_address = data.get('wallet_address', '').strip().lower()
        
        if wallet_address == ADMIN_WALLET.lower():
            return
        
        restriction = IPRestriction.query.filter_by(ip_address=ip_address).first()
        
        if restriction:
            if restriction.banned_until and datetime.utcnow() < restriction.banned_until:
                return jsonify({
                    'success': False,
                    'message': f'IP temporarily restricted. Try again after {restriction.banned_until.strftime("%Y-%m-%d %H:%M UTC")}'
                }), 429
            
            if restriction.wallet_count >= MAX_WALLETS_PER_IP:
                restriction.banned_until = datetime.utcnow() + timedelta(hours=IP_BAN_HOURS)
                db.session.commit()
                return jsonify({
                    'success': False,
                    'message': f'Maximum wallet limit ({MAX_WALLETS_PER_IP}) reached from this IP address. Temporary restriction applied.'
                }), 429

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/check-wallet', methods=['POST'])
@limiter.limit("10 per minute")
def check_wallet():
    data = request.json or {}
    wallet_address = data.get('wallet_address', '').strip()
    
    is_valid, wallet_or_error = AirdropSystem.validate_wallet_address(wallet_address)
    if not is_valid:
        return jsonify({
            'success': False,
            'eligible': False,
            'message': wallet_or_error
        })
    
    wallet_address = wallet_or_error
    
    ip_address = get_remote_address()
    
    claim = AirdropClaim.query.filter_by(wallet=wallet_address).first()
    
    if claim:
        user = User.query.get(wallet_address)
        current_referral_count = user.referral_count if user else 0
        
        achievement_rewards = calculate_achievement_rewards(wallet_address)
        
        total_amount = AirdropSystem.calculate_airdrop_amount(
            current_referral_count, 
            float(achievement_rewards)
        )
        
        return jsonify({
            'success': True,
            'eligible': False,
            'message': 'Wallet has already claimed tokens',
            'already_claimed': True,
            'claim_data': {
                'amount': total_amount,
                'base_amount': 1005.0,
                'referral_bonus': current_referral_count * 121,
                'achievement_rewards': float(achievement_rewards),
                'referral_count': current_referral_count,
                'tx_hash': claim.tx_hash,
                'timestamp': claim.claimed_at.isoformat(),
                'referrer': claim.referrer
            },
            'referral_code': user.referral_code if user else None,
            'can_still_refer': True
        })
    
    is_eligible = True
    reasons = []
    
    if len(wallet_address.replace('0x', '')) < 40:
        is_eligible = False
        reasons.append("Invalid wallet format")
    
    if is_eligible:
        restriction = IPRestriction.query.filter_by(ip_address=ip_address).first()
        if restriction and restriction.wallet_count >= MAX_WALLETS_PER_IP:
            is_eligible = False
            reasons.append(f"Maximum wallets ({MAX_WALLETS_PER_IP}) reached from this IP")
    
    referral_code = None
    user = User.query.get(wallet_address)
    user_exists = user is not None
    
    if is_eligible:
        if not user_exists:
            referral_code = AirdropSystem.generate_referral_code(wallet_address)
            user = User(
                wallet=wallet_address,
                referral_code=referral_code,
                referral_count=0,
                link_clicks=0,
                link_conversions=0,
                referrer=None,
                active=False,
                ip_address=ip_address,
                last_active=datetime.utcnow()
            )
            db.session.add(user)
            
            restriction = IPRestriction.query.filter_by(ip_address=ip_address).first()
            if restriction:
                restriction.wallet_count += 1
                restriction.last_wallet_created = datetime.utcnow()
            else:
                restriction = IPRestriction(
                    ip_address=ip_address,
                    wallet_count=1,
                    last_wallet_created=datetime.utcnow()
                )
                db.session.add(restriction)
            
            notification = Notification(
                id=AirdropSystem.generate_notification_id(),
                wallet=wallet_address,
                type='welcome',
                message='Welcome to APRO Airdrop! Claim your first tokens.',
                timestamp=datetime.utcnow(),
                read=False
            )
            db.session.add(notification)
            
            db.session.commit()
        else:
            referral_code = user.referral_code
            user.last_active = datetime.utcnow()
            db.session.commit()
    
    return jsonify({
        'success': True,
        'eligible': is_eligible,
        'message': 'Wallet is eligible for airdrop' if is_eligible else 'Not eligible: ' + ', '.join(reasons),
        'referral_code': referral_code,
        'base_amount': 1005.0,
        'user_exists': user_exists
    })

@app.route('/api/claim-airdrop', methods=['POST'])
@limiter.limit("5 per minute")
def claim_airdrop():
    data = request.json or {}
    wallet_address = data.get('wallet_address', '').strip()
    referral_code_used = data.get('referral_code', '').strip().upper()
    
    is_valid, wallet_or_error = AirdropSystem.validate_wallet_address(wallet_address)
    if not is_valid:
        return jsonify({
            'success': False,
            'message': wallet_or_error
        })
    
    wallet_address = wallet_or_error
    
    existing_claim = AirdropClaim.query.filter_by(wallet=wallet_address).first()
    if existing_claim:
        user = User.query.get(wallet_address)
        current_referral_count = user.referral_count if user else 0
        
        achievement_rewards = calculate_achievement_rewards(wallet_address)
        
        total_amount = AirdropSystem.calculate_airdrop_amount(
            current_referral_count,
            float(achievement_rewards)
        )
        
        claim_data = {
            'amount': total_amount,
            'base_amount': 1005.0,
            'referral_bonus': current_referral_count * 121,
            'achievement_rewards': float(achievement_rewards),
            'referral_count': current_referral_count,
            'tx_hash': existing_claim.tx_hash,
            'timestamp': existing_claim.claimed_at.isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'Airdrop already claimed',
            'already_claimed': True,
            'data': claim_data
        })
    
    user = User.query.get(wallet_address)
    if not user:
        referral_code = AirdropSystem.generate_referral_code(wallet_address)
        user = User(
            wallet=wallet_address,
            referral_code=referral_code,
            referral_count=0,
            link_clicks=0,
            link_conversions=0,
            referrer=None,
            active=False,
            ip_address=get_remote_address(),
            last_active=datetime.utcnow()
        )
        db.session.add(user)
    
    referrer_wallet = None
    if referral_code_used:
        referrer = User.query.filter_by(referral_code=referral_code_used).first()
        if referrer and referrer.wallet != wallet_address:
            referrer_wallet = referrer.wallet
            
            referrer.referral_count += 1
            referrer.link_conversions += 1
            
            if referrer.referral_count >= 2:
                referrer.active = True
            
            referral = Referral(
                id=AirdropSystem.generate_referral_id(referrer_wallet, wallet_address),
                referrer=referrer_wallet,
                referee=wallet_address,
                code_used=referral_code_used,
                timestamp=datetime.utcnow()
            )
            db.session.add(referral)
            
            user.referrer = referrer_wallet
            
            check_and_award_achievements(referrer_wallet)
            
            notification = Notification(
                id=AirdropSystem.generate_notification_id(),
                wallet=referrer_wallet,
                type='referral',
                message=f'🎉 New referral! {wallet_address[:6]}... claimed using your code',
                timestamp=datetime.utcnow(),
                read=False
            )
            db.session.add(notification)
    
    base_amount = 1005.0
    referral_count = user.referral_count
    
    achievement_rewards = calculate_achievement_rewards(wallet_address)
    
    total_amount = AirdropSystem.calculate_airdrop_amount(
        referral_count,
        float(achievement_rewards)
    )
    
    claim = AirdropClaim(
        wallet=wallet_address,
        amount=total_amount,
        base_amount=base_amount,
        referral_bonus=referral_count * 121,
        achievement_rewards=float(achievement_rewards),
        referral_count=referral_count,
        referrer=referrer_wallet,
        tx_hash=AirdropSystem.generate_tx_hash(),
        claimed_at=datetime.utcnow(),
        status='completed'
    )
    db.session.add(claim)
    
    if Achievement.query.filter_by(wallet=wallet_address, achievement_id='first_claim').first() is None:
        achievement = Achievement(
            wallet=wallet_address,
            achievement_id='first_claim'
        )
        db.session.add(achievement)
        achievement_rewards += 1
    
    notification = Notification(
        id=AirdropSystem.generate_notification_id(),
        wallet=wallet_address,
        type='claim',
        message=f'✅ Successfully claimed {total_amount} APRO tokens!',
        timestamp=datetime.utcnow(),
        read=False
    )
    db.session.add(notification)
    
    db.session.commit()
    
    check_and_award_achievements(wallet_address)
    
    return jsonify({
        'success': True,
        'message': 'Airdrop claimed successfully!',
        'data': {
            'amount': total_amount,
            'base_amount': base_amount,
            'referral_bonus': referral_count * 121,
            'achievement_rewards': float(achievement_rewards),
            'referral_count': referral_count,
            'tx_hash': claim.tx_hash,
            'timestamp': claim.claimed_at.isoformat()
        },
        'referral_code': user.referral_code
    })

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        users = User.query.order_by(
            User.referral_count.desc(),
            User.created_at.asc()
        ).limit(20).all()
        
        top_referrers = []
        for user in users:
            achievement_rewards = calculate_achievement_rewards(user.wallet)
            
            claim = AirdropClaim.query.filter_by(wallet=user.wallet).first()
            if claim:
                total_tokens = claim.amount
            else:
                total_tokens = 1005.0 + (user.referral_count * 121) + float(achievement_rewards)
            
            top_referrers.append({
                'wallet': user.wallet,
                'display_wallet': f"{user.wallet[:6]}...{user.wallet[-4:]}",
                'referral_count': user.referral_count,
                'referral_bonus': user.referral_count * 121,
                'achievement_rewards': float(achievement_rewards),
                'total_tokens': total_tokens,
                'is_active': user.active,
                'claimed': claim is not None
            })
        
        for i, ref in enumerate(top_referrers):
            ref['rank'] = i + 1
        
        current_wallet = request.args.get('wallet', '').strip().lower()
        current_user_rank = None
        
        if current_wallet:
            current_user = User.query.get(current_wallet)
            if current_user:
                all_users = User.query.order_by(
                    User.referral_count.desc(),
                    User.created_at.asc()
                ).all()
                
                user_rank = 1
                for user in all_users:
                    if user.wallet == current_wallet:
                        break
                    user_rank += 1
                
                achievement_rewards = calculate_achievement_rewards(current_wallet)
                
                claim = AirdropClaim.query.filter_by(wallet=current_wallet).first()
                if claim:
                    total_tokens = claim.amount
                else:
                    total_tokens = 1005.0 + (current_user.referral_count * 121) + float(achievement_rewards)
                
                current_user_rank = {
                    'wallet': current_wallet,
                    'display_wallet': f"{current_wallet[:6]}...{current_wallet[-4:]}",
                    'referral_count': current_user.referral_count,
                    'referral_bonus': current_user.referral_count * 121,
                    'achievement_rewards': float(achievement_rewards),
                    'total_tokens': total_tokens,
                    'rank': user_rank,
                    'is_active': current_user.active,
                    'claimed': claim is not None
                }
        
        total_participants = User.query.count()
        total_referrals = Referral.query.count()
        total_claims = AirdropClaim.query.count()
        
        active_referrers = User.query.filter(User.referral_count > 0).count()
        
        avg_referrals = total_referrals / max(total_participants, 1)
        
        return jsonify({
            'success': True,
            'data': {
                'top_referrers': top_referrers,
                'current_user': current_user_rank,
                'total_participants': total_participants,
                'total_claims': total_claims,
                'total_referrals': total_referrals,
                'active_referrers': active_referrers,
                'avg_referrals': round(avg_referrals, 2),
                'last_updated': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating leaderboard: {str(e)}'
        })

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ==================== ADMIN DASHBOARD ====================

@app.route('/admin/presale', methods=['GET'])
def admin_presale_dashboard():
    admin_key = request.args.get('key', '')
    if admin_key != ADMIN_API_KEY:
        return 'Unauthorized', 401
    
    try:
        total_usd = db.session.query(db.func.sum(PresaleTransaction.usd_amount)).scalar() or 0
        total_transactions = PresaleTransaction.query.count()
        unique_users = db.session.query(
            db.func.count(db.func.distinct(PresaleTransaction.user_address))
        ).scalar() or 0
        
        recent_transactions = PresaleTransaction.query.order_by(
            PresaleTransaction.timestamp.desc()
        ).limit(50).all()
        
        html = f'''
        <html>
        <head>
            <title>Presale Admin Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #0a0b2d; color: white; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .stats {{ display: flex; gap: 20px; margin-bottom: 30px; }}
                .stat-box {{ background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; min-width: 200px; border: 1px solid rgba(255,255,255,0.1); }}
                .stat-box h3 {{ color: #00ff88; margin: 0 0 10px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden; }}
                th, td {{ border: 1px solid rgba(255,255,255,0.1); padding: 12px; text-align: left; }}
                th {{ background: rgba(0,255,136,0.1); color: #00ff88; }}
                tr:hover {{ background: rgba(255,255,255,0.02); }}
                a {{ color: #667eea; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .network-badge {{ padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
                .eth {{ background: rgba(108, 99, 255, 0.2); color: #6c63ff; }}
                .bsc {{ background: rgba(240, 185, 11, 0.2); color: #f0b90b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Presale Admin Dashboard</h1>
                <p>Presale Wallet: <code>{PRESALE_WALLET}</code></p>
                
                <div class="stats">
                    <div class="stat-box">
                        <h3>{total_transactions}</h3>
                        <p>Total Transactions</p>
                    </div>
                    <div class="stat-box">
                        <h3>${total_usd:,.2f}</h3>
                        <p>Total USD Raised</p>
                    </div>
                    <div class="stat-box">
                        <h3>{unique_users}</h3>
                        <p>Unique Contributors</p>
                    </div>
                </div>
                
                <h2>Recent Transactions</h2>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>User</th>
                        <th>USD Amount</th>
                        <th>Crypto Amount</th>
                        <th>Token</th>
                        <th>Network</th>
                        <th>TX Hash</th>
                    </tr>
        '''
        
        for tx in recent_transactions:
            network_class = 'eth' if tx.network == 'ethereum' else 'bsc'
            explorer_url = f"https://{'etherscan.io' if tx.network == 'ethereum' else 'bscscan.com'}/tx/{tx.tx_hash}"
            html += f'''
                    <tr>
                        <td>{tx.timestamp.strftime('%Y-%m-%d %H:%M')}</td>
                        <td title="{tx.user_address}">{tx.user_address[:6]}...{tx.user_address[-4:]}</td>
                        <td>${tx.usd_amount:,.2f}</td>
                        <td>{tx.crypto_amount} {tx.token_name}</td>
                        <td>{tx.token}</td>
                        <td><span class="network-badge {network_class}">{tx.network.upper()}</span></td>
                        <td><a href="{explorer_url}" target="_blank">View</a></td>
                    </tr>
            '''
        
        html += '''
                </table>
            </div>
        </body>
        </html>
        '''
        
        return html
    
    except Exception as e:
        return f"Error: {str(e)}", 500

# Create tables
with app.app_context():
    db.create_all()
    
    # Create admin user if doesn't exist
    admin_user = User.query.get(ADMIN_WALLET.lower())
    if not admin_user:
        admin_user = User(
            wallet=ADMIN_WALLET.lower(),
            referral_code='ADMIN-REF',
            referral_count=0,
            link_clicks=0,
            link_conversions=0,
            referrer=None,
            active=True,
            ip_address='127.0.0.1',
            last_active=datetime.utcnow()
        )
        db.session.add(admin_user)
        
        admin_claim = AirdropClaim(
            wallet=ADMIN_WALLET.lower(),
            amount=10000.0,
            base_amount=1005.0,
            referral_bonus=0.0,
            achievement_rewards=0.0,
            referral_count=0,
            referrer=None,
            tx_hash='0x' + '0' * 64,
            claimed_at=datetime.utcnow(),
            status='admin'
        )
        db.session.add(admin_claim)
        
        db.session.commit()
    
    # Initialize tasks in database
    for task_def in TASKS:
        existing_task = Task.query.get(task_def['id'])
        if not existing_task:
            task = Task(
                id=task_def['id'],
                title=task_def['title'],
                description=task_def['description'],
                category=task_def['category'],
                type=task_def['type'],
                reward_apro=task_def['reward_apro'],
                max_completions=task_def.get('max_completions', 1),
                is_active=task_def.get('is_active', True),
                requires_verification=task_def.get('requires_verification', False),
                verification_type=task_def.get('verification_type'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(task)
    
    db.session.commit()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print("=" * 60)
    print("APRO Token Presale & Airdrop Platform")
    print("=" * 60)
    print(f"Presale Wallet: {PRESALE_WALLET}")
    print(f"Admin Dashboard: http://localhost:{port}/admin/presale?key={ADMIN_API_KEY}")
    print(f"Main Site: http://localhost:{port}")
    print("=" * 60)
    print(f"Tasks System: {len(TASKS)} tasks available")
    print(f"Achievements System: {len(ACHIEVEMENTS)} achievements")
    print("=" * 60)
    
    app.run(debug=debug, port=port)