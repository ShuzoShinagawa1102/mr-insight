"""
DRF views for the rag application.

Each model gets a read-only (list + retrieve) ViewSet for now.
Write operations will be added incrementally as the RAG pipeline matures.
"""

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from .models import (
    Company,
    EventFact,
    FinancialStatement,
    Guidance,
    MetricFact,
    RiskFact,
    SourceDocument,
    StatementFact,
    ValuationSnapshot,
)
from .serializers import (
    CompanySerializer,
    EventFactSerializer,
    FinancialStatementSerializer,
    GuidanceSerializer,
    MetricFactSerializer,
    RiskFactSerializer,
    SourceDocumentSerializer,
    StatementFactSerializer,
    ValuationSnapshotSerializer,
)


class CompanyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Company.objects.order_by("name")
    serializer_class = CompanySerializer
    permission_classes = [AllowAny]


class SourceDocumentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = SourceDocument.objects.select_related("company").order_by("-published_at")
    serializer_class = SourceDocumentSerializer
    permission_classes = [AllowAny]


class MetricFactViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = MetricFact.objects.select_related("company").order_by("-asof")
    serializer_class = MetricFactSerializer
    permission_classes = [AllowAny]


class EventFactViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = EventFact.objects.select_related("company").order_by("-asof")
    serializer_class = EventFactSerializer
    permission_classes = [AllowAny]


class StatementFactViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = StatementFact.objects.select_related("company").order_by("-asof")
    serializer_class = StatementFactSerializer
    permission_classes = [AllowAny]


class RiskFactViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = RiskFact.objects.select_related("company").order_by("-asof")
    serializer_class = RiskFactSerializer
    permission_classes = [AllowAny]


class FinancialStatementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = FinancialStatement.objects.select_related("company").order_by(
        "company__name", "-period_year", "-period_quarter"
    )
    serializer_class = FinancialStatementSerializer
    permission_classes = [AllowAny]


class GuidanceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Guidance.objects.select_related("company").order_by("-updated_at")
    serializer_class = GuidanceSerializer
    permission_classes = [AllowAny]


class ValuationSnapshotViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ValuationSnapshot.objects.select_related("company").order_by("-asof")
    serializer_class = ValuationSnapshotSerializer
    permission_classes = [AllowAny]
