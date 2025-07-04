from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class TokenBlacklist(db.Model):
    __tablename__ = 'token_blacklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(128), nullable=True)

    def __repr__(self):
        return f"<TokenBlacklist jti={self.jti}>"


class BaseModel(db.Model):
    __abstract__ = True

    def save(self):
        db.session.add(self)
        db.session.commit()




class Users(BaseModel):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    photo_url = db.Column(db.String(1020), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(1020), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "photo_url": self.photo_url,
            "email": self.email,
            "role": self.role,
        }

class Influencers(BaseModel):
    __tablename__ = 'influencers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    social_net = db.Column(db.String(50))
    link = db.Column(db.String(1020))
    price_stories = db.Column(db.Numeric(10, 2))
    story_with_travel_to_location = db.Column(db.Numeric(10, 2))
    price_reels_creative = db.Column(db.Numeric(10, 2))
    price_photo_post = db.Column(db.Numeric(10, 2))
    collaboration = db.Column(db.Numeric(10, 2))
    category = db.Column(db.String(50))
    subs = db.Column(db.Integer)
    avg_view_reels = db.Column(db.Integer)
    cpv_reels_creative = db.Column(db.Numeric(5, 2))
    engagement_rate = db.Column(db.Numeric(3, 2))
    men = db.Column(db.Numeric(3, 2))
    women = db.Column(db.Numeric(3, 2))
    age13_17 = db.Column(db.Numeric(3, 2))
    age18_24 = db.Column(db.Numeric(3, 2))
    age25_34 = db.Column(db.Numeric(3, 2))
    age35_44 = db.Column(db.Numeric(3, 2))
    armenia = db.Column(db.Numeric(3, 2))
    russia = db.Column(db.Numeric(3, 2))
    georgia = db.Column(db.Numeric(3, 2))
    usa = db.Column(db.Numeric(3, 2))
    yerevan = db.Column(db.Numeric(3, 2))
    gyumri = db.Column(db.Numeric(3, 2))
    vanadzor = db.Column(db.Numeric(3, 2))
    moscow = db.Column(db.Numeric(3, 2))

    user = db.relationship('Users', backref=db.backref('influencer_prices', cascade='all, delete'))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "social_net": self.social_net,
            "link": self.link,
            "price_stories": self.price_stories,
            "story_with_travel_to_location": self.story_with_travel_to_location,
            "price_reels_creative": self.price_reels_creative,
            "price_photo_post": self.price_photo_post,
            "collaboration": self.collaboration,
            "category": self.category,
            "subs": self.subs,
            "avg_view_reels": self.avg_view_reels,
            "cpv_reels_creative": self.cpv_reels_creative,
            "engagement_rate": self.engagement_rate,
            "men": self.men,
            "women": self.women,
            "age13_17": self.age13_17,
            "age18_24": self.age18_24,
            "age25_34": self.age25_34,
            "age35_44": self.age35_44,
            "armenia": self.armenia,
            "russia": self.russia,
            "georgia": self.georgia,
            "usa": self.usa,
            "yerevan": self.yerevan,
            "gyumri": self.gyumri,
            "vanadzor": self.vanadzor,
            "moscow": self.moscow,
        }   


class Company(BaseModel):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(50), nullable=False)
    logo_url = db.Column(db.String(1020), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Company identity
    sphere = db.Column(db.String(50))              # e.g., 'Fashion', 'Tech', 'Travel'
    description = db.Column(db.Text)               # Rich text about company goals, tone, brand
    location = db.Column(db.String(500))           # Main target market (used for influencer location match)

    # Social links
    linkdin = db.Column(db.String(500))
    instagram = db.Column(db.String(500))
    facebook = db.Column(db.String(500))

    # 👇 New: Matching preferences
    target_category = db.Column(db.String(50))     # e.g., 'lifestyle', 'tech', 'food'
    target_gender = db.Column(db.String(10))       # 'men', 'women', 'any'
    target_age_min = db.Column(db.Integer)         # e.g., 18
    target_age_max = db.Column(db.Integer)         # e.g., 35
    min_engagement_rate = db.Column(db.Float)      # e.g., 0.25
    min_avg_views = db.Column(db.Integer)          # e.g., 10000
    max_price = db.Column(db.Float)                # optional budget cap

    # Relationships
    user = db.relationship('Users', backref=db.backref('companies', cascade='all, delete'))


    def to_dict(self):
            return {
                "id": self.id,
                "title": self.title,
                "logo_url": self.logo_url,
                "user_id": self.user_id,
                "sphere": self.sphere,
                "description": self.description,
                "linkdin": self.linkdin,
                "instagram": self.instagram,
                "facebook": self.facebook,
                "location": self.location,
            }
