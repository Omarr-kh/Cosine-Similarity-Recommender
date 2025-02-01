import numpy as np
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

from real_state.models import RealState, UserInteraction


class UserBasedCF:
    def __init__(self):
        self.user_item_matrix = self._create_matrix()

    def _create_matrix(self):
        interactions = UserInteraction.objects.all()
        matrix = defaultdict(dict)

        for interaction in interactions:
            user_id = interaction.user.id
            property_id = interaction.property.id
            weight = {'view': 1, 'like': 2, 'save': 3}.get(
                interaction.interaction_type, 0
            )
            matrix[user_id][property_id] = weight

        return matrix

    def get_recommendations(self, user, top_n=10):
        target_user_id = user.id
        user_interactions = self.user_item_matrix.get(target_user_id, {})

        if not user_interactions:
            return RealState.objects.none()

        # Find users who have rated any of the same properties
        similar_users = []
        target_items = set(user_interactions.keys())

        property_user_map = defaultdict(list)
        # First, build a map of properties to users who rated them
        for other_user_id, other_interactions in self.user_item_matrix.items():
            if other_user_id != target_user_id:
                for prop_id in other_interactions:
                    property_user_map[prop_id].append(other_user_id)

        # Find users who rated any of the same properties
        candidate_users = set()
        for prop_id in target_items:
            candidate_users.update(property_user_map[prop_id])

        for other_user_id in candidate_users:
            other_interactions = self.user_item_matrix[other_user_id]
            other_items = set(other_interactions.keys())

            # Calculate overlap
            common_items = target_items & other_items
            if not common_items:
                continue

            # Calculate simple similarity based on rating agreement
            rating_agreements = 0
            for item in common_items:
                rating_diff = abs(user_interactions[item] - other_interactions[item])
                if rating_diff <= 1:  # Consider ratings within 1 point as agreement
                    rating_agreements += 1

            # Calculate similarity score
            similarity = rating_agreements / len(common_items)

            # Accept any user with any positive similarity
            if similarity > 0:
                similar_users.append((other_user_id, similarity))

        # Get recommendations
        recommendations = defaultdict(list)  # Changed to store all ratings

        for other_user_id, similarity in similar_users:
            other_interactions = self.user_item_matrix[other_user_id]

            # Recommend properties this user hasn't seen
            for prop_id, rating in other_interactions.items():
                if prop_id not in user_interactions:
                    recommendations[prop_id].append((float(rating), similarity))

        # Score properties by weighted average rating
        scored_items = []
        for prop_id, ratings_and_sims in recommendations.items():
            ratings = [r for r, _ in ratings_and_sims]
            sims = [s for _, s in ratings_and_sims]
            avg_rating = sum(r * s for r, s in ratings_and_sims) / sum(sims)
            scored_items.append((prop_id, avg_rating))

        if not scored_items:
            # Fallback: recommend most popular properties user hasn't seen
            property_ratings = defaultdict(list)

            for interactions in self.user_item_matrix.values():
                for prop_id, rating in interactions.items():
                    if prop_id not in user_interactions:
                        property_ratings[prop_id].append(float(rating))

            scored_items = [
                (prop_id, sum(ratings) / len(ratings))
                for prop_id, ratings in property_ratings.items()
                if len(ratings) >= 2  # Require at least 2 ratings
            ]

        if not scored_items:
            return RealState.objects.none()

        scored_items.sort(key=lambda x: x[1], reverse=True)
        recommended_ids = [item[0] for item in scored_items[:top_n]]

        return RealState.objects.filter(id__in=recommended_ids)


class ItemBasedCF:
    def __init__(self):
        self.item_user_matrix = self._create_matrix()
        self.item_similarities = {}
        self.item_popularity = self._calculate_item_popularity()

    def _create_matrix(self):
        interactions = UserInteraction.objects.all()
        matrix = defaultdict(dict)

        interaction_count = 0

        for interaction in interactions:
            property_id = interaction.property.id
            user_id = interaction.user.id
            weight = {'view': 1, 'like': 2, 'save': 3}.get(
                interaction.interaction_type, 0
            )
            matrix[property_id][user_id] = weight
            interaction_count += 1

        return matrix

    def _calculate_item_popularity(self):
        """Calculate popularity scores for items."""
        popularity = defaultdict(lambda: {'count': 0, 'avg_weight': 0.0})

        for item_id, users in self.item_user_matrix.items():
            popularity[item_id]['count'] = len(users)
            popularity[item_id]['avg_weight'] = sum(users.values()) / len(users)

        return popularity

    def _compute_item_similarity(self, item1_id, item2_id):
        """Compute similarity between two items using multiple metrics."""
        item1_users = self.item_user_matrix.get(item1_id, {})
        item2_users = self.item_user_matrix.get(item2_id, {})

        # Get common users
        common_users = set(item1_users.keys()) & set(item2_users.keys())
        if not common_users:
            return 0.0

        # Calculate Jaccard similarity
        all_users = set(item1_users.keys()) | set(item2_users.keys())
        jaccard_sim = len(common_users) / len(all_users)

        # Calculate rating similarity
        rating_similarities = []
        for user_id in common_users:
            rating1 = item1_users[user_id]
            rating2 = item2_users[user_id]
            # Consider ratings similar if they're within 1 point
            rating_sim = 1.0 - (
                abs(rating1 - rating2) / 3.0
            )  # 3.0 is max possible difference
            rating_similarities.append(rating_sim)

        rating_sim = sum(rating_similarities) / len(rating_similarities)

        # Combine similarities with weights
        combined_sim = (jaccard_sim * 0.4) + (rating_sim * 0.6)
        return combined_sim

    def get_recommendations(self, user, top_n=10):
        target_user_id = user.id
        user_interactions = defaultdict(dict)

        # Get user's interactions
        for item_id, users in self.item_user_matrix.items():
            if target_user_id in users:
                user_interactions[item_id] = users[target_user_id]

        if not user_interactions:
            return RealState.objects.none()

        # Calculate recommendations
        recommendations = defaultdict(float)
        similarity_sums = defaultdict(float)
        similar_items_found = 0

        # For each item the user has interacted with
        for user_item_id, user_rating in user_interactions.items():
            similar_items = 0

            # Compare with all other items
            for other_item_id in self.item_user_matrix:
                if other_item_id not in user_interactions:  # Only consider unseen items
                    # Get or compute similarity
                    sim_pair = tuple(sorted([user_item_id, other_item_id]))
                    if sim_pair not in self.item_similarities:
                        self.item_similarities[sim_pair] = (
                            self._compute_item_similarity(sim_pair[0], sim_pair[1])
                        )

                    similarity = self.item_similarities[sim_pair]
                    if similarity > 0.1:  # Lowered threshold for sparse data
                        similar_items += 1
                        recommendations[other_item_id] += similarity * user_rating
                        similarity_sums[other_item_id] += similarity

            similar_items_found += similar_items

        # Normalize and sort recommendations
        scored_items = []
        for item_id, score in recommendations.items():
            if similarity_sums[item_id] > 0:
                normalized_score = score / similarity_sums[item_id]
                # Boost score with item popularity
                popularity_boost = (
                    self.item_popularity[item_id]['avg_weight'] / 3.0
                )  # Normalize to [0,1]
                final_score = (normalized_score * 0.7) + (popularity_boost * 0.3)
                scored_items.append((item_id, final_score))

        if not scored_items:
            # Fallback: recommend popular items the user hasn't interacted with
            for item_id, pop_data in self.item_popularity.items():
                if item_id not in user_interactions and pop_data['count'] >= 2:
                    popularity_score = (
                        pop_data['count'] * pop_data['avg_weight']
                    ) / 3.0
                    scored_items.append((item_id, popularity_score))

        if not scored_items:
            return RealState.objects.none()

        scored_items.sort(key=lambda x: x[1], reverse=True)
        recommended_ids = [item[0] for item in scored_items[:top_n]]

        return RealState.objects.filter(id__in=recommended_ids)


# Singleton instances
user_based_recommender = None
item_based_recommender = None


def get_user_based_recommender():
    global user_based_recommender
    if user_based_recommender is None:
        user_based_recommender = UserBasedCF()
    return user_based_recommender


def get_item_based_recommender():
    global item_based_recommender
    if item_based_recommender is None:
        item_based_recommender = ItemBasedCF()
    return item_based_recommender
