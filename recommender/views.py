from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .system import real_state_recommender

import traceback


@api_view(["GET"])
def get_recommendations(request):
    try:
        user_preferences = {
            "budget": float(request.query_params.get("budget")),
            "bedrooms": int(request.query_params.get("bedrooms")),
            "bathrooms": int(request.query_params.get("bathrooms")),
            "sqft": float(request.query_params.get("sqft")),
            "year_built": int(request.query_params.get("year_built")),
            "parking_spaces": int(request.query_params.get("parking_spaces")),
        }
        num_recommendations = int(request.query_params.get("num_recommendations", 5))

        recommendations_df = real_state_recommender.get_recommendations(user_preferences, num_recommendations)

        # Convert DataFrame to a JSON-serializable format
        recommendations = recommendations_df.to_dict(orient="records")

        return Response(recommendations, status=status.HTTP_200_OK)
    except:
        print(traceback.format_exc())
        return Response(status=status.HTTP_409_CONFLICT)
