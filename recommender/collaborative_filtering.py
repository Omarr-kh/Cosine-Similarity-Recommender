import numpy as np
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity

from real_state.models import UserInteraction, RealState

def create_user_item_matrix():
    # Fetch all user interactions
    interactions = UserInteraction.objects.all()

    # Create a dictionary to store user-item interactions
    user_item_matrix = defaultdict(lambda: defaultdict(int))

    # Populate the matrix
    for interaction in interactions:
        user_id = interaction.user.id
        property_id = interaction.property.id
        # Assign weights to interaction types (e.g., view=1, like=2, save=3)
        weight = {'view': 1, 'like': 2, 'save': 3}.get(interaction.interaction_type, 0)
        user_item_matrix[user_id][property_id] = weight

    return user_item_matrix

def user_based_collaborative_filtering(user, top_n=10):
    user_item_matrix = create_user_item_matrix()

    # Get the target user's interactions
    target_user_id = user.id
    target_user_interactions = user_item_matrix.get(target_user_id, {})

    if not target_user_interactions:
        return RealState.objects.none()  # No interactions for the user

    # Compute similarity between the target user and all other users
    similarities = []
    for other_user_id, other_user_interactions in user_item_matrix.items():
        if other_user_id == target_user_id:
            continue  # Skip the target user

        # Find common properties between the target user and the other user
        common_properties = set(target_user_interactions.keys()) & set(other_user_interactions.keys())
        if not common_properties:
            continue  # No common properties

        # Create vectors for common properties
        target_vector = [target_user_interactions[prop] for prop in common_properties]
        other_vector = [other_user_interactions[prop] for prop in common_properties]

        # Compute cosine similarity
        similarity = cosine_similarity([target_vector], [other_vector])[0][0]
        similarities.append((other_user_id, similarity))

    # Sort users by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Get top N similar users
    top_similar_users = [user_id for user_id, _ in similarities[:top_n]]

    # Recommend properties interacted with by similar users
    recommended_properties = set()
    for user_id in top_similar_users:
        for property_id in user_item_matrix[user_id]:
            if property_id not in target_user_interactions:
                recommended_properties.add(property_id)

    # Fetch recommended properties from the database
    return RealState.objects.filter(id__in=recommended_properties)

def item_based_collaborative_filtering(user, top_n=10):
    user_item_matrix = create_user_item_matrix()

    # Get the target user's interactions
    target_user_id = user.id
    target_user_interactions = user_item_matrix.get(target_user_id, {})

    if not target_user_interactions:
        return RealState.objects.none()  # No interactions for the user

    # Compute similarity between properties
    property_similarities = defaultdict(list)
    for other_user_id, other_user_interactions in user_item_matrix.items():
        if other_user_id == target_user_id:
            continue  # Skip the target user

        # Find common properties between the target user and the other user
        common_properties = set(target_user_interactions.keys()) & set(other_user_interactions.keys())
        if not common_properties:
            continue  # No common properties

        # Create vectors for common properties
        target_vector = [target_user_interactions[prop] for prop in common_properties]
        other_vector = [other_user_interactions[prop] for prop in common_properties]

        # Compute cosine similarity
        similarity = cosine_similarity([target_vector], [other_vector])[0][0]

        # Store similarity for each property
        for property_id in other_user_interactions:
            if property_id not in target_user_interactions:
                property_similarities[property_id].append(similarity)

    # Average similarity scores for each property
    property_avg_similarities = {
        property_id: np.mean(scores) for property_id, scores in property_similarities.items()
    }

    # Sort properties by average similarity
    sorted_properties = sorted(property_avg_similarities.items(), key=lambda x: x[1], reverse=True)

    # Get top N recommended properties
    recommended_property_ids = [property_id for property_id, _ in sorted_properties[:top_n]]
    return RealState.objects.filter(id__in=recommended_property_ids)