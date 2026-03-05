import re
import hashlib
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from agents import Agent, Runner, function_tool


# =========================================================
# みえるマン：共通ドメインモデル（必要な分だけ残す）
# =========================================================

Id = str

class PeriodKind(str, Enum):
    FY = "FY"
    Q = "Q"
    H1 = "H1"
    H2 = "H2"
    TTM = "TTM"

class MoneyCurrency(str, Enum):
    JPY = "JPY"
    USD = "USD"
    EUR = "EUR"

class Unit(str, Enum):
    COUNT = "count"
    PERCENT = "percent"
    JPY = "JPY"
    USD = "USD"
    PERSON = "person"
    YEN_MN = "JPY_mn"

class Period(BaseModel):
    kind: PeriodKind
    year: int = Field(ge=1900, le=2100)
    quarter: Optional[int] = Field(default=None, ge=1, le=4)

    @field_validator("quarter")
    @classmethod
    def quarter_required_for_q(cls, v, info):
        kind = info.data.get("kind")
        if kind == PeriodKind.Q and v is None:
            raise ValueError("kind=Q の場合 quarter が必要")
        if kind != PeriodKind.Q and v is not None:
            raise ValueError("kind!=Q の場合 quarter は不要")
        return v

class MetricValue(BaseModel):
    value: Decimal
    unit: Unit
    raw: Optional[str] = None

class SourceKind(str, Enum):
    EDINET = "EDINET"
    TDNET = "TDNET"
    IR_DECK = "IR_DECK"
    TRANSCRIPT = "TRANSCRIPT"
    NEWS = "NEWS"
    BLOG = "BLOG"
    SNS = "SNS"
    MARKET = "MARKET"
    OTHER = "OTHER"

class SourceDocument(BaseModel):
    id: Id
    kind: SourceKind
    title: str
    published_at: datetime
    url: Optional[HttpUrl] = None
    company_id: Optional[Id] = None
    blob_ref: Optional[str] = None
    extractor_version: Optional[str] = None

class Evidence(BaseModel):
    doc_id: Id
    locator: Dict[str, Any] = Field(default_factory=dict)
    quote: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)

class Company(BaseModel):
    id: Id
    name: str

class FactType(str, Enum):
    METRIC = "METRIC"
    EVENT = "EVENT"
    STATEMENT = "STATEMENT"
    RISK = "RISK"

class FactBase(BaseModel):
    id: Id
    company_id: Id
    fact_type: FactType
    asof: datetime
    evidences: List[Evidence] = Field(default_factory=list)
    fingerprint: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class MetricFact(FactBase):
    fact_type: Literal[FactType.METRIC] = FactType.METRIC
    name: str
    period: Optional[Period] = None
    value: MetricValue
    yoy: Optional[Decimal] = None
    qoq: Optional[Decimal] = None

class ExtractedItemType(str, Enum):
    TABLE_ROW = "TABLE_ROW"
    SENTENCE = "SENTENCE"
    KEY_VALUE = "KEY_VALUE"

class ExtractedItem(BaseModel):
    id: Id
    doc_id: Id
    item_type: ExtractedItemType
    text: str
    structure: Dict[str, Any] = Field(default_factory=dict)
    evidence: Evidence

class NormalizationResult(BaseModel):
    company_id: Id
    facts: List[MetricFact] = Field(default_factory=list)
    source_doc_ids: List[Id] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================
# ツール（責務分割：Extract / Normalize / Verify / Commit）
# =========================================================

def _stable_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

@function_tool
def register_source_document(
    kind: str,
    title: str,
    published_at_iso: str,
    url: str = "",
    blob_ref: str = "",
) -> dict:
    """
    資料メタ登録（本番はDB保存）
    戻り値は SourceDocument 相当の dict（doc_id だけでなく後続で使う）
    """
    doc_id = f"doc_{abs(hash((kind, title, published_at_iso))) % 10_000_000}"
    doc = SourceDocument(
        id=doc_id,
        kind=SourceKind(kind),
        title=title,
        published_at=datetime.fromisoformat(published_at_iso),
        url=url or None,
        blob_ref=blob_ref or None,
        extractor_version="demo_v1",
    )
    return doc.model_dump()

@function_tool
def load_document_text(doc: dict, raw_text: str = "") -> str:
    """
    本文ロード（本番は doc['blob_ref'] から）
    デモでは raw_text をそのまま返す
    """
    _ = doc["id"]
    return raw_text

@function_tool
def extract_items(doc: dict, text: str) -> List[dict]:
    """
    Extract層：テキストを最小単位へ分解（推論しない）
    """
    doc_id = doc["id"]
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: List[dict] = []
    for i, ln in enumerate(lines[:400]):
        out.append(
            ExtractedItem(
                id=f"{doc_id}_item_{i}",
                doc_id=doc_id,
                item_type=ExtractedItemType.SENTENCE,
                text=ln,
                structure={"line_no": i},
                evidence=Evidence(doc_id=doc_id, locator={"line_no": i}, quote=ln[:240], confidence=0.6),
            ).model_dump()
        )
    return out

@function_tool
def resolve_company(extracted_items: List[dict]) -> dict:
    """
    Entity resolution：会社同定（本番はDB照合）
    """
    text_all = "\n".join([it.get("text", "") for it in extracted_items])
    m = re.search(r"([一-龥ぁ-んァ-ンA-Za-z0-9・\s]{2,30}株式会社)", text_all)
    name = m.group(1).strip() if m else "UNKNOWN_COMPANY"
    company_id = f"cmp_{abs(hash(name)) % 10_000_000}"
    return Company(id=company_id, name=name).model_dump()

@function_tool
def map_items_to_candidate_facts(company: dict, extracted_items: List[dict]) -> List[dict]:
    """
    Candidate生成：候補Factを作る（まだ確定しない）
    - デモでは「売上」「営業利益」だけ雑に拾う
    """
    company_id = company["id"]
    candidates: List[dict] = []

    patterns = [
        ("revenue", r"(売上高|売上)\s*[:：]?\s*([0-9][0-9,\.]*)", Unit.YEN_MN),
        ("operating_income", r"(営業利益)\s*[:：]?\s*([0-9][0-9,\.]*)", Unit.YEN_MN),
    ]

    for it in extracted_items:
        t = it.get("text", "")
        for name, pat, unit in patterns:
            m = re.search(pat, t)
            if not m:
                continue
            v = Decimal(m.group(2).replace(",", ""))
            candidates.append(
                {
                    "name": name,
                    "value": {"value": str(v), "unit": unit.value, "raw": t},
                    "evidence": it["evidence"],
                    "asof_iso": datetime.utcnow().isoformat(),
                    # period は本番で推定する（FY/Q抽出）
                    "period": None,
                }
            )
    return candidates

@function_tool
def normalize_candidates_to_common_model(company: dict, doc: dict, candidates: List[dict]) -> dict:
    """
    Normalize層：候補 -> 共通モデル（MetricFact / NormalizationResult）
    - fingerprint を必ず付ける
    """
    company_id = company["id"]
    facts: List[MetricFact] = []

    for c in candidates:
        name = c["name"]
        value = c["value"]
        asof = datetime.fromisoformat(c["asof_iso"])

        # fingerprint：会社 + fact名 + 主要値(文字列) + doc_id（必要に応じて period も含める）
        fp_src = f"{company_id}|{name}|{value['value']}|{value['unit']}|{doc['id']}"
        fingerprint = _stable_hash(fp_src)

        fact = MetricFact(
            id=f"fact_{fingerprint}",
            company_id=company_id,
            asof=asof,
            evidences=[Evidence(**c["evidence"])],
            fingerprint=fingerprint,
            name=name,
            value=MetricValue(
                value=Decimal(value["value"]),
                unit=Unit(value["unit"]),
                raw=value.get("raw"),
            ),
        )
        facts.append(fact)

    result = NormalizationResult(
        company_id=company_id,
        facts=facts,
        source_doc_ids=[doc["id"]],
    )
    # Pydanticで一度validateして、壊れてたらここで落とす（Gate A）
    NormalizationResult.model_validate(result.model_dump())
    return result.model_dump()

@function_tool
def verify_before_commit(result: dict, min_confidence: float = 0.55) -> dict:
    """
    Verify層（Gate B）：DB確定前の最低限チェック
    - Evidenceがあるか
    - confidence閾値
    - fingerprint重複（同一result内）
    """
    facts = result.get("facts", [])
    issues: List[str] = []

    fps = set()
    for f in facts:
        fp = f.get("fingerprint")
        if not fp:
            issues.append("fingerprint_missing")
        elif fp in fps:
            issues.append(f"fingerprint_duplicate:{fp}")
        fps.add(fp)

        evs = f.get("evidences", [])
        if not evs:
            issues.append(f"evidence_missing:{f.get('id')}")
        else:
            conf = evs[0].get("confidence", 0.0)
            if conf < min_confidence:
                issues.append(f"low_confidence:{f.get('id')} conf={conf}")

    verdict = "pass" if not issues else "fail"
    return {"verdict": verdict, "issues": issues}

@function_tool
def commit_to_store(company: dict, doc: dict, result: dict) -> str:
    """
    Commit層：永続化（このツールは CommitAgent だけが持つ）
    """
    # 本番：
    # - Company upsert
    # - SourceDocument upsert
    # - Fact upsert (fingerprint unique)
    return f"committed: company_id={company['id']} doc_id={doc['id']} facts={len(result.get('facts', []))}"

@function_tool
def emit_ingest_summary(company: dict, doc: dict, result: dict, verify: dict) -> str:
    facts = result.get("facts", [])
    lines = [
        f"Company: {company.get('name')} ({company.get('id')})",
        f"Doc: {doc.get('title')} ({doc.get('id')}) kind={doc.get('kind')}",
        f"Facts: {len(facts)}",
        f"Verify: {verify.get('verdict')} issues={len(verify.get('issues', []))}",
    ]
    for f in facts[:5]:
        lines.append(f"- {f.get('name')} = {f.get('value', {}).get('value')} [{f.get('value', {}).get('unit')}] fp={f.get('fingerprint')}")
    if verify.get("issues"):
        lines.append("Issues:")
        lines.extend([f"  - {x}" for x in verify["issues"][:20]])
    return "\n".join(lines)


# =========================================================
# エージェント構成（データ整備まで）
# - 書き込み権限(Commit)を分離する
# =========================================================

# Layer 1: Extract
ExtractAgent = Agent(
    name="Extract Agent",
    instructions="""
あなたは抽出担当。
資料本文を最小単位（ExtractedItem）へ分割し、推論はしない。
""",
    tools=[register_source_document, load_document_text, extract_items],
)

# Layer 1.5: Entity Resolution
EntityResolutionAgent = Agent(
    name="Entity Resolution Agent",
    instructions="""
あなたは会社同定担当。
ExtractedItem を使い、会社名を推定して Company を返す。
不明な場合は UNKNOWN_COMPANY で進める。
""",
    tools=[resolve_company],
)

# Layer 2: Candidate -> Normalize
SchemaMapperAgent = Agent(
    name="Schema Mapper Agent",
    instructions="""
あなたは候補Fact生成〜共通モデル正規化担当。
1) map_items_to_candidate_facts で候補を作る
2) normalize_candidates_to_common_model で NormalizationResult を生成する
fingerprint を必ず付ける。失敗したら候補生成からやり直す。
""",
    tools=[map_items_to_candidate_facts, normalize_candidates_to_common_model],
)

# Layer 3: Verify (read-only)
VerifierAgent = Agent(
    name="Verifier Agent",
    instructions="""
あなたはDB確定前の検証担当（書き込み禁止）。
verify_before_commit を呼び、verdict と issues を返す。
""",
    tools=[verify_before_commit],
)

# Layer 4: Commit (write-only)
CommitAgent = Agent(
    name="Commit Agent",
    instructions="""
あなたは永続化担当。書き込み以外はしない。
verdict=pass のときだけ commit_to_store を呼ぶ。
""",
    tools=[commit_to_store],
)

# Orchestrator: 全体制御（ここは“順番を守る”のが役割）
IngestOrchestrator = Agent(
    name="Ingest Orchestrator",
    instructions="""
あなたはデータ整備のオーケストレーター。
必ず次の順番でサブタスクを実行し、最後に summary を返す。

手順：
A) Extract Agent で doc登録→本文ロード→抽出
B) Entity Resolution Agent で company決定
C) Schema Mapper Agent で候補→正規化
D) Verifier Agent で検証
E) verdict=pass の場合のみ Commit Agent で永続化
F) emit_ingest_summary で結果をまとめる

注意：
- 自分で commit_to_store を直接呼ばない（CommitAgentのみ）。
- 検証が fail の場合は commit しない。summary に issues を出す。
""",
    tools=[emit_ingest_summary],
)


# =========================================================
# デモ実行
# =========================================================

if __name__ == "__main__":
    raw_text = """
    〇〇株式会社 2025年度 通期 決算概要
    売上高 12,345
    営業利益 1,234
    """

    # ここでは簡易に「オーケストレーターが全部やった体」で、
    # 実際は Runner.run_sync で各Agentを順に回す。
    #
    # Agents SDK の呼び分けは環境次第なので、まずは設計と責務分離を固める目的。

    # 1) Extract
    doc = register_source_document(
        kind="IR_DECK",
        title="2025年度 通期 決算概要",
        published_at_iso=datetime.utcnow().isoformat(),
        url="",
        blob_ref="",
    )
    text = load_document_text(doc, raw_text=raw_text)
    items = extract_items(doc, text)

    # 2) Resolve company
    company = resolve_company(items)

    # 3) Candidate + Normalize
    candidates = map_items_to_candidate_facts(company, items)
    result = normalize_candidates_to_common_model(company, doc, candidates)

    # 4) Verify
    verify = verify_before_commit(result)

    # 5) Commit (only if pass)
    commit_msg = ""
    if verify["verdict"] == "pass":
        commit_msg = commit_to_store(company, doc, result)

    # 6) Summary
    summary = emit_ingest_summary(company, doc, result, verify)
    print(summary)
    if commit_msg:
        print(commit_msg)