from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user_login'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False, unique=True)

    # Reverse relationship to UserProfile, using the user_id as the foreign key
    profile = db.relationship('UserProfile', back_populates='user', uselist=False)

    @property
    def full_names(self):
        return self.profile.full_names if self.profile else None

    @property
    def phone_no(self):
        return self.profile.phone_no if self.profile else None

    @property
    def country(self):
        return self.profile.country if self.profile else None

    @property
    def location(self):
        return self.profile.location if self.profile else None
    

    def __repr__(self):
        return f"<User {self.username}, email {self.email}>"
    

class UserProfile(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_names = db.Column(db.String(100), nullable=False)
    monthly_income = db.Column(db.String(100), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    business_level = db.Column(db.String(100), nullable=False)
    profile_pic = db.Column(db.String(100), nullable=False, unique=False, default="default.jpg")
    phone_no = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)

    # Foreign key referencing the 'id' from the User table
    user_id = db.Column(db.Integer, db.ForeignKey('user_login.id'), nullable=False, unique=True)
    
    # Relationship to the User table using the user_id
    user = db.relationship('User', back_populates='profile')

    def __repr__(self):
        return f"<UserProfile {self.full_names}, user_id {self.user_id}>"

class PeerToPeerAdvice(db.Model):
    __tablename__ = 'peer_to_peer_advice'
    
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f"<Message from {self.username}>"

class LoanApplication(db.Model):
    __tablename__ = 'loan_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), default='Pending')
    submitted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f"<LoanApplication {self.id}>"