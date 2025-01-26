from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np

from real_state.models import RealState, UserInteraction


# Fit the scaler on the entire dataset once
all_properties = RealState.objects.all()
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
        for prop in all_properties
    ]
)
scaler = MinMaxScaler().fit(numerical_features)


def property_to_feature_vector(property):
    # Normalize numerical features using the pre-fitted scaler
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
    numerical_features = scaler.transform(numerical_features).flatten()

    # Encode categorical features
    property_type = 1 if property.property_type == 'residential' else 0
    has_garage = 1 if property.has_garage else 0
    has_pool = 1 if property.has_pool else 0

    # Combine all features into a single vector
    feature_vector = np.concatenate(
        [numerical_features, [property_type, has_garage, has_pool]]
    )
    return feature_vector


def get_similar_properties(user, top_n=10):
    # Get properties the user has interacted with
    user_interactions = UserInteraction.objects.filter(user=user)
    user_properties = [interaction.property for interaction in user_interactions]
    for prop in user_properties:
        print(
            f"Property ID: {prop.id}, Feature Vector: {property_to_feature_vector(prop)}"
        )

    if not user_properties:
        return RealState.objects.none()  # Return empty queryset if no interactions

    # Convert user's properties to feature vectors
    user_feature_vectors = np.array(
        [property_to_feature_vector(prop) for prop in user_properties]
    )

    # Compute average feature vector for the user
    user_avg_vector = np.mean(user_feature_vectors, axis=0)

    # Compute similarity for all properties
    all_properties = RealState.objects.all()
    similarities = []
    for prop in all_properties:
        prop_vector = property_to_feature_vector(prop)
        similarity = cosine_similarity([user_avg_vector], [prop_vector])[0][0]
        similarities.append((prop, similarity))

    # Sort by similarity and return top N
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [prop for prop, _ in similarities[:top_n]]
