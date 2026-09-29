import os
import asyncio
from datetime import datetime, timezone

from hindsight_client import Hindsight


BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "satquery")
BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)


def _create_client():
    api_key = os.getenv("HINDSIGHT_API_KEY")
    if not api_key:
        raise RuntimeError("HINDSIGHT_API_KEY is not set.")

    return Hindsight(
        base_url=BASE_URL,
        api_key=api_key
    )


async def _retain_async(content):
    client = _create_client()
    try:
        return await client.aretain(
            bank_id=BANK_ID,
            content=content
        )
    finally:
        await client.aclose()


async def _recall_async(query):
    client = _create_client()
    try:
        return await client.arecall(
            bank_id=BANK_ID,
            query=query
        )
    finally:
        await client.aclose()


async def _create_bank_async():
    client = _create_client()
    try:
        return await client.acreate_bank(
            bank_id=BANK_ID,
            name="SatQuery AI",
            background=(
                "Long-term memory for a remote-sensing AI agent. "
                "Stores satellite observations, historical analyses, "
                "analyst corrections, and outcomes so future analyses "
                "can use relevant past experience."
            )
        )
    finally:
        await client.aclose()


def _run_async(coroutine):
    """Run native Hindsight async APIs from our synchronous Flask routes."""
    return asyncio.run(coroutine)


# ============================================================
# INITIALIZE MEMORY BANK
# ============================================================

def initialize_memory():
    try:
        _run_async(_create_bank_async())
        print(f"[HINDSIGHT] Memory bank ready: {BANK_ID}")
    except Exception as error:
        message = str(error).lower()

        if (
            "already exists" in message
            or "409" in message
            or "conflict" in message
        ):
            print(f"[HINDSIGHT] Memory bank already exists: {BANK_ID}")
        else:
            print(
                "[HINDSIGHT] Bank initialization notice: "
                f"{type(error).__name__}: {error}"
            )

    return True


# ============================================================
# RECALL
# ============================================================

def recall_memories(query, limit=5):
    if not query or not str(query).strip():
        return []

    try:
        result = _run_async(
            _recall_async(str(query).strip())
        )

        memories = []
        results = getattr(result, "results", None) or []

        for memory in results[:limit]:
            text = getattr(memory, "text", None)

            if text is None and isinstance(memory, dict):
                text = memory.get("text") or memory.get("content")

            if text:
                memories.append(str(text))

        print(
            f"[HINDSIGHT] Recalled {len(memories)} relevant memories."
        )
        return memories

    except Exception as error:
        print("[HINDSIGHT ERROR] Recall failed:")
        print(
            f"[HINDSIGHT ERROR] {type(error).__name__}: {error}"
        )
        return []


# ============================================================
# RETAIN NORMAL EXPERIENCE
# ============================================================

def retain_experience(content):
    if not content or not str(content).strip():
        print("[HINDSIGHT ERROR] Cannot store empty experience.")
        return False

    try:
        _run_async(
            _retain_async(str(content).strip())
        )

        print("[HINDSIGHT] Experience stored successfully.")
        return True

    except Exception as error:
        print("[HINDSIGHT ERROR] Experience retain failed:")
        print(
            f"[HINDSIGHT ERROR] {type(error).__name__}: {error}"
        )
        return False


# ============================================================
# RETAIN ANALYST CORRECTION
# ============================================================

def retain_correction(question, ai_analysis, correction):
    if not question or not str(question).strip():
        print(
            "[HINDSIGHT ERROR] Correction rejected: question is empty."
        )
        return False

    if not correction or not str(correction).strip():
        print(
            "[HINDSIGHT ERROR] Correction rejected: correction is empty."
        )
        return False

    timestamp = datetime.now(timezone.utc).isoformat()

    correction_memory = f"""
SATQUERY ANALYST CORRECTION

Memory type:
HIGH-PRIORITY HUMAN FEEDBACK

Timestamp:
{timestamp}

Original user question:
{str(question).strip()}

Original SatQuery analysis:
{str(ai_analysis or '').strip()}

Analyst correction:
{str(correction).strip()}

IMPORTANT MEMORY RULE:

This is explicit analyst feedback about a previous SatQuery interpretation.
Future analyses should consider this correction when the current image,
question, sensor, location, date, or phenomenon is relevant.

Do not blindly apply the correction to unrelated images, sensors,
locations, dates, or phenomena. Always compare this historical feedback
against the current image and current evidence.
""".strip()

    try:
        print(
            "[HINDSIGHT] Sending analyst correction using native "
            "Hindsight async API..."
        )

        _run_async(
            _retain_async(correction_memory)
        )

        print(
            "[HINDSIGHT] Analyst correction stored successfully."
        )
        return True

    except Exception as error:
        print("[HINDSIGHT ERROR] Correction retain failed:")
        print(
            f"[HINDSIGHT ERROR] {type(error).__name__}: {error}"
        )

        if "event loop" in str(error).lower():
            print(
                "[HINDSIGHT ERROR] Hindsight async API still encountered "
                "an event-loop problem. Check the installed SDK version."
            )

        return False
