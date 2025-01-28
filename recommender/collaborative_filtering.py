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
        common_properties = set(target_user_interactions.keys()) & set(
            other_user_interactions.keys()
        )
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

    # Create item-item similarity matrix (precompute this offline for efficiency)
    all_properties = RealState.objects.all()
    property_ids = [prop.id for prop in all_properties]
    property_vectors = defaultdict(list)

    # Create property vectors based on user interactions
    for property_id in property_ids:
        for user_id, interactions in user_item_matrix.items():
            property_vectors[property_id].append(interactions.get(property_id, 0))

    # Compute item-item similarity matrix
    item_similarity_matrix = {}
    for i, property_id_1 in enumerate(property_ids):
        for j, property_id_2 in enumerate(property_ids):
            if property_id_1 == property_id_2:
                continue  # Skip self-similarity
            if (property_id_2, property_id_1) in item_similarity_matrix:
                item_similarity_matrix[(property_id_1, property_id_2)] = (
                    item_similarity_matrix[(property_id_2, property_id_1)]
                )
            else:
                vector_1 = property_vectors[property_id_1]
                vector_2 = property_vectors[property_id_2]
                similarity = cosine_similarity([vector_1], [vector_2])[0][0]
                item_similarity_matrix[(property_id_1, property_id_2)] = similarity

    # Generate recommendations for the target user
    property_scores = defaultdict(float)
    for property_id in target_user_interactions:
        for other_property_id in property_ids:
            if other_property_id not in target_user_interactions:
                similarity = item_similarity_matrix.get(
                    (property_id, other_property_id), 0
                )
                property_scores[other_property_id] += similarity

    # Sort properties by their recommendation scores
    sorted_properties = sorted(
        property_scores.items(), key=lambda x: x[1], reverse=True
    )

    # Get top N recommended properties
    recommended_property_ids = [
        property_id for property_id, _ in sorted_properties[:top_n]
    ]
    return RealState.objects.filter(id__in=recommended_property_ids)
