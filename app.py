import os
import stripe
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required

from config import Config
from extensions import db, login_manager, migrate, mail
from forms import (
    LoginForm, RegistrationForm, CampaignForm,
    MessageForm
)
from models import (
    User, Profile, Subscription, Campaign, Collaboration,
    Deliverable, Payment, Message, Influencer
)

from data_manager import DataManager, recommend_influencers

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions properly
db.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)

# Initialize LoginManager and set login view
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

data_manager = DataManager(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port= os.getenv("DB_PORT")
    )

# Initialize Stripe with secret key
stripe.api_key = app.config.get('STRIPE_SECRET_KEY')

@app.template_filter('float_format')
def float_format_filter(value, format_str='%.2f', skip_none=False):
    if skip_none and (value is None or value == ''):
        return ''
    try:
        return format_str % float(value)
    except (ValueError, TypeError):
        return value

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='influencer' if form.account_type.data == 'influencer' else 'user'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Create profile if influencer
        if form.account_type.data == 'influencer':
            profile = Profile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()

        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    # Get the user profile data
    user = User.query.filter_by(username=username).first_or_404()
    profile = Profile.query.filter_by(user_id=user.id).first()
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    
    # Get campaigns created by this user (if they're a brand)
    campaigns = Campaign.query.filter_by(creator_id=user.id).order_by(Campaign.created_at.desc()).limit(5).all()
    
    # Get collaborations (if they're an influencer)
    collaborations = Collaboration.query.filter_by(influencer_id=user.id).order_by(Collaboration.created_at.desc()).limit(5).all()
    
    # Get stats for influencers
    if user.is_influencer():
        completed_collabs = Collaboration.query.filter_by(
            influencer_id=user.id, 
            status='completed'
        ).count()
        
        total_earnings = db.session.query(
            db.func.sum(Payment.amount)
            .filter(
                Payment.collaboration_id == Collaboration.id,
                Collaboration.influencer_id == user.id,
                Payment.status == 'paid'
            ).scalar() or 0)
    else:
        completed_collabs = None
        total_earnings = None
    
    return render_template(
        'profile.html',
        user=user,
        profile=profile,
        subscription=subscription,
        campaigns=campaigns,
        collaborations=collaborations,
        completed_collabs=completed_collabs,
        total_earnings=total_earnings
    )

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    pass

@app.route('/dashboard')
@login_required
def dashboard():
    with DataManager(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port= os.getenv("DB_PORT")
    ) as dm:
        all_influencers = dm.get_all_influencers(limit=100)
        for influencer in all_influencers:
            influencer_data = dm.get_influencer_data_points(influencer['id'])
            influencer['data_points'] = influencer_data
        return render_template('influencers.html', influencers=all_influencers)

@app.route("/influencers")   # LIST Influencers
@login_required
def browse_influencers():
    with DataManager(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port= os.getenv("DB_PORT")
    ) as dm:
        all_influencers = dm.get_all_influencers(limit=100)
        for influencer in all_influencers:
            influencer_data = dm.get_influencer_data_points(influencer['id'])
            influencer['data_points'] = influencer_data
        return render_template('influencers.html', influencers=all_influencers)

@app.route('/influencer/<int:influencer_id>')    # VIEW Influencer Profile TODO
@login_required
def influencer_profile(influencer_id):
    influencer = Influencer.query.get_or_404(influencer_id)

    profile = Profile.query.filter_by(user_id=influencer_id).first()
    return render_template('influencers/profile.html', influencer=influencer, profile=profile)

@app.route('/campaigns')    # LIST Campaigns
@login_required
def list_campaigns():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if current_user.role == 'influencer':
        collaborations = Collaboration.query.filter_by(influencer_id=current_user.id).all()
        campaign_ids = [c.campaign_id for c in collaborations]
        campaigns_pagination = Campaign.query.filter(Campaign.id.in_(campaign_ids)).order_by(Campaign.created_at.desc()).paginate(page=page, per_page=per_page)
    else:
        campaigns_pagination = Campaign.query.filter_by(creator_id=current_user.id).order_by(Campaign.created_at.desc()).paginate(page=page, per_page=per_page)

    # Manually add computed fields if necessary
    for campaign in campaigns_pagination.items:
        campaign.influencer_count = len(campaign.collaborations)
        campaign.brand = current_user.company_name if hasattr(current_user, 'company_name') else "N/A"

    return render_template('campaigns/list.html', campaigns=campaigns_pagination)

@app.route('/campaigns/<int:campaign_id>/view')    # VIEW Campaign
@login_required
def view_campaign(campaign_id):
    campaigns = Campaign.query.filter_by(creator_id=current_user.id).order_by(Campaign.created_at.desc()).limit(5).all()
    collaborations = Collaboration.query.filter_by(influencer_id=current_user.id).order_by(Collaboration.created_at.desc()).limit(5).all()
    # Get AI recommendations
    recommended_influencers = recommend_influencers()
    # Calculate stats
    active_campaigns = Campaign.query.filter_by(creator_id=current_user.id, status='active').count()
    total_influencers = Collaboration.query.filter(Collaboration.campaign_id.in_(
        [c.id for c in Campaign.query.filter_by(creator_id=current_user.id).all()]
    )).count()
    campaign = Campaign.query.get_or_404(campaign_id)

    return render_template('campaigns/view.html',
                            campaign=campaign,
                           
                           recommended_influencers=recommended_influencers,
                           campaigns=campaigns,
                           collaborations=collaborations,
                           active_campaigns=active_campaigns,
                           total_influencers=total_influencers)

@app.route('/campaign/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if current_user.role == 'influencer':
        flash('Influencers cannot create campaigns', 'warning')
        return redirect(url_for('dashboard'))

    form = CampaignForm()
    if form.validate_on_submit():
        campaign = Campaign(
            title=form.title.data,
            description=form.description.data,
            creator_id=current_user.id,
            budget=form.budget.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            requirements=form.requirements.data,
            target_audience={
                'gender': form.target_gender.data,
                'age_min': form.target_age_min.data,
                'age_max': form.target_age_max.data,
                'location': form.target_location.data
            }
        )
        db.session.add(campaign)
        db.session.commit()
        flash('Your campaign has been created!', 'success')
        return redirect(url_for('view_campaign', campaign_id=campaign.id))
    return render_template('campaigns/create.html', form=form)

@app.route('/collaboration/<int:collaboration_id>')
@login_required
def view_collaboration(collaboration_id):
    collaboration = Collaboration.query.get_or_404(collaboration_id)

    if current_user.id not in [collaboration.campaign.creator_id, collaboration.influencer_id]:
        flash('You do not have access to this collaboration', 'danger')
        return redirect(url_for('dashboard'))

    deliverables = Deliverable.query.filter_by(collaboration_id=collaboration_id).all()
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == collaboration.influencer_id)) |
        ((Message.sender_id == collaboration.influencer_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()

    form = MessageForm()
    return render_template('collaboration/view.html',
                           collaboration=collaboration,
                           deliverables=deliverables,
                           messages=messages,
                           form=form)

@app.route('/send_message/<int:recipient_id>', methods=['POST'])
@login_required
def send_message(recipient_id):
    recipient = User.query.get_or_404(recipient_id)
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            body=form.message.data
        )
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent.', 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/pricing')
def pricing():
    return render_template('payments/plans.html', plans=app.config.get('PRICING_PLANS', {}))

@app.route('/checkout/<plan>/<period>', methods=['GET', 'POST'])
@login_required
def checkout(plan, period):
    pass

@app.route('/payment/<plan_id>')
def payment(plan_id):
   pass

@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    pass

@app.route('/payment/success')
def payment_success():
    pass

def get_stripe_price_id(plan_id):
    pass

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    pass

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True) 