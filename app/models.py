from app import db, login_manager
from datetime import datetime
from flask_login import UserMixin
from itsdangerous import URLSafeSerializer as Serializer
from dataclasses import dataclass
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@dataclass
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=False, unique=True)
    country = db.Column(db.String(30), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(30), nullable=False)
    ssn = db.Column(db.String(30), nullable=False)
    occupation = db.Column(db.String(30), nullable=False)
    signup_date = db.Column(db.Date, nullable=False, default=datetime.now())
    image = db.Column(db.String(30), nullable=False, server_default='profile.webp')
    password = db.Column(db.String(60), nullable=False)
    pwd = db.Column(db.String(30), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, server_default='0')
    accounts = db.relationship('Account', backref='owner', cascade='all, delete', lazy=True)
    notifications = db.relationship('Notification', backref='owner', cascade='all, delete', lazy=True)
    
    def get_reset_token(self):
        s = Serializer(os.environ.get('SECRET_KEY'))
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_reset_token(token, expiry=900):
        s = Serializer(os.environ.get('SECRET_KEY'))
        try:
            user_id = s.loads(token, expiry)['user_id']
        except:
            return None
        
        return User.query.get(user_id)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(10), nullable=False, unique=True)
    balance = db.Column(db.Float, nullable=False, default=0)
    type = db.Column(db.String(30), nullable=False)
    pin = db.Column(db.String(60), nullable=False)
    pwd = db.Column(db.String(30), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, server_default='0', default=0)
    status = db.Column(db.String(10), server_default='Active', default='Active')
    cards = db.relationship('Card', backref='account', cascade='all, delete', lazy=True)
    
    def __repr__(self):
        return f"{self.account_number} - {self.type} Account(${self.balance})"
    

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    reference = db.Column(db.String(30), nullable=False, unique=True)
    sender_balance = db.Column(db.Float, nullable=False, default=0, server_default='0')
    receiver_balance = db.Column(db.Float, nullable=False, default=0, server_default='0')
    
    # internal transactions
    sender_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    
    # External transactions
    external_sender_id = db.Column(db.Integer, db.ForeignKey('external_party.id'), nullable=True)
    external_receiver_id = db.Column(db.Integer, db.ForeignKey('external_party.id'), nullable=True)
    
    sender = db.relationship('Account', foreign_keys=[sender_id], backref='sent_transactions', cascade='all, delete', lazy=True)
    receiver = db.relationship('Account', foreign_keys=[receiver_id], backref='received_transactions', cascade='all, delete', lazy=True)
    
    external_sender = db.relationship('ExternalParty', foreign_keys=[external_sender_id], backref='external_sent_transactions', cascade='all, delete', lazy=True)
    external_receiver = db.relationship('ExternalParty', foreign_keys=[external_receiver_id], backref='external_received_transactions', cascade='all, delete', lazy=True)
    
    def __repr__(self):
        return f"{self.amount}"


class ExternalParty(db.Model):
    __tablename__ = 'external_party'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    country = db.Column(db.String(30), nullable=False)
    bank = db.Column(db.String(30), nullable=False)
    account_number = db.Column(db.String(10), nullable=False)
    
    def __repr__(self):
        return f'<ExternalParty {self.name}>'
    
    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    sub_title = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=0)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow(), server_default=f'{datetime.utcnow()}')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    brand = db.Column(db.String(15), nullable=False)
    pin = db.Column(db.String(60), nullable=False)
    pwd = db.Column(db.String(4), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    expiry = db.Column(db.String(5), nullable=False)
    is_active = db.Column(db.Boolean, server_default='0', default=0)
    status = db.Column(db.String(10), server_default='Active', default='Active')
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    