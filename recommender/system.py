import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

from real_state.models import RealState


class RealEstateRecommender:
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.properties_df = None
        self.features_matrix = None
        self.load_properties()

    def load_properties(self):
        """
        Load and preprocess property data
        """
        queryset  = RealState.objects.all()

        # Convert the queryset to a Pandas DataFrame
        properties_data = pd.DataFrame(list(queryset.values(
            'price',
            'bedrooms',
            'bathrooms',
            'sqft',
            'year_built',
            'parking_spaces'
        )))

        # Ensure the DataFrame is not empty
        if properties_data.empty:
            raise ValueError("No property data found in the database.")

        # Store the properties DataFrame
        self.properties_df = properties_data

        # Select numerical features for similarity calculation
        feature_columns = [
            'price',
            'bedrooms',
            'bathrooms',
            'sqft',
            'year_built',
            'parking_spaces',
        ]

        # Normalize features to 0-1 range
        self.features_matrix = self.scaler.fit_transform(
            self.properties_df[feature_columns]
        )

    def get_recommendations(self, user_preferences, num_recommendations=5):
        """
        Get property recommendations based on user preferences

        Parameters:
        user_preferences: dict with keys:
            - budget: float
            - min_bedrooms: int
            - min_bathrooms: int
            - preferred_sqft: float
            - min_year_built: int
            - parking_spaces: int
        num_recommendations: int, number of properties to recommend

        Returns:
        DataFrame with recommended properties
        """
        # Create preference vector
        pref_vector = np.array(
            [
                user_preferences['budget'],
                user_preferences['min_bedrooms'],
                user_preferences['min_bathrooms'],
                user_preferences['preferred_sqft'],
                user_preferences['min_year_built'],
                user_preferences['parking_spaces'],
            ]
        ).reshape(1, -1)

        # Normalize preferences using the same scaler
        pref_vector_normalized = self.scaler.transform(pref_vector)

        # Calculate similarity scores
        similarity_scores = cosine_similarity(
            self.features_matrix, pref_vector_normalized
        ).flatten()

        # Apply hard constraints
        mask = (
            (self.properties_df['price'] <= user_preferences['budget'])
            & (self.properties_df['bedrooms'] >= user_preferences['min_bedrooms'])
            & (self.properties_df['bathrooms'] >= user_preferences['min_bathrooms'])
        )

        # Get indices of properties that meet constraints
        valid_indices = np.where(mask)[0]

        # Sort by similarity score
        recommended_indices = valid_indices[
            np.argsort(-similarity_scores[valid_indices])[:num_recommendations]
        ]

        # Get recommendations and format output
        recommendations = self.properties_df.iloc[recommended_indices].copy()

        return recommendations


real_state_recommender = RealEstateRecommender()
