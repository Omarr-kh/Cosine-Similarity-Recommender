import numpy as np
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from real_state.models import UserInteraction, RealState


class CollaborativeFiltering:
    def __init__(self):
        self.user_item_matrix = self._create_user_item_matrix()

    def _create_user_item_matrix(self):
        # Fetch all user interactions
        interactions = UserInteraction.objects.all()

        # Create a dictionary to store user-item interactions
        user_item_matrix = defaultdict(lambda: defaultdict(int))

        # Populate the matrix
        for interaction in interactions:
            user_id = interaction.user.id
            property_id = interaction.property.id
            weight = {'view': 1, 'like': 2, 'save': 3}.get(
                interaction.interaction_type, 0
            )
            user_item_matrix[user_id][property_id] = weight

        return user_item_matrix

    def user_based_recommendations(self, user, top_n=10):
        target_user_id = user.id
        target_user_interactions = self.user_item_matrix.get(target_user_id, {})

        if not target_user_interactions:
            return RealState.objects.none()

        similarities = []
        for other_user_id, other_user_interactions in self.user_item_matrix.items():
            if other_user_id == target_user_id:
                continue

            common_properties = set(target_user_interactions.keys()) & set(
                other_user_interactions.keys()
            )
            if not common_properties:
                continue

            target_vector = [
                target_user_interactions[prop] for prop in common_properties
            ]
            other_vector = [other_user_interactions[prop] for prop in common_properties]

            similarity = cosine_similarity([target_vector], [other_vector])[0][0]
            similarities.append((other_user_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similar_users = [user_id for user_id, _ in similarities[:top_n]]

        recommended_properties = set()
        for user_id in top_similar_users:
            for property_id in self.user_item_matrix[user_id]:
                if property_id not in target_user_interactions:
                    recommended_properties.add(property_id)

        return RealState.objects.filter(id__in=recommended_properties)

    def item_based_recommendations(self, user, top_n=10):
        target_user_id = user.id
        target_user_interactions = self.user_item_matrix.get(target_user_id, {})

        if not target_user_interactions:
            return RealState.objects.none()

        # Fetch all properties and create a matrix of interactions
        all_properties = RealState.objects.all()
        property_ids = [prop.id for prop in all_properties]
        property_id_index = {
            property_id: idx for idx, property_id in enumerate(property_ids)
        }

        # Build the interaction matrix
        interaction_matrix = np.zeros((len(property_ids), len(self.user_item_matrix)))
        for user_idx, (user_id, interactions) in enumerate(
            self.user_item_matrix.items()
        ):
            for property_id, value in interactions.items():
                if property_id in property_id_index:
                    interaction_matrix[property_id_index[property_id], user_idx] = value

        # Compute the item similarity matrix
        similarity_matrix = cosine_similarity(interaction_matrix)

        # Calculate scores for unvisited properties
        target_interaction_vector = np.array(
            [target_user_interactions.get(prop_id, 0) for prop_id in property_ids]
        )
        property_scores = similarity_matrix.dot(target_interaction_vector)

        # Exclude properties already interacted with
        for idx, score in enumerate(target_interaction_vector):
            if score > 0:
                property_scores[idx] = 0

        # Get top-N recommendations
        top_indices = np.argsort(property_scores)[::-1][:top_n]
        recommended_property_ids = [property_ids[idx] for idx in top_indices]

        return RealState.objects.filter(id__in=recommended_property_ids)


collaborative_filtering_recommender = None


def get_collaborative_filtering_recommender():
    global collaborative_filtering_recommender
    if collaborative_filtering_recommender is None:
        collaborative_filtering_recommender = CollaborativeFiltering()
    return collaborative_filtering_recommender
