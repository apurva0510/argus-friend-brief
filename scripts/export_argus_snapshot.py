from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_SYMBOLS = ("NVDA", "VRT", "CEG")


def display_value(value: Any, kind: str = "plain") -> str:
    if value is None:
        return "Not available"
    if kind == "percent":
        return f"{float(value) * 100:+.1f}%"
    if kind == "money":
        amount = float(value)
        for divisor, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
            if abs(amount) >= divisor:
                return f"${amount / divisor:.1f}{suffix}"
        return f"${amount:,.0f}"
    if kind == "multiple":
        return f"{float(value):.1f}x"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def fact(
    symbol: str,
    category: str,
    name: str,
    value: Any,
    as_of: Any,
    source: str,
    *,
    kind: str = "plain",
    label: str | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    date_part = str(as_of or "undated").replace(" ", "T")
    return {
        "id": f"{symbol}.{category}.{name}.{date_part}",
        "label": label or name.replace("_", " ").title(),
        "value": value,
        "display_value": display_value(value, kind),
        "as_of": str(as_of) if as_of else None,
        "source": source,
        "url": url,
    }


def rows(connection: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> list[dict]:
    return [dict(row) for row in connection.execute(sql, params).fetchall()]


def export_company(connection: sqlite3.Connection, symbol: str) -> dict[str, Any]:
    company = connection.execute(
        "SELECT id, symbol, name, sector, industry FROM companies WHERE symbol = ?",
        (symbol,),
    ).fetchone()
    if company is None:
        raise ValueError(f"Unknown Argus symbol: {symbol}")
    company = dict(company)
    company_id = company["id"]
    symbol = company["symbol"]
    facts: list[dict[str, Any]] = []

    metrics = rows(
        connection,
        """
        SELECT date, return_1d, return_1w, return_1m, return_3m, return_ytd,
               rsi_14, drawdown_52w, distance_from_50dma, distance_from_200dma,
               relative_return_vs_qqq_3m, volatility_20d, opportunity_score
        FROM daily_metrics WHERE company_id = ? ORDER BY date DESC LIMIT 2
        """,
        (company_id,),
    )
    percent_metrics = {
        "return_1d",
        "return_1w",
        "return_1m",
        "return_3m",
        "return_ytd",
        "drawdown_52w",
        "distance_from_50dma",
        "distance_from_200dma",
        "relative_return_vs_qqq_3m",
        "volatility_20d",
    }
    for position, metric_row in enumerate(metrics):
        category = "metric_latest" if position == 0 else "metric_previous"
        for name, value in metric_row.items():
            if name == "date":
                continue
            facts.append(
                fact(
                    symbol,
                    category,
                    name,
                    value,
                    metric_row["date"],
                    "Argus daily_metrics",
                    kind="percent" if name in percent_metrics else "plain",
                )
            )

    signal_rows = rows(
        connection,
        """
        SELECT date, sentiment_proxy_7d, news_relevance_7d, corr_nvda_60d,
               corr_hyperscaler_60d, earnings_sensitivity, power_signal, capex_signal
        FROM signal_daily WHERE company_id = ? ORDER BY date DESC LIMIT 1
        """,
        (company_id,),
    )
    for signal_row in signal_rows:
        for name, value in signal_row.items():
            if name != "date":
                facts.append(
                    fact(symbol, "signal", name, value, signal_row["date"], "Argus signal_daily")
                )

    fundamentals = rows(
        connection,
        """
        SELECT as_of_date, market_cap, forward_pe, price_to_sales, ev_to_sales,
               ev_to_ebitda, revenue_growth, gross_margin, operating_margin,
               free_cash_flow, provider
        FROM fundamentals_snapshot WHERE company_id = ?
        ORDER BY as_of_date DESC, id DESC LIMIT 1
        """,
        (company_id,),
    )
    money_fields = {"market_cap", "free_cash_flow"}
    multiple_fields = {"forward_pe", "price_to_sales", "ev_to_sales", "ev_to_ebitda"}
    percent_fields = {"revenue_growth", "gross_margin", "operating_margin"}
    for fundamental in fundamentals:
        for name, value in fundamental.items():
            if name in {"as_of_date", "provider"}:
                continue
            kind = (
                "money"
                if name in money_fields
                else "multiple"
                if name in multiple_fields
                else "percent"
                if name in percent_fields
                else "plain"
            )
            facts.append(
                fact(
                    symbol,
                    "fundamental",
                    name,
                    value,
                    fundamental["as_of_date"],
                    f"Argus fundamentals_snapshot ({fundamental['provider']})",
                    kind=kind,
                )
            )

    valuation_rows = rows(
        connection,
        """
        SELECT as_of_date, metric_name, company_value, peer_median,
               premium_discount_pct, valuation_flag
        FROM valuation_peer_snapshot
        WHERE company_id = ? AND as_of_date = (
            SELECT MAX(as_of_date) FROM valuation_peer_snapshot WHERE company_id = ?
        ) AND peer_group_type = 'sector'
        ORDER BY metric_name LIMIT 6
        """,
        (company_id, company_id),
    )
    for valuation in valuation_rows:
        metric_name = valuation["metric_name"]
        for name in ("company_value", "peer_median", "premium_discount_pct", "valuation_flag"):
            kind = "percent" if name == "premium_discount_pct" else "plain"
            facts.append(
                fact(
                    symbol,
                    "valuation",
                    f"{metric_name}_{name}",
                    valuation[name],
                    valuation["as_of_date"],
                    "Argus valuation_peer_snapshot",
                    kind=kind,
                )
            )

    thesis = connection.execute(
        """
        SELECT bull_thesis, bear_thesis, key_kpis, thesis_status, conviction_score,
               last_reviewed_date
        FROM investment_theses WHERE company_id = ?
        """,
        (company_id,),
    ).fetchone()
    if thesis:
        thesis = dict(thesis)
        for name in ("bull_thesis", "bear_thesis", "key_kpis", "thesis_status", "conviction_score"):
            facts.append(
                fact(
                    symbol,
                    "thesis",
                    name,
                    thesis[name],
                    thesis["last_reviewed_date"],
                    "Argus deterministic investment_theses",
                )
            )

    themes = rows(
        connection,
        """
        SELECT t.name, e.exposure_score, e.as_of_date
        FROM company_theme_exposure e JOIN themes t ON t.id = e.theme_id
        WHERE e.company_id = ? ORDER BY e.exposure_score DESC LIMIT 3
        """,
        (company_id,),
    )
    for index, theme in enumerate(themes, start=1):
        facts.append(
            fact(
                symbol,
                "theme",
                f"theme_{index}",
                f"{theme['name']} ({theme['exposure_score']:.1f}/5)",
                theme["as_of_date"],
                "Argus company_theme_exposure",
            )
        )

    news = rows(
        connection,
        """
        SELECT n.published_at, n.title, n.url, n.source_name
        FROM news_items n JOIN news_mentions m ON m.news_id = n.id
        WHERE m.company_id = ? ORDER BY n.published_at DESC LIMIT 5
        """,
        (company_id,),
    )
    for index, item in enumerate(news, start=1):
        facts.append(
            fact(
                symbol,
                "news",
                f"headline_{index}",
                item["title"],
                item["published_at"],
                item["source_name"] or "Argus news feed",
                url=item["url"],
            )
        )

    filings = rows(
        connection,
        """
        SELECT filing_date, form, filing_detail_url
        FROM sec_filings WHERE company_id = ? ORDER BY filing_date DESC LIMIT 3
        """,
        (company_id,),
    )
    for index, filing in enumerate(filings, start=1):
        facts.append(
            fact(
                symbol,
                "filing",
                f"filing_{index}",
                filing["form"],
                filing["filing_date"],
                "SEC EDGAR via Argus",
                url=filing["filing_detail_url"],
            )
        )

    for index, evidence in enumerate(facts, start=1):
        evidence["id"] = f"{symbol}.E{index:03d}"

    return {
        "symbol": symbol,
        "name": company["name"],
        "sector": company["sector"],
        "industry": company["industry"],
        "facts": facts,
    }


def export_snapshot(database: Path, symbols: list[str]) -> dict[str, Any]:
    database = database.resolve()
    uri = f"file:{database}?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        companies = [export_company(connection, symbol.upper()) for symbol in symbols]
    finally:
        connection.close()
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_label": "Argus read-only SQLite export",
        "companies": companies,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a sanitized Argus demo snapshot")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/demo_snapshot.json"))
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    args = parser.parse_args()

    snapshot = export_snapshot(args.database, args.symbols)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Exported {len(snapshot['companies'])} companies to {args.output}")


if __name__ == "__main__":
    main()
