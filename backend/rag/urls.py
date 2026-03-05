"""
URL patterns for the rag application.

Mounted under /api/ by config/urls.py.
"""

from rest_framework.routers import DefaultRouter

from .views import (
    CompanyViewSet,
    EventFactViewSet,
    FinancialStatementViewSet,
    GuidanceViewSet,
    MetricFactViewSet,
    RiskFactViewSet,
    SourceDocumentViewSet,
    StatementFactViewSet,
    ValuationSnapshotViewSet,
)

router = DefaultRouter()
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"documents", SourceDocumentViewSet, basename="sourcedocument")
router.register(r"facts/metrics", MetricFactViewSet, basename="metricfact")
router.register(r"facts/events", EventFactViewSet, basename="eventfact")
router.register(r"facts/statements", StatementFactViewSet, basename="statementfact")
router.register(r"facts/risks", RiskFactViewSet, basename="riskfact")
router.register(r"financials", FinancialStatementViewSet, basename="financialstatement")
router.register(r"guidances", GuidanceViewSet, basename="guidance")
router.register(r"valuations", ValuationSnapshotViewSet, basename="valuationsnapshot")

urlpatterns = router.urls
