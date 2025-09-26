from django.urls import path

from trends.views import SimilarQueriesView, TrendingAnalysisView, TrendingHealthView

app_name = "trends"

urlpatterns = [
    path("", TrendingAnalysisView.as_view(), name="trending-analysis"),
    path("similar/", SimilarQueriesView.as_view(), name="similar-queries"),
    path("health/", TrendingHealthView.as_view(), name="trending-health"),
]
