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
        queryset = RealState.objects.all()

        # Convert the queryset to a Pandas DataFrame
        properties_data = pd.DataFrame(list(queryset.values()))

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

    def add_property(self, property_data):
        """
        Add a new property to the recommendation system.

        Parameters:
        property_data: dict with keys matching RealState fields
        """
        # Convert the property data to a DataFrame
        new_property_df = pd.DataFrame([property_data])

        # Append to properties DataFrame
        self.properties_df = pd.concat(
            [self.properties_df, new_property_df], ignore_index=True
        )

        # Normalize features of the new property
        feature_columns = [
            'price',
            'bedrooms',
            'bathrooms',
            'sqft',
            'year_built',
            'parking_spaces',
        ]
        new_features = self.scaler.transform(new_property_df[feature_columns])

        # Append normalized features to the features matrix
        self.features_matrix = np.vstack([self.features_matrix, new_features])

    def remove_property(self, property_id):
        """
        Remove a property from the recommendation system.

        Parameters:
        property_id: int, unique identifier of the property
        """
        # Find the index of the property to remove
        index_to_remove = self.properties_df[
            self.properties_df['id'] == property_id
        ].index

        if not index_to_remove.empty:
            # Drop the property from properties DataFrame
            self.properties_df = self.properties_df.drop(
                index=index_to_remove
            ).reset_index(drop=True)

            # Remove the corresponding row from the features matrix
            self.features_matrix = np.delete(
                self.features_matrix, index_to_remove, axis=0
            )
        else:
            pass

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


real_state_recommender = None


def get_real_state_recommender():
    global real_state_recommender
    if real_state_recommender is None:
        # Initialize the recommender here (only when accessed)
        real_state_recommender = RealEstateRecommender()
    return real_state_recommender
