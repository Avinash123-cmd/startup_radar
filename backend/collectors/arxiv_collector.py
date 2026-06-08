from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime

import httpx

from collectors.base import guarded_collect
from intelligence.types import CollectorBatch, RawSignal

SEARCH_TERMS = [
    "artificial intelligence",
    "large language models",
    "AI agents",
    "multimodal AI",
    "code generation",
    "speech synthesis",
    "browser automation",
]

ARXIV_API_URL = "http://export.arxiv.org/api/query"


def collect_arxiv(db=None, settings: dict | None = None) -> CollectorBatch:
    settings = settings or {}
    limit = min(int(settings.get("collectors_limit", 20) or 20), 50)
    started_at = datetime.utcnow()

    def _collect() -> list[RawSignal]:
        return _run_async(_collect_arxiv_async(SEARCH_TERMS, limit))

    return guarded_collect("arxiv", _collect, started_at)


async def _collect_arxiv_async(search_terms: list[str], limit: int) -> list[RawSignal]:
    records: list[RawSignal] = []
    seen: set[str] = set()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for index, term in enumerate(search_terms):
            if index:
                await asyncio.sleep(3.0)
            xml_text = await _query_arxiv(client, term, limit)
            for record in _parse_arxiv_response(xml_text):
                if record.external_id in seen:
                    continue
                seen.add(record.external_id)
                records.append(record)
    return records


async def _query_arxiv(client: httpx.AsyncClient, search_term: str, limit: int) -> str:
    response = await client.get(
        ARXIV_API_URL,
        params={
            "search_query": f'all:"{search_term}"',
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": limit,
        },
        timeout=25.0,
    )
    response.raise_for_status()
    return response.text


def _parse_arxiv_response(xml_content: str) -> list[RawSignal]:
    root = ET.fromstring(xml_content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    records: list[RawSignal] = []

    for entry in root.findall("atom:entry", ns):
        id_url = _text(entry.find("atom:id", ns))
        if not id_url:
            continue
        arxiv_id = _extract_arxiv_id(id_url)
        title = " ".join(_text(entry.find("atom:title", ns)).split())
        abstract = " ".join(_text(entry.find("atom:summary", ns)).split())
        published_at = _parse_datetime(_text(entry.find("atom:published", ns)))
        authors = [
            _text(author.find("atom:name", ns))
            for author in entry.findall("atom:author", ns)
            if _text(author.find("atom:name", ns))
        ]
        pdf_url = _pdf_url(entry, ns, arxiv_id)
        records.append(
            RawSignal(
                source="arxiv",
                external_id=arxiv_id,
                title=f"[arXiv] {title}",
                description=f"Authors: {', '.join(authors)}. Abstract: {abstract}",
                url=f"https://arxiv.org/abs/{arxiv_id}",
                engagement_score=0,
                published_at=published_at,
                raw_payload={
                    "authors": authors,
                    "pdf_url": pdf_url,
                    "abstract": abstract,
                },
            )
        )
    return records


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def _text(node) -> str:
    return node.text.strip() if node is not None and node.text else ""


def _extract_arxiv_id(url: str) -> str:
    value = url.split("/abs/")[-1].split("/pdf/")[-1]
    for index in range(len(value) - 1, -1, -1):
        if value[index] == "v" and value[index + 1 :].isdigit():
            return value[:index]
    return value


def _parse_datetime(value: str) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.utcnow()


def _pdf_url(entry, ns: dict[str, str], arxiv_id: str) -> str:
    for link in entry.findall("atom:link", ns):
        if link.attrib.get("type") == "application/pdf" or link.attrib.get("title") == "pdf":
            return link.attrib.get("href") or f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
