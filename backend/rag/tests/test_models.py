"""
Django tests for the rag application models.
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone as tz

from rag.models import (
    Company,
    EventFact,
    FactType,
    FinancialStatement,
    Guidance,
    MetricFact,
    PeriodKind,
    RiskFact,
    SourceDocument,
    StatementFact,
    ValuationSnapshot,
)


class CompanyModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            company_id="cmp_test_001",
            name="テスト株式会社",
            name_en="Test Corp",
            listings=[{"country": "JP", "exchange": "TSE", "ticker": "9999"}],
            industries=[{"scheme": "東証33業種", "code": "3700", "name": "情報・通信"}],
        )

    def test_company_str(self):
        self.assertIn("テスト株式会社", str(self.company))
        self.assertIn("cmp_test_001", str(self.company))

    def test_company_fields(self):
        c = Company.objects.get(company_id="cmp_test_001")
        self.assertEqual(c.name, "テスト株式会社")
        self.assertEqual(c.name_en, "Test Corp")
        self.assertEqual(len(c.listings), 1)
        self.assertEqual(c.listings[0]["ticker"], "9999")


class SourceDocumentModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            company_id="cmp_test_002", name="サンプル株式会社"
        )
        self.doc = SourceDocument.objects.create(
            doc_id="doc_test_001",
            kind="IR_DECK",
            title="2025年度 通期 決算概要",
            published_at=tz.now(),
            company=self.company,
        )

    def test_source_document_str(self):
        self.assertIn("2025年度 通期 決算概要", str(self.doc))

    def test_source_document_relation(self):
        self.assertEqual(self.doc.company, self.company)


class MetricFactModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            company_id="cmp_test_003", name="指標テスト株式会社"
        )
        self.fact = MetricFact.objects.create(
            fact_id="fact_abc123",
            company=self.company,
            fact_type=FactType.METRIC,
            asof=tz.now(),
            name="revenue",
            period_kind=PeriodKind.FY,
            period_year=2025,
            metric_value=Decimal("12345000000"),
            metric_unit="JPY_mn",
            fingerprint="abc123",
            evidences=[{"doc_id": "doc_001", "confidence": 0.9}],
        )

    def test_metric_fact_str(self):
        self.assertIn("revenue", str(self.fact))

    def test_metric_fact_fields(self):
        f = MetricFact.objects.get(fact_id="fact_abc123")
        self.assertEqual(f.name, "revenue")
        self.assertEqual(f.period_kind, PeriodKind.FY)
        self.assertEqual(f.period_year, 2025)
        self.assertEqual(f.metric_value, Decimal("12345000000"))


class FinancialStatementModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            company_id="cmp_test_004", name="財務テスト株式会社"
        )
        self.fs = FinancialStatement.objects.create(
            fs_id="fs_test_001",
            company=self.company,
            period_kind=PeriodKind.FY,
            period_year=2025,
            revenue={"amount": "12345000000", "currency": "JPY"},
            operating_income={"amount": "1234500000", "currency": "JPY"},
        )

    def test_financial_statement_str(self):
        self.assertIn("財務テスト株式会社", str(self.fs))

    def test_financial_statement_fields(self):
        fs = FinancialStatement.objects.get(fs_id="fs_test_001")
        self.assertEqual(fs.period_kind, PeriodKind.FY)
        self.assertEqual(fs.period_year, 2025)
        self.assertIsNotNone(fs.revenue)
        self.assertEqual(fs.revenue["currency"], "JPY")


class ValuationSnapshotModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            company_id="cmp_test_005", name="バリュエーションテスト株式会社"
        )
        self.snapshot = ValuationSnapshot.objects.create(
            snapshot_id="snap_test_001",
            company=self.company,
            asof=date(2025, 3, 31),
            per=Decimal("15.5"),
            pbr=Decimal("2.3"),
        )

    def test_valuation_snapshot_str(self):
        self.assertIn("バリュエーションテスト株式会社", str(self.snapshot))

    def test_valuation_snapshot_fields(self):
        snap = ValuationSnapshot.objects.get(snapshot_id="snap_test_001")
        self.assertEqual(snap.asof, date(2025, 3, 31))
        self.assertEqual(snap.per, Decimal("15.5"))
