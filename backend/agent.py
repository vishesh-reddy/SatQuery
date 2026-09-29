from datetime import datetime

from vision import analyze_satellite_image

from hindsight_memory import (
    recall_memories,
    retain_experience
)


# ============================================================
# SATQUERY AGENT
# ============================================================

def run_satquery_agent(
    image_path,
    question
):

    print()
    print("=" * 65)
    print("SATQUERY AGENT")
    print("=" * 65)

    print(
        f"Question: {question}"
    )


    # ========================================================
    # STEP 1 — RECALL PREVIOUS EXPERIENCE
    # ========================================================

    print(
        "[AGENT] Searching long-term memory..."
    )

    memory_query = f"""
Remote sensing analysis related to:

{question}

Look for previous:

- satellite observations
- sensor information
- flood observations
- weather observations
- analyst corrections
- previous interpretations
- previous conclusions
"""

    memories = recall_memories(
        query=memory_query,
        limit=5
    )


    if memories:

        memory_context = "\n\n".join(
            f"- {memory}"
            for memory in memories
        )

        print(
            f"[AGENT] Recalled {len(memories)} memories."
        )

    else:

        memory_context = ""

        print(
            "[AGENT] No relevant memories found."
        )


    # ========================================================
    # STEP 2 — ANALYZE CURRENT IMAGE
    # ========================================================

    print(
        "[AGENT] Inspecting satellite image..."
    )

    analysis = analyze_satellite_image(
        image_path=image_path,
        question=question,
        memory_context=memory_context
    )


    # ========================================================
    # STEP 3 — CREATE EXPERIENCE FOR HINDSIGHT
    # ========================================================

    timestamp = datetime.utcnow().isoformat()

    experience = f"""
SATQUERY REMOTE-SENSING EXPERIENCE

Timestamp:
{timestamp}

User question:
{question}

Current analysis:
{analysis}

Historical memory retrieved:
{memory_context if memory_context else "None"}

IMPORTANT:

This memory represents a previous SatQuery analysis.

Future analyses should use this as historical context,
not as unquestionable ground truth.

If an analyst later corrects this interpretation,
the correction should take precedence over this
previous observation.
"""


    # ========================================================
    # STEP 4 — STORE EXPERIENCE
    # ========================================================

    print(
        "[AGENT] Storing experience in Hindsight..."
    )

    memory_saved = retain_experience(
        experience
    )


    if memory_saved:

        print(
            "[HINDSIGHT] Experience stored successfully."
        )

    else:

        print(
            "[HINDSIGHT] Experience was not stored."
        )


    # ========================================================
    # STEP 5 — RETURN RESULT
    # ========================================================

    return {
        "answer": analysis,
        "memories_used": memories,
        "memory_saved": memory_saved
    }