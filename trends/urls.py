from django.urls import path

from trends.views import RelatedSearchesView, TrendingAnalysisView, TrendingHealthView

app_name = "trends"

urlpatterns = [
    path("", TrendingAnalysisView.as_view(), name="trending-analysis"),
    path("related-searches/", RelatedSearchesView.as_view(), name="related-searches"),
    path("health-status/", TrendingHealthView.as_view(), name="trending-health"),
]
