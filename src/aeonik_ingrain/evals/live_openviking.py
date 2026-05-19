"""Optional live OpenViking comparison harness.

The default eval is deterministic and dependency-free. This module is for
launch-time proof: point it at a running OpenViking server and compare the same
learned-experience scenarios against live resource retrieval.
"""

from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from aeonik_ingrain.evals.comparison import SCENARIOS, _score_output


class OpenVikingLiveError(RuntimeError):
    """Raised when the live OpenViking benchmark cannot run."""


def run_live_openviking_comparison(
    *,
    endpoint: str = "http://127.0.0.1:1933",
    account: str = "default",
    user: str = "default",
    agent: str = "hermes",
    timeout: int = 90,
) -> dict[str, Any]:
    endpoint = endpoint.rstrip("/")
    health = _request_json("GET", f"{endpoint}/health", headers=_headers(account, user, agent), timeout=timeout)
    scenarios: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="ingrain-openviking-live-") as tmp:
        tmp_dir = Path(tmp)
        for scenario in SCENARIOS:
            fixture = tmp_dir / f"{scenario.name}.md"
            fixture.write_text(_scenario_markdown(scenario), encoding="utf-8")
            add_result = _add_resource(
                endpoint=endpoint,
                fixture=fixture,
                account=account,
                user=user,
                agent=agent,
                timeout=timeout,
            )
            search_result = _search(
                endpoint=endpoint,
                query=scenario.query,
                account=account,
                user=user,
                agent=agent,
                timeout=timeout,
            )
            output_parts = [json.dumps(search_result, ensure_ascii=False)]
            read_uris: list[str] = []
            for uri in _candidate_read_uris(search_result):
                read_uris.append(uri)
                output_parts.append(
                    json.dumps(
                        _read(endpoint=endpoint, uri=uri, account=account, user=user, agent=agent, timeout=timeout),
                        ensure_ascii=False,
                    )
                )
            output = "\n".join(output_parts)
            scenarios.append(
                {
                    "scenario": scenario.name,
                    "score": _score_output(output, scenario),
                    "max": 20,
                    "read_uris": read_uris,
                    "output_chars": len(output),
                    "root_uri": _unwrap(add_result).get("root_uri", ""),
                }
            )

    total = sum(item["score"] for item in scenarios)
    return {
        "name": "Live OpenViking Resource Retrieval Comparison",
        "endpoint": endpoint,
        "health": health,
        "score": total,
        "max": len(scenarios) * 20,
        "scenarios": scenarios,
        "note": (
            "This is a live OpenViking resource-retrieval benchmark. It does not "
            "exercise OpenViking long-term memory extraction unless the server is "
            "configured with model credentials."
        ),
    }


def format_live_openviking_comparison(result: dict[str, Any]) -> str:
    lines = [
        result.get("name", "Live OpenViking Comparison"),
        "",
        f"Endpoint: {result.get('endpoint', '')}",
        f"Score: {result.get('score', 0)}/{result.get('max', 0)}",
        "",
        "Scenario breakdown:",
    ]
    for item in result.get("scenarios", []):
        uris = ", ".join(item.get("read_uris", [])[:3]) or "none"
        lines.append(f"- {item['scenario']}: {item['score']}/{item['max']} read={uris}")
    if result.get("note"):
        lines.extend(["", result["note"]])
    return "\n".join(lines).strip()


def _scenario_markdown(scenario: Any) -> str:
    events = "\n".join(f"- {event}" for event in scenario.events)
    return (
        f"# Ingrain Benchmark Scenario: {scenario.name}\n\n"
        f"Query: {scenario.query}\n\n"
        "## Events\n"
        f"{events}\n"
    )


def _candidate_read_uris(search_result: dict[str, Any], limit: int = 5) -> list[str]:
    result = _unwrap(search_result)
    if not isinstance(result, dict):
        return []
    candidates: list[str] = []
    for bucket in ("resources", "memories", "skills", "results"):
        for item in result.get(bucket, []) or []:
            uri = item.get("uri", "")
            if not uri:
                continue
            if uri.endswith(("/.abstract.md", "/.overview.md", "/.read.md", "/.full.md")):
                continue
            if uri.endswith(".md") and uri not in candidates:
                candidates.append(uri)
            if len(candidates) >= limit:
                return candidates
    return candidates


def _add_resource(*, endpoint: str, fixture: Path, account: str, user: str, agent: str, timeout: int) -> dict[str, Any]:
    temp_id = _upload_temp(endpoint=endpoint, fixture=fixture, account=account, user=user, agent=agent, timeout=timeout)
    payload = {
        "source_name": fixture.name,
        "temp_file_id": temp_id,
        "reason": "Aeonik Ingrain live comparison fixture",
        "wait": True,
        "timeout": timeout,
    }
    return _request_json(
        "POST",
        f"{endpoint}/api/v1/resources",
        payload=payload,
        headers=_headers(account, user, agent),
        timeout=timeout,
    )


def _upload_temp(*, endpoint: str, fixture: Path, account: str, user: str, agent: str, timeout: int) -> str:
    boundary = f"----ingrain-{uuid.uuid4().hex}"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{fixture.name}"\r\n'.encode(),
            b"Content-Type: text/markdown\r\n\r\n",
            fixture.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    headers = _headers(account, user, agent, content_type=f"multipart/form-data; boundary={boundary}")
    data = _request_json(
        "POST",
        f"{endpoint}/api/v1/resources/temp_upload",
        body=body,
        headers=headers,
        timeout=timeout,
    )
    result = _unwrap(data)
    temp_id = result.get("temp_file_id", "") if isinstance(result, dict) else ""
    if not temp_id:
        raise OpenVikingLiveError("OpenViking temp_upload did not return temp_file_id")
    return temp_id


def _search(*, endpoint: str, query: str, account: str, user: str, agent: str, timeout: int) -> dict[str, Any]:
    return _request_json(
        "POST",
        f"{endpoint}/api/v1/search/find",
        payload={"query": query, "top_k": 10, "mode": "fast"},
        headers=_headers(account, user, agent),
        timeout=timeout,
    )


def _read(*, endpoint: str, uri: str, account: str, user: str, agent: str, timeout: int) -> dict[str, Any]:
    url = f"{endpoint}/api/v1/content/read?{urlencode({'uri': uri})}"
    return _request_json("GET", url, headers=_headers(account, user, agent), timeout=timeout)


def _request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int,
) -> dict[str, Any]:
    data = body
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
    except HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise OpenVikingLiveError(f"OpenViking HTTP {exc.code} at {url}: {text}") from exc
    except URLError as exc:
        raise OpenVikingLiveError(f"Could not reach OpenViking at {url}: {exc.reason}") from exc
    if not text:
        return {}
    try:
        data_json = json.loads(text)
    except json.JSONDecodeError as exc:
        raise OpenVikingLiveError(f"OpenViking returned non-JSON at {url}: {text[:500]}") from exc
    if isinstance(data_json, dict) and data_json.get("status") == "error":
        raise OpenVikingLiveError(json.dumps(data_json, ensure_ascii=False))
    return data_json


def _headers(account: str, user: str, agent: str, *, content_type: str = "application/json") -> dict[str, str]:
    return {
        "Content-Type": content_type,
        "Accept": "application/json",
        "X-OpenViking-Account": account,
        "X-OpenViking-User": user,
        "X-OpenViking-Agent": agent,
    }


def _unwrap(value: Any) -> Any:
    if isinstance(value, dict) and "result" in value:
        return value["result"]
    return value
