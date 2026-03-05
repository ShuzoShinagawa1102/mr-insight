"""
Tests for rag.model.glossary domain module.
"""

from django.test import SimpleTestCase

from rag.model.glossary import GlossaryCategory, GlossaryTermEntry, MetricName


class MetricNameEnumTest(SimpleTestCase):
    """MetricName enum の基本動作テスト"""

    def test_metric_name_values_are_snake_case(self):
        for member in MetricName:
            self.assertRegex(
                member.value,
                r"^[a-z][a-z0-9_]*$",
                msg=f"{member.name} の値 '{member.value}' がスネークケースでない",
            )

    def test_key_financial_metrics_exist(self):
        """主要財務指標が MetricName に定義されていること"""
        expected = [
            MetricName.REVENUE,
            MetricName.GROSS_PROFIT,
            MetricName.OPERATING_INCOME,
            MetricName.NET_INCOME,
            MetricName.EBITDA,
            MetricName.TOTAL_ASSETS,
            MetricName.EQUITY,
            MetricName.CFO,
            MetricName.FREE_CASH_FLOW,
            MetricName.ROE,
            MetricName.ROA,
            MetricName.PER,
            MetricName.PBR,
            MetricName.EV_EBITDA,
        ]
        for metric in expected:
            self.assertIn(metric, MetricName)

    def test_metric_name_string_lookup(self):
        """文字列から MetricName を取得できること"""
        self.assertEqual(MetricName("revenue"), MetricName.REVENUE)
        self.assertEqual(MetricName("operating_income"), MetricName.OPERATING_INCOME)

    def test_metric_name_is_str(self):
        """MetricName の値が str のサブクラスであること"""
        self.assertIsInstance(MetricName.REVENUE, str)
        self.assertEqual(MetricName.REVENUE, "revenue")


class GlossaryTermEntryTest(SimpleTestCase):
    """GlossaryTermEntry Pydantic モデルのテスト"""

    def test_create_with_all_fields(self):
        entry = GlossaryTermEntry(
            ja_name="売上高",
            en_name="Net Sales / Revenue",
            category=GlossaryCategory.FINANCIAL_STATEMENT,
            description="企業の主要な収益項目",
        )
        self.assertEqual(entry.ja_name, "売上高")
        self.assertEqual(entry.en_name, "Net Sales / Revenue")
        self.assertEqual(entry.category, GlossaryCategory.FINANCIAL_STATEMENT)

    def test_create_minimal(self):
        entry = GlossaryTermEntry(ja_name="のれん")
        self.assertEqual(entry.ja_name, "のれん")
        self.assertIsNone(entry.en_name)
        self.assertEqual(entry.category, GlossaryCategory.OTHER)

    def test_glossary_category_enum(self):
        self.assertEqual(GlossaryCategory.FINANCIAL_STATEMENT, "FINANCIAL_STATEMENT")
        self.assertEqual(GlossaryCategory.CONSULTING, "CONSULTING")
        self.assertEqual(GlossaryCategory.ESG, "ESG")
