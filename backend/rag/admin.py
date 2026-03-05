"""
Django admin registrations for the rag application.
"""

from django.contrib import admin

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


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("company_id", "name", "name_en", "created_at")
    search_fields = ("company_id", "name", "name_en")
    ordering = ("name",)


@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = ("doc_id", "title", "kind", "published_at", "company")
    list_filter = ("kind",)
    search_fields = ("doc_id", "title")
    ordering = ("-published_at",)


@admin.register(MetricFact)
class MetricFactAdmin(admin.ModelAdmin):
    list_display = (
        "fact_id",
        "company",
        "name",
        "metric_value",
        "metric_unit",
        "period_kind",
        "period_year",
    )
    list_filter = ("name", "metric_unit", "period_kind")
    search_fields = ("fact_id", "fingerprint", "name")


@admin.register(EventFact)
class EventFactAdmin(admin.ModelAdmin):
    list_display = ("fact_id", "company", "kind", "title", "asof")
    list_filter = ("kind",)
    search_fields = ("fact_id", "title")


@admin.register(StatementFact)
class StatementFactAdmin(admin.ModelAdmin):
    list_display = ("fact_id", "company", "kind", "speaker", "asof")
    list_filter = ("kind",)
    search_fields = ("fact_id", "text")


@admin.register(RiskFact)
class RiskFactAdmin(admin.ModelAdmin):
    list_display = ("fact_id", "company", "kind", "title", "likelihood", "impact")
    list_filter = ("kind",)
    search_fields = ("fact_id", "title")


@admin.register(FinancialStatement)
class FinancialStatementAdmin(admin.ModelAdmin):
    list_display = ("fs_id", "company", "period_kind", "period_year", "period_quarter")
    list_filter = ("period_kind",)
    search_fields = ("fs_id",)


@admin.register(Guidance)
class GuidanceAdmin(admin.ModelAdmin):
    list_display = (
        "guidance_id",
        "company",
        "metric_name",
        "period_kind",
        "period_year",
        "updated_at",
    )
    search_fields = ("guidance_id", "metric_name")


@admin.register(ValuationSnapshot)
class ValuationSnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot_id", "company", "asof", "per", "pbr")
    ordering = ("-asof",)
    search_fields = ("snapshot_id",)
