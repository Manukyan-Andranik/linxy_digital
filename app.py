import os
from datetime import timedelta

from flask_cors import CORS, cross_origin
from flask import Flask, render_template, request, jsonify
from flask_jwt_extended import (
    JWTManager, get_jwt, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from log import Logger
from datamanager import DataManager
from models import Users, Influencers, Company, db, TokenBlacklist
from utils import ResponseHandler, DEFAULT_COMPANY_URL

load_dotenv()

# Logger setup
logger = Logger.load_logger(__name__)

# Initialize Flask app
app = Flask(__name__)

# DB & JWT Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///linxy_app_last.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Init Extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app)
DATA_MANAGER = DataManager(db, Users, Influencers, Company)

# Create tables
with app.app_context():
    db.create_all()

# JWT Blocklist
@jwt.token_in_blocklist_loader
def is_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return db.session.query(TokenBlacklist.id).filter_by(jti=jti).first() is not None

@app.route('/')
def home():
    chart_data = DATA_MANAGER.get_charts_data()
    
    return jsonify(ResponseHandler.success("Welcome to DevHacks", {
        "data": chart_data
    }))

# --------- Auth Routes ---------
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    try:
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form['role']
        phone = request.form['phone']
        photo = request.files.get('photo')

        photo_url = DataManager.upload_image_to_cloudinary(photo) if photo else None
        hashed_password = generate_password_hash(password)

        user = Users(email=email, password=hashed_password, full_name=full_name,
                     photo_url=photo_url, role=role, phone=phone)
        user.save()

        return jsonify(ResponseHandler.success("User created successfully")), 200
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        return jsonify(ResponseHandler.error("Signup failed")), 500

@app.route('/signin', methods=['POST', 'GET'])
@cross_origin(supports_credentials=True)
def signin():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify(ResponseHandler.error("Email and password are required")), 400

        user_response = DATA_MANAGER.get_user_by_email(email)
        if not user_response or not user_response.get("message"):
            return jsonify(ResponseHandler.unauthorized("Invalid credentials")), 401

        user = user_response["message"]

        if not check_password_hash(user.password, password):
            return jsonify(ResponseHandler.unauthorized("Invalid credentials")), 401

        user_id = str(user.id)
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)

        return jsonify(ResponseHandler.success("Signed in successfully", {
            'access_token': access_token,
            'refresh_token': refresh_token
        })), 200
    except Exception as e:
        logger.error(f"Signin failed: {e}")
        return jsonify(ResponseHandler.error("Signin failed")), 500

@app.route('/refresh', methods=['POST', 'GET'])
@jwt_required(refresh=True)
def refresh_token():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify(ResponseHandler.success("Token refreshed", {'access_token': access_token})), 200

@app.route('/logout', methods=['POST', 'GET'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    user_id = get_jwt_identity()
    blacklisted_token = TokenBlacklist(jti=jti, user_id=user_id, reason="logout")
    db.session.add(blacklisted_token)
    db.session.commit()
    return jsonify(ResponseHandler.success("Successfully logged out")), 200

# --------- Protected Route Example ---------
@app.route('/profile', methods=['POST', 'GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = Users.query.get(user_id)

    if not user:
        return jsonify(ResponseHandler.error("User not found")), 404

    profile_data = {
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "photo_url": user.photo_url,
        "email": user.email,
        "role": user.role,
    }

    if user.role == 'company_admin':
        companies = Company.query.filter_by(user_id=user.id).all()
        profile_data['companies'] = [
            {
                "id": c.id,
                "sphere": c.sphere,
                "description": c.description,
                "linkdin": c.linkdin,
                "instagram": c.instagram,
                "facebook": c.facebook,
                "location": c.location,
            } for c in companies
        ]
    elif user.role == 'influencer':
        price_list = Influencers.query.filter_by(user_id=user.id).all()
        profile_data['price_list'] = [
            {
                "id": p.id,
                "social_net": p.social_net,
                "link": p.link,
                "price_stories": str(p.price_stories),
                "story_with_travel_to_location": str(p.story_with_travel_to_location),
                "subs": p.subs,
                "engagement_rate": str(p.engagement_rate),
            } for p in price_list
        ]

    return jsonify(ResponseHandler.success("Profile fetched", profile_data)), 200

@app.route('/create_company', methods=['POST', 'GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def create_company():
    user_id = get_jwt_identity()
    user = DATA_MANAGER.get_user_by_id(user_id)
    if not user or user["message"].role != 'company_admin':
        return jsonify(ResponseHandler.error("Unauthorized or invalid role")), 403

    logo = request.files.get('logo')
    print(logo)
    
    if not logo:
        return jsonify(ResponseHandler.error("Logo is required")), 400

    # try:
    logo_img = request.files.get('logo')
            # Optional: Cloudinary setup (replace with actual)
    if logo_img:
        # Replace this with your actual Cloudinary call
        logo_url = DataManager.upload_image_to_cloudinary(logo_img, folder='company_logos')
    else:
        logo_url = DEFAULT_COMPANY_URL
    print(request.form)
    company = Company(
        logo_url=logo_url,
        user_id=user_id,
        sphere=request.form['sphere'],
        description=request.form['description'],
        linkdin=request.form['linkdin'],
        instagram=request.form['instagram'],
        facebook=request.form['facebook'],
        location=request.form['location'],
        title=request.form['title']
    )
    company.save()
    return jsonify(ResponseHandler.success("Company created", {"company_id": company.id})), 201

    # except Exception as e:
    #     logger.error(f"Company creation failed: {e}")
    #     return jsonify(ResponseHandler.error("Company creation failed")), 500

@app.route('/companyes', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_company():
    user_id = get_jwt_identity()
    user = DATA_MANAGER.get_user_by_id(user_id)

    if not user:
        return jsonify(ResponseHandler.error("User not found")), 404

    companyes = DATA_MANAGER.get_companyes_by_user_id(user_id)["message"]
    print(companyes)
    if not companyes:
        return jsonify(ResponseHandler.error("Company not found")), 404

    # Convert each company to dictionary
    companyes_data = [company.to_dict() for company in companyes]

    return jsonify(ResponseHandler.success("Company fetched", data=companyes_data)), 200

# _____________ INFLUENCER ROUTES ____________
@app.route('/influencers', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_influencers():
    # res = DATA_MANAGER.upload_influencers()
    # print(res)
    user_id = get_jwt_identity()
    user = DATA_MANAGER.get_user_by_id(user_id)

    if not user:
        return jsonify(ResponseHandler.error("User not found")), 404

    influencers = DATA_MANAGER.get_influencers()["message"]
    if not influencers:
        return jsonify(ResponseHandler.error("Influencer not found")), 404

    influencers_data = [influencers for influencers in influencers] 


    return jsonify(ResponseHandler.success("Influencers fetched", data=influencers_data)), 200
    # Convert each influencer to dictionary

@app.route('/company/<int:company_id>/influencers', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_influencers_by_company(company_id):
    user_id = get_jwt_identity()
    user = DATA_MANAGER.get_user_by_id(user_id)

    if not user:
        return jsonify(ResponseHandler.error("User not found")), 404

    company = DATA_MANAGER.get_companyes_by_company_id(company_id, user_id)

    if not company:
        return jsonify(ResponseHandler.error("Company not found")), 404

    influencers_data = DATA_MANAGER.get_influencers()["message"]

    recomendations = DATA_MANAGER.AI_MODEL.get_best_5(company, influencers_data)

    print(recomendations)
    return jsonify(ResponseHandler.success("Influencers fetched", data=recomendations)), 200

# --------- Example Refresh Protected Route ---------
@app.route('/protected', methods=['POST', 'GET'])
@jwt_required()
def protected():
    return jsonify(ResponseHandler.success("Access granted", {'user_id': get_jwt_identity()})), 200

# Run App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
