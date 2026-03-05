"""
DRF serializers for the rag application.
"""

from rest_framework import serializers

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


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id",
            "company_id",
            "name",
            "name_en",
            "listings",
            "industries",
            "homepage",
            "description",
            "parent_company",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SourceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceDocument
        fields = [
            "id",
            "doc_id",
            "kind",
            "title",
            "published_at",
            "url",
            "company",
            "blob_ref",
            "extractor_version",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MetricFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricFact
        fields = [
            "id",
            "fact_id",
            "company",
            "fact_type",
            "asof",
            "evidences",
            "fingerprint",
            "tags",
            "name",
            "period_kind",
            "period_year",
            "period_quarter",
            "metric_value",
            "metric_unit",
            "metric_raw",
            "yoy",
            "qoq",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EventFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventFact
        fields = [
            "id",
            "fact_id",
            "company",
            "fact_type",
            "asof",
            "evidences",
            "fingerprint",
            "tags",
            "kind",
            "title",
            "summary",
            "impact",
            "severity",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class StatementFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementFact
        fields = [
            "id",
            "fact_id",
            "company",
            "fact_type",
            "asof",
            "evidences",
            "fingerprint",
            "tags",
            "kind",
            "text",
            "speaker",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RiskFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskFact
        fields = [
            "id",
            "fact_id",
            "company",
            "fact_type",
            "asof",
            "evidences",
            "fingerprint",
            "tags",
            "kind",
            "title",
            "description",
            "likelihood",
            "impact",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class FinancialStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialStatement
        fields = [
            "id",
            "fs_id",
            "company",
            "period_kind",
            "period_year",
            "period_quarter",
            "revenue",
            "gross_profit",
            "operating_income",
            "net_income",
            "total_assets",
            "total_liabilities",
            "equity",
            "cfo",
            "cfi",
            "cff",
            "evidences",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GuidanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guidance
        fields = [
            "id",
            "guidance_id",
            "company",
            "period_kind",
            "period_year",
            "period_quarter",
            "metric_name",
            "forecast_value",
            "forecast_unit",
            "forecast_raw",
            "updated_at",
            "evidences",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ValuationSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValuationSnapshot
        fields = [
            "id",
            "snapshot_id",
            "company",
            "asof",
            "market_cap",
            "enterprise_value",
            "per",
            "pbr",
            "ev_ebitda",
            "evidences",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
