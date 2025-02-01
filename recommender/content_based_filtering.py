from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.db.models import Prefetch
from real_state.models import RealState, UserInteraction, Feature
from functools import lru_cache


class ContentFiltering:
    def __init__(self):
        # Fetch all properties with their features in a single query
        self.all_properties = RealState.objects.only(
            "id",
            "price",
            "bedrooms",
            "bathrooms",
            "sqft",
        ).all()
        # Check if properties exist
        if not self.all_properties:
            raise ValueError("No properties found in the database.")

        # Precompute all feature names for one-hot encoding
        self.all_feature_names = list(Feature.objects.values_list('name', flat=True))

        # Extract numerical features and scale them
        numerical_features = np.array(
            [
                [
                    prop.price,
                    prop.bedrooms,
                    prop.bathrooms,
                    prop.sqft,
                ]
                for prop in self.all_properties
            ]
        )
        self.scaler = MinMaxScaler().fit(numerical_features)

        # Precompute and cache feature vectors
        self.property_vectors = {
            prop.id: self.property_to_feature_vector(prop)
            for prop in self.all_properties
        }

    def property_to_feature_vector(self, property):
        # Numerical features
        numerical_features = np.array(
            [
                property.price,
                property.bedrooms,
                property.bathrooms,
                property.sqft,
            ]
        ).reshape(1, -1)
        numerical_features = self.scaler.transform(numerical_features).flatten()

        # Combine all features into a single vector
        return numerical_features

    @lru_cache(maxsize=128)  # Cache results for frequently accessed users
    def get_similar_properties(self, user_id, top_n=10):
        # Fetch user interactions in a single query
        user_interactions = UserInteraction.objects.filter(
            user_id=user_id
        ).select_related('property')
        user_properties = [interaction.property for interaction in user_interactions]

        if not user_properties:
            return RealState.objects.none()

        # Compute average feature vector for user's interacted properties
        user_feature_vectors = np.array(
            [self.property_vectors[prop.id] for prop in user_properties]
        )
        user_avg_vector = np.mean(user_feature_vectors, axis=0)

        # Compute similarity in bulk
        all_vectors = np.array(list(self.property_vectors.values()))
        similarities = cosine_similarity([user_avg_vector], all_vectors)[0]

        # Attach similarity scores to properties
        properties_with_similarity = [
            (prop, similarities[idx])
            for idx, prop in enumerate(self.all_properties)
            if similarities[idx] >= 0.7  # Adjust threshold as needed
        ]

        # Sort by similarity and return top N properties
        properties_with_similarity.sort(key=lambda x: x[1], reverse=True)
        return [prop for prop, _ in properties_with_similarity[:top_n]]


# Singleton pattern for the recommender
content_filtering_recommender = None


def get_content_filtering_recommender():
    global content_filtering_recommender
    if content_filtering_recommender is None:
        content_filtering_recommender = ContentFiltering()
    return content_filtering_recommender
