"""
DRF API tests for the rag application views.
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone as tz
from rest_framework import status
from rest_framework.test import APIClient

from rag.models import (
    Company,
    FinancialStatement,
    Guidance,
    MetricFact,
    PeriodKind,
    FactType,
    ValuationSnapshot,
)


class CompanyViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            company_id="cmp_view_001",
            name="APIテスト株式会社",
            name_en="API Test Corp",
        )

    def test_list_companies(self):
        response = self.client.get("/api/companies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["company_id"], "cmp_view_001")

    def test_retrieve_company(self):
        response = self.client.get(f"/api/companies/{self.company.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "APIテスト株式会社")
        self.assertEqual(data["name_en"], "API Test Corp")

    def test_retrieve_nonexistent_company(self):
        response = self.client.get("/api/companies/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MetricFactViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            company_id="cmp_view_002", name="指標APIテスト株式会社"
        )
        self.fact = MetricFact.objects.create(
            fact_id="fact_view_001",
            company=self.company,
            fact_type=FactType.METRIC,
            asof=tz.now(),
            name="revenue",
            period_kind=PeriodKind.FY,
            period_year=2025,
            metric_value=Decimal("9876000000"),
            metric_unit="JPY_mn",
        )

    def test_list_metric_facts(self):
        response = self.client.get("/api/facts/metrics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fact_id"], "fact_view_001")

    def test_retrieve_metric_fact(self):
        response = self.client.get(f"/api/facts/metrics/{self.fact.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "revenue")
        self.assertEqual(data["period_kind"], PeriodKind.FY)


class FinancialStatementViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            company_id="cmp_view_003", name="財務APIテスト株式会社"
        )
        self.fs = FinancialStatement.objects.create(
            fs_id="fs_view_001",
            company=self.company,
            period_kind=PeriodKind.FY,
            period_year=2025,
            revenue={"amount": "5000000000", "currency": "JPY"},
        )

    def test_list_financial_statements(self):
        response = self.client.get("/api/financials/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fs_id"], "fs_view_001")

    def test_retrieve_financial_statement(self):
        response = self.client.get(f"/api/financials/{self.fs.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["period_year"], 2025)
        self.assertEqual(data["revenue"]["currency"], "JPY")
