import os
import re
import json
import dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from ai import AiModel  

# Load .env variables
dotenv.load_dotenv()

class DataManager:
    def __init__(self, db, Users, Influencers=None, Company=None, ai_name='model.pkl'):
        cloudinary.config(
            cloud_name=os.environ.get('CLOUD_NAME'),
            api_key=os.environ.get('API_KEY'),
            api_secret=os.environ.get('API_SECRET')
        )

        self.db = db
        self.Users = Users
        self.Company = Company
        self.Influencers = Influencers
        self.AI_MODEL = AiModel().load(ai_name)
        
    def get_user_by_email(self, email):
        """
        Fetch a user from the database by email.

        Returns:
            dict: {
                "status": "success",
                "message": user_object
            }
            or
            {
                "status": "error",
                "error_reason": "User not found"
            }
        """
        try:
            user = self.Users.query.filter_by(email=email).first()
            if user:
                return {
                    "status": "success",
                    "message": user
                }
            else:
                return {
                    "status": "error",
                    "error_reason": "User not found"
                }
        except SQLAlchemyError as e:
            return {
                "status": "error",
                "error_reason": str(e)
            }

    def get_user_by_id(self, id):    
        try:
            user = self.Users.query.filter_by(id=id).first()
            if user:
                return {
                    "status": "success",
                    "message": user
                }
            else:
                return {
                    "status": "error",
                    "error_reason": "User not found"
                }
        except SQLAlchemyError as e:
            return {
                "status": "error",
                "error_reason": str(e)
            }

    def get_companyes_by_user_id(self, user_id):
        try:
            company = self.Company.query.filter_by(id=user_id)
            if company:
                return {
                    "status": "success",
                    "message": list(company)
                }
            else:
                return {
                    "status": "error",
                    "error_reason": "Company not found"
                }
        except SQLAlchemyError as e:
            return {
                "status": "error",
                "error_reason": str(e)
            }

    def get_companyes_by_company_id(self, company_id, user_id):
        try:
            company = self.Company.query.filter_by(id=company_id).first()
            if not company:
                return {
                    "status": "error",
                    "error_reason": "Company not found"
                }

            if company.user_id != user_id:
                return {
                    "status": "error",
                    "error_reason": "Unauthorized access. This company does not belong to the user."
                }

            return {
                "status": "success",
                "message": company.to_dict() if hasattr(company, 'to_dict') else {
                    "id": company.id,
                    "name": company.name if hasattr(company, "name") else "",
                    "user_id": company.user_id
                }
            }

        except SQLAlchemyError as e:
            return {
                "status": "error",
                "error_reason": str(e)
            }


    def get_influencer_by_id(self, influencer_id):
        try:
            influencer = self.Influencers.query.filter_by(id=influencer_id).first()
            if influencer:
                user = influencer.user  # Access the linked user
                return {
                    "status": "success",
                    "message": {
                        "user": user.to_dict(),
                        "influencer": influencer.to_dict()
                    }
                }
            else:
                return {
                    "status": "error",
                    "error_reason": "Influencer not found"
                }
        except SQLAlchemyError as e:
            return {
                "status": "error",
                "error_reason": str(e)
            }

    def get_influencers(self):
        try:
            influencers = self.Influencers.query.all()
            result = []
            for influencer in influencers:
                user = influencer.user  # Access the linked user
                result.append({
                    "user": user.to_dict(),
                    "influencer": influencer.to_dict()
                })

            return {
                "status": "success",
                "message": result
            }
        except SQLAlchemyError as e:
            return {
                "status": "error",
                "error_reason": str(e)
            }
    @staticmethod
    def upload_image_to_cloudinary(image, folder="linxy_users"):
        try:
            response = cloudinary.uploader.upload(image, folder=folder)
            return response['secure_url']
        except Exception as e:
            print(f"Cloudinary upload failed: {e}")
            return None

    @staticmethod
    def delete_image_from_cloudinary(image_url):
        try:
            match = re.search(r'/upload/.+/(.*)\.\w+$', image_url)
            if not match:
                raise ValueError("Invalid Cloudinary URL format")
            public_id = match.group(1)
            result = cloudinary.uploader.destroy(public_id)
            return result
        except Exception as e:
            print(f"Cloudinary delete failed: {e}")
            return {'result': 'error', 'error': str(e)}

    def upload_influencers(self, json_path='all_influencers.json'):
        """
        Upload influencers and their associated user accounts using ORM.
        Email: inf1@gmail.com, inf2@gmail.com...
        Password: infpass1, infpass2...
        Handles null values and provides better error reporting.
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                influencers = json.load(file)

            results = {
                "success": 0,
                "failed": 0,
                "errors": []
            }

            for index, influencer in enumerate(influencers, start=1):
                try:
                    dp = influencer.get('data_points', {})

                    # Email and password format
                    email = f"inf{index}@gmail.com"
                    password = f"infpass{index}"
                    hashed_password = generate_password_hash(password)

                    # Create user
                    user = self.Users(
                        full_name=influencer.get('full_name'),
                        phone=0,
                        photo_url=influencer.get('photo'),
                        email=email,
                        password=hashed_password,
                        role='influencer'
                    )
                    user.save()

                    # Create influencer entry
                    influencer_record = self.Influencers(
                        user_id=user.id,
                        social_net=dp.get('social_net', 'instagram'),
                        link=dp.get('link', ''),
                        price_stories=dp.get('price_stories', 0),
                        story_with_travel_to_location=dp.get('story_with_travel_to_location', 0),
                        price_reels_creative=dp.get('price_reels_creative', 0),
                        price_photo_post=dp.get('price_photo_post', 0),
                        collaboration=dp.get('collaboration', 0),
                        category=dp.get('category', 'lifestyle'),
                        subs=dp.get('subs', 0) or 0,
                        avg_view_reels=dp.get('avg_views_reels', 0) or 0,
                        cpv_reels_creative=dp.get('cpv_reels_creative', 0),
                        engagement_rate=dp.get('engagement_rate', 0),
                        men=dp.get('men', 0),
                        women=dp.get('women', 0),
                        age13_17=dp.get('age_13_17', 0),
                        age18_24=dp.get('age_18_24', 0),
                        age25_34=dp.get('age_25_34', 0),
                        age35_44=dp.get('age_35_44', 0),
                        armenia=dp.get('armenia', 0),
                        russia=dp.get('russia', 0),
                        georgia=dp.get('georgia', 0),
                        usa=dp.get('usa', 0),
                        yerevan=dp.get('yerevan', 0),
                        gyumri=dp.get('gyumri', 0),
                        vanadzor=dp.get('vanadzor', 0),
                        moscow=dp.get('moscow', 0)
                    )
                    influencer_record.save()
                    results["success"] += 1

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "index": index,
                        "email": email,
                        "error": str(e)
                    })

            return {
                "status": "completed",
                "total": len(influencers),
                "message": f"Successfully uploaded {results['success']} out of {len(influencers)} influencers",
                **results
            }

        except Exception as e:
            return {
                "status": "error",
                "error_reason": str(e),
                "message": "Failed to process influencer data"
            }

    @staticmethod
    def get_charts_data():
        with open('chart_data/charts.json', 'r') as f:
            carts = json.load(f)
        return carts