import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import LabelEncoder

import pickle
from pathlib import Path

class DataTransformer:
    @staticmethod
    def transform_influencers_data(raw_data):
        """
        Transforms raw influencers data into a structured DataFrame
        """
        influencers = []
        
        # Ensure raw_data has the correct structure
        if 'data' not in raw_data:
            raw_data = {'data': raw_data} if isinstance(raw_data, list) else {'data': [raw_data]}
        
        for item in raw_data['data']:
            influencer = item.get('influencer', {})
            user = item.get('user', {})
            
            # Safely get all values with defaults
            record = {
                'id': influencer.get('id', 0),
                'full_name': user.get('full_name', ''),
                'category': influencer.get('category', ''),
                'social_net': influencer.get('social_net', ''),
                'subs': influencer.get('subs', 0),
                'avg_view_reels': influencer.get('avg_view_reels', 0),
                'engagement_rate': float(influencer.get('engagement_rate', 0)) if influencer.get('engagement_rate') not in [None, ''] else 0,
                'price_photo_post': float(influencer.get('price_photo_post', 0)) if influencer.get('price_photo_post') not in [None, ''] else 0,
                'price_reels_creative': float(influencer.get('price_reels_creative', 0)) if influencer.get('price_reels_creative') not in [None, ''] else 0,
                'price_stories': float(influencer.get('price_stories', 0)) if influencer.get('price_stories') not in [None, ''] else 0,
                'men': float(influencer.get('men', 0)) if influencer.get('men') not in [None, ''] else 0,
                'women': float(influencer.get('women', 0)) if influencer.get('women') not in [None, ''] else 0,
                'age13_17': float(influencer.get('age13_17', 0)) if influencer.get('age13_17') not in [None, ''] else 0,
                'age18_24': float(influencer.get('age18_24', 0)) if influencer.get('age18_24') not in [None, ''] else 0,
                'age25_34': float(influencer.get('age25_34', 0)) if influencer.get('age25_34') not in [None, ''] else 0,
                'age35_44': float(influencer.get('age35_44', 0)) if influencer.get('age35_44') not in [None, ''] else 0,
                'armenia': float(influencer.get('armenia', 0)) if influencer.get('armenia') not in [None, ''] else 0,
                'yerevan': float(influencer.get('yerevan', 0)) if influencer.get('yerevan') not in [None, ''] else 0,
                'gyumri': float(influencer.get('gyumri', 0)) if influencer.get('gyumri') not in [None, ''] else 0,
                'vanadzor': float(influencer.get('vanadzor', 0)) if influencer.get('vanadzor') not in [None, ''] else 0,
                'russia': float(influencer.get('russia', 0)) if influencer.get('russia') not in [None, ''] else 0,
                'moscow': float(influencer.get('moscow', 0)) if influencer.get('moscow') not in [None, ''] else 0,
                'georgia': float(influencer.get('georgia', 0)) if influencer.get('georgia') not in [None, ''] else 0,
                'usa': float(influencer.get('usa', 0)) if influencer.get('usa') not in [None, ''] else 0,
                'photo_url': user.get('photo_url', ''),
                'link': influencer.get('link', '')
            }
            
            influencers.append(record)
        
        df = pd.DataFrame(influencers)
        
        # Encode categorical features
        label_encoders = {}
        categorical_cols = ['category', 'social_net']
        
        for col in categorical_cols:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
        
        return df, label_encoders
    
    @staticmethod
    def transform_company_data(company_data, label_encoders):
        """
        Transforms company data into the same format as influencers data
        """
        # Create a dictionary with default values for all expected fields
        default_values = {
            'category': '',
            'social_net': '',
            'subs': 0,
            'avg_view_reels': 0,
            'engagement_rate': 0,
            'price_photo_post': 0,
            'price_reels_creative': 0,
            'price_stories': 0,
            'men': 0,
            'women': 0,
            'age13_17': 0,
            'age18_24': 0,
            'age25_34': 0,
            'age35_44': 0,
            'armenia': 0,
            'yerevan': 0,
            'gyumri': 0,
            'vanadzor': 0,
            'russia': 0,
            'moscow': 0,
            'georgia': 0,
            'usa': 0
        }
        
        # Update defaults with provided company data
        company_data = {**default_values, **company_data}
        
        # Convert to DataFrame
        company_df = pd.DataFrame([company_data])
        
        # Encode categorical features using the same encoders as influencers
        categorical_cols = ['category', 'social_net']
        
        for col in categorical_cols:
            if col in company_df.columns and col in label_encoders:
                # Handle unseen categories by assigning a new value
                le = label_encoders[col]
                company_df[col] = company_df[col].astype(str).apply(
                    lambda x: x if x in le.classes_ else 'unknown'
                )
                if 'unknown' not in le.classes_:
                    le.classes_ = np.append(le.classes_, 'unknown')
                company_df[col] = le.transform(company_df[col])
        
        return company_df


class AiModel:
    def __init__(self):
        self.model = DecisionTreeRegressor(random_state=42)
        self.label_encoders = None
        self.feature_columns = None
        self.is_trained = False
    
    def train(self, influencers_data):
        """
        Train the Decision Tree model on influencers data
        """
        # Transform raw data
        df, self.label_encoders = DataTransformer.transform_influencers_data(influencers_data)
        
        # Define target and features
        df['target_score'] = (
            df['engagement_rate'] * 0.4 + 
            np.log(df['subs'] + 1) * 0.3 + 
            (df['age18_24'] + df['age25_34']) * 0.2 + 
            (1 - (df['price_reels_creative'] / (df['price_reels_creative'].max() + 1e-6))) * 0.1
        )
        
        # Define feature columns (excluding metadata)
        self.feature_columns = [
            'category', 'social_net', 'subs', 'avg_view_reels', 'engagement_rate',
            'price_photo_post', 'price_reels_creative', 'price_stories',
            'men', 'women', 'age13_17', 'age18_24', 'age25_34', 'age35_44',
            'armenia', 'yerevan', 'gyumri', 'vanadzor', 'russia', 'moscow', 
            'georgia', 'usa'
        ]
        
        X = df[self.feature_columns]
        y = df['target_score']
        
        # Train the model
        self.model.fit(X, y)
        self.is_trained = True
    
    def predict(self, company_data):
        """
        Predict scores for influencers based on company data
        """
        if not self.is_trained:
            raise ValueError("Model has not been trained yet. Call train() first.")
        
        # Transform company data to match training format
        company_df = DataTransformer.transform_company_data(company_data, self.label_encoders)
        
        # Ensure all required columns are present
        for col in self.feature_columns:
            if col not in company_df.columns:
                company_df[col] = 0  # Fill missing with 0
        
        # Make sure columns are in the same order as training
        company_df = company_df[self.feature_columns]
        
        # Predict scores
        scores = self.model.predict(company_df)
        return scores
    
    def get_best_10(self, company_data, influencers_data):
        """
        Get the top 10 influencers based on company data
        """
        if not self.is_trained:
            raise ValueError("Model has not been trained yet. Call train() first.")
        
        # Transform influencers data
        influencers_df, _ = DataTransformer.transform_influencers_data(influencers_data)
        
        # Create a DataFrame with company data repeated for each influencer
        company_df = pd.DataFrame([company_data] * len(influencers_df))
        
        # Ensure all required columns are present
        for col in self.feature_columns:
            if col not in company_df.columns:
                company_df[col] = 0
        
        # Encode categorical columns using the label encoders
        categorical_cols = ['category', 'social_net']
        for col in categorical_cols:
            if col in company_df.columns and col in self.label_encoders:
                le = self.label_encoders[col]
                company_df[col] = company_df[col].astype(str).apply(
                    lambda x: x if x in le.classes_ else 'unknown'
                )
                if 'unknown' not in le.classes_:
                    le.classes_ = np.append(le.classes_, 'unknown')
                company_df[col] = le.transform(company_df[col])
        
        # Make sure columns are in the same order as training
        company_df = company_df[self.feature_columns]
        
        # Predict scores for all influencers
        influencers_df['score'] = self.model.predict(company_df)
        
        # Get top 10 influencers
        top_10 = influencers_df.sort_values('score', ascending=False).head(10)
        
        # Format the result with relevant information
        result = []
        for _, row in top_10.iterrows():
            result.append({
                'id': row['id'],
                'full_name': row['full_name'],
                'category': row['category'],
                'social_net': row['social_net'],
                'subs': row['subs'],
                'engagement_rate': row['engagement_rate'],
                'avg_view_reels': row['avg_view_reels'],
                'price_reels_creative': row['price_reels_creative'],
                'score': row['score'],
                'photo_url': row['photo_url'],
                'link': row['link']
            })
        
        return result

    def save(self, file_path):
        """
        Save the trained model to a file
        :param file_path: Path to save the model (e.g., 'model.pkl')
        """
        if not self.is_trained:
            raise ValueError("Model has not been trained yet. Nothing to save.")
            
        model_data = {
            'model': self.model,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)
        # Alternatively with joblib:
        # dump(model_data, file_path)
    
    @classmethod
    def load(cls, file_path):
        """
        Load a trained model from file
        :param file_path: Path to the saved model file
        :return: Loaded AiModel instance
        """
        with open(file_path, 'rb') as f:
            model_data = pickle.load(f)
        # Alternatively with joblib:
        # model_data = load(file_path)
        
        loaded_model = cls()
        loaded_model.model = model_data['model']
        loaded_model.label_encoders = model_data['label_encoders']
        loaded_model.feature_columns = model_data['feature_columns']
        loaded_model.is_trained = model_data['is_trained']
        
        return loaded_model