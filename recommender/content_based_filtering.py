from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np

from real_state.models import RealState, UserInteraction


class ContentFiltering:
    def __init__(self):
        try:
            self.all_properties = RealState.objects.only(
                "id",
                "price",
                "bedrooms",
                "bathrooms",
                "sqft",
                "year_built",
                "parking_spaces",
                "property_type",
                "has_garage",
                "has_pool",
            )
        except:
            self.all_properties = []

        numerical_features = np.array(
            [
                [
                    prop.price,
                    prop.bedrooms,
                    prop.bathrooms,
                    prop.sqft,
                    prop.year_built,
                    prop.parking_spaces,
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
        numerical_features = np.array(
            [
                property.price,
                property.bedrooms,
                property.bathrooms,
                property.sqft,
                property.year_built,
                property.parking_spaces,
            ]
        ).reshape(1, -1)
        numerical_features = self.scaler.transform(numerical_features).flatten()

        property_type = 1 if property.property_type == 'residential' else 0
        has_garage = 1 if property.has_garage else 0
        has_pool = 1 if property.has_pool else 0

        return np.concatenate(
            [numerical_features, [property_type, has_garage, has_pool]]
        )

    def get_similar_properties(self, user, top_n=10):
        user_interactions = UserInteraction.objects.filter(user=user)
        user_properties = [interaction.property for interaction in user_interactions]

        if not user_properties:
            return RealState.objects.none()

        user_feature_vectors = np.array(
            [self.property_to_feature_vector(prop) for prop in user_properties]
        )
        user_avg_vector = np.mean(user_feature_vectors, axis=0)

        # Compute similarity in bulk
        all_vectors = np.array(list(self.property_vectors.values()))
        similarities = cosine_similarity([user_avg_vector], all_vectors)[0]

        # Attach similarity scores to properties
        properties_with_similarity = [
            (prop, similarities[idx])
            for idx, prop in enumerate(self.all_properties)
            if similarities[idx] >= 0.7
        ]

        properties_with_similarity.sort(key=lambda x: x[1], reverse=True)
        return [prop for prop, _ in properties_with_similarity[:top_n]]


content_filtering_recommender = None


def get_content_filtering_recommender():
    global content_filtering_recommender
    if content_filtering_recommender is None:
        # Initialize the recommender here (only when accessed)
        content_filtering_recommender = ContentFiltering()
    return content_filtering_recommender
