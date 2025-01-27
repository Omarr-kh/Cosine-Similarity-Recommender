from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .system import get_real_state_recommender
from .content_based_filtering import get_content_filtering_recommender
from .collaborative_filtering import user_based_collaborative_filtering

from django.contrib.auth.models import User

import traceback


@api_view(["GET"])
def get_recommendations(request):
    try:
        real_state_recommender = get_real_state_recommender()
        user_preferences = {
            "budget": float(request.query_params.get("budget")),
            "min_bedrooms": int(request.query_params.get("bedrooms")),
            "min_bathrooms": int(request.query_params.get("bathrooms")),
            "preferred_sqft": float(request.query_params.get("sqft")),
            "min_year_built": int(request.query_params.get("year_built")),
            "parking_spaces": int(request.query_params.get("parking_spaces")),
        }
        num_recommendations = int(request.query_params.get("num_recommendations", 5))

        recommendations_df = real_state_recommender.get_recommendations(
            user_preferences, num_recommendations
        )

        # Convert DataFrame to a JSON-serializable format
        recommendations = recommendations_df.to_dict(orient="records")

        return Response(recommendations, status=status.HTTP_200_OK)
    except:
        print(traceback.format_exc())
        return Response(status=status.HTTP_409_CONFLICT)


@permission_classes([permissions.IsAuthenticated])
@api_view(["GET"])
def recommend_properties(request):
    try:
        recommender = get_content_filtering_recommender()
        user = User.objects.get(id=2)
        similar_properties = recommender.get_similar_properties(user, top_n=5)

        # Serialize the recommended properties
        recommendations = [
            {
                'id': prop.id,
                'price': prop.price,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'sqft': prop.sqft,
                'year_built': prop.year_built,
                'property_type': prop.property_type,
                'address': prop.address,
                'city': prop.city,
                'country': prop.country,
                'parking_spaces': prop.parking_spaces,
                'has_garage': prop.has_garage,
                'has_pool': prop.has_pool,
                'description': prop.description,
            }
            for prop in similar_properties
        ]

        return Response({'recommendations': recommendations}, status=status.HTTP_200_OK)
    except:
        print(traceback.format_exc())
        return Response(status=status.HTTP_409_CONFLICT)


@permission_classes([permissions.IsAuthenticated])
@api_view(["GET"])
def recommend_properties_cf(request):
    try:
        user = request.user
        # Choose either user-based or item-based CF
        similar_properties = user_based_collaborative_filtering(user, top_n=5)
        # similar_properties = item_based_collaborative_filtering(user, top_n=5)

        # Serialize the recommended properties
        recommendations = [
            {
                'id': prop.id,
                'price': prop.price,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'sqft': prop.sqft,
                'year_built': prop.year_built,
                'property_type': prop.property_type,
                'address': prop.address,
                'city': prop.city,
                'country': prop.country,
                'parking_spaces': prop.parking_spaces,
                'has_garage': prop.has_garage,
                'has_pool': prop.has_pool,
                'description': prop.description,
            }
            for prop in similar_properties
        ]

        return Response({'recommendations': recommendations}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error: {e}")
        return Response(status=status.HTTP_409_CONFLICT)
