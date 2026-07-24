import json
import re
from urllib import error, request

from django.conf import settings

from investigator.services.routing import QuestionLanguage


class GenerationUnavailable(RuntimeError):
    """Raised when a safe model-generated refinement cannot be produced."""


def _safe_model_answer(answer, *, allowed_context, facts):
    if not answer or len(answer) > 4000:
        return False
    forbidden = ("fraud", "corruption", "embezzled", "घोटाला", "भ्रष्टाचार")
    lowered = answer.casefold()
    if any(term in lowered for term in forbidden):
        return False
    allowed_numbers = set(re.findall(r"[\d\u0966-\u096f][\d\u0966-\u096f,.\/]*", allowed_context))
    answer_numbers = set(re.findall(r"[\d\u0966-\u096f][\d\u0966-\u096f,.\/]*", answer))
    if not answer_numbers.issubset(allowed_numbers):
        return False
    if facts and facts["contract"]["status"] == "unknown":
        if any(term in lowered for term in ("was awarded to", "winning contractor is")):
            return False
    return True


def refine_with_ollama(question, language, route, facts, citations, deterministic_answer):
    if language == QuestionLanguage.ROMANIZED_NEPALI:
        raise GenerationUnavailable("Romanized Nepali uses the verified deterministic composer.")
    context = {
        "route": str(route),
        "language": str(language),
        "structured_facts": facts,
        "evidence": citations,
        "verified_draft": deterministic_answer,
    }
    context_json = json.dumps(context, ensure_ascii=False, default=str)
    system_prompt = (
        "You are Budget Darpan, an evidence-bounded civic investigator. Rewrite the verified "
        "draft clearly in the requested language. Use only supplied facts and evidence. Preserve "
        "every uncertainty. Never turn a tender estimate into an award or payment. Never accuse "
        "anyone of wrongdoing. Do not add names, numbers, dates, or claims. Return plain text only."
    )
    payload = json.dumps(
        {
            "model": settings.OLLAMA_CHAT_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Question: {question}\nVerified context: {context_json}",
                },
            ],
            "options": {"temperature": 0.1, "num_predict": 420},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    http_request = request.Request(
        f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=settings.OLLAMA_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
        answer = result.get("message", {}).get("content", "").strip()
    except (error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise GenerationUnavailable("Ollama chat is unavailable.") from exc

    allowed_context = f"{question}\n{context_json}"
    if not _safe_model_answer(answer, allowed_context=allowed_context, facts=facts):
        raise GenerationUnavailable("The model response failed evidence safety checks.")
    return answer
