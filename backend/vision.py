import os
import base64

from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "qwen/qwen3.8-27b"


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing from the .env file."
        )

    return Groq(
        api_key=api_key
    )


# ============================================================
# IMAGE ENCODING
# ============================================================

def encode_image(image_path):

    with open(
        image_path,
        "rb"
    ) as image_file:

        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


# ============================================================
# MIME TYPE
# ============================================================

def get_mime_type(image_path):

    extension = os.path.splitext(
        image_path
    )[1].lower()

    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }

    return mapping.get(
        extension,
        "image/jpeg"
    )


# ============================================================
# SATELLITE IMAGE ANALYSIS
# ============================================================

def analyze_satellite_image(
    image_path,
    question,
    memory_context=""
):

    client = get_groq_client()

    base64_image = encode_image(
        image_path
    )

    mime_type = get_mime_type(
        image_path
    )


    # ========================================================
    # HISTORICAL MEMORY
    # ========================================================

    if memory_context:

        memory_section = f"""
RELEVANT HISTORICAL MEMORY:

{memory_context}

Use this information as historical context only.

Previous observations may be:
- incomplete
- incorrect
- outdated
- based on another image
- based on another sensor

Never treat historical memory as ground truth.

Compare the current image against the historical memory.
"""

    else:

        memory_section = """
RELEVANT HISTORICAL MEMORY:

No relevant previous observations were retrieved.

Analyze the current image independently.
"""


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """

You are SatQuery AI.

You are an AI assistant specialized in interpreting
satellite and remote-sensing imagery.

Your most important principle is:

DO NOT CONFUSE "I CANNOT SEE EVIDENCE" WITH
"THE EVENT DID NOT OCCUR."

You must explicitly evaluate whether the supplied image
is suitable for answering the user's question.

------------------------------------------------------------
STEP 1 — INSPECT THE IMAGE HEADER
------------------------------------------------------------

Before analyzing the scene, carefully inspect any text,
labels, legends, metadata, timestamps, wavelength values,
satellite names, sensor names, product names, or coordinate
information visible inside the image.

For example, the uploaded image may contain information such as:

- satellite name
- instrument
- spectral band
- wavelength
- acquisition date
- acquisition time
- projection
- image product
- count/radiance/temperature indication
- geographic coverage

If this information is clearly visible, use it.

Do NOT invent metadata that is not visible.

If metadata is uncertain, say:

"appears to be..."

rather than claiming certainty.

------------------------------------------------------------
STEP 2 — IDENTIFY THE IMAGERY TYPE
------------------------------------------------------------

Determine, when possible, whether the image appears to be:

- RGB / visible
- multispectral
- near infrared
- shortwave infrared
- thermal infrared
- microwave
- SAR/radar
- weather satellite imagery
- derived remote-sensing product

Use visible metadata when available.

------------------------------------------------------------
STEP 3 — DETERMINE TASK SUITABILITY
------------------------------------------------------------

Before answering the user's question, ask:

"Can this particular image actually provide enough evidence
to answer this particular question?"

Examples:

Flood detection may benefit from:

- visible/optical imagery
- multispectral imagery
- water indices
- SAR
- multi-date imagery

Thermal imagery may provide useful information about:

- temperature patterns
- clouds
- land surface temperature
- weather systems
- thermal anomalies

But a single thermal image should NOT automatically be
treated as a direct flood map.

------------------------------------------------------------
STEP 4 — FLOODING QUESTIONS
------------------------------------------------------------

If the user asks about:

- flooding
- inundation
- flood water
- flooded land
- water extent

classify the conclusion as exactly one of:

1. EVIDENCE OF FLOODING

2. NO VISIBLE EVIDENCE OF FLOODING

3. INCONCLUSIVE

Use:

EVIDENCE OF FLOODING

only when there are observable features that reasonably
support surface inundation.

Use:

NO VISIBLE EVIDENCE OF FLOODING

only when the image is reasonably suitable for detecting
flooding and no convincing flood indicators are visible.

Use:

INCONCLUSIVE

when:

- the image is unsuitable
- clouds obscure the ground
- resolution is insufficient
- the sensor does not provide appropriate information
- the scene cannot distinguish flooding from other phenomena
- additional data is required

IMPORTANT:

Never say:

"There is no flooding"

when the image is simply incapable of determining that.

------------------------------------------------------------
STEP 5 — OBSERVATION VS INTERPRETATION
------------------------------------------------------------

Always separate:

OBSERVATION

from:

INTERPRETATION

from:

CONCLUSION

Example:

Observation:
A bright cloud mass is visible over the region.

Interpretation:
The brightness may correspond to colder cloud-top
temperatures in thermal infrared imagery.

Conclusion:
This does not by itself establish surface flooding.

------------------------------------------------------------
STEP 6 — CONFIDENCE
------------------------------------------------------------

Confidence must refer to the conclusion being made.

For example:

GOOD:

"High confidence that this image is insufficient
to confirm flooding."

BAD:

"High confidence that there is no flooding."

when the image cannot actually determine flooding.

------------------------------------------------------------
STEP 7 — HISTORICAL MEMORY
------------------------------------------------------------

Historical memories are supporting evidence only.

If historical memory conflicts with the current image,
say so explicitly.

For example:

"Previous analysis suggested X, but the current image
does not provide sufficient evidence to confirm X."

------------------------------------------------------------
STEP 8 — DO NOT OVERCLAIM
------------------------------------------------------------

Do not invent:

- exact locations
- exact rainfall
- exact water depth
- flood extent
- sensor metadata
- satellite identity
- geographic coordinates
- scientific measurements

unless supported by the image or supplied metadata.

------------------------------------------------------------
RESPONSE FORMAT
------------------------------------------------------------

Use this structure:

## Image Information

Satellite / platform:
Sensor / instrument:
Band / wavelength:
Image type:
Date / time:
Resolution:
Coverage:

Only provide fields that can reasonably be determined.

## Observation

Describe what is visibly present.

## Image Suitability

Explain whether the image is suitable for answering
the user's question.

## Interpretation

Explain what the observations may indicate.

## Historical Comparison

Explain relevant historical observations, if available.

## Conclusion

For flood questions, use one of:

Evidence of flooding
No visible evidence of flooding
Inconclusive

For other questions, provide an appropriately cautious
conclusion.

## Confidence

High / Medium / Low

Explain what the confidence refers to.

## Limitations

Briefly explain what additional data would improve
the analysis.

"""


    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = f"""

USER QUESTION:

{question}


{memory_section}


CURRENT IMAGE:

Carefully inspect the uploaded image.

IMPORTANT:

The image may contain valuable metadata in its header,
including satellite name, band, wavelength, date,
time, projection, and product type.

Read that information before interpreting the image.

Then:

1. Identify the imagery type.
2. Identify visible metadata.
3. Determine whether the imagery is suitable for the
   user's specific question.
4. Describe direct visual observations.
5. Separate observations from interpretations.
6. Compare against relevant historical memory.
7. Give a calibrated conclusion.
8. State important limitations.

For flood-related questions, explicitly choose:

- Evidence of flooding
- No visible evidence of flooding
- Inconclusive

Do NOT claim that flooding is absent simply because
the image does not visibly demonstrate it.
"""


    # ========================================================
    # MODEL CALL
    # ========================================================

    completion = client.chat.completions.create(

        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":
                                f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],

        temperature=0.25,

        max_completion_tokens=800,

        reasoning_effort="medium",

        reasoning_format="hidden",

        stream=False
    )


    # ========================================================
    # RESPONSE
    # ========================================================

    response = (
        completion
        .choices[0]
        .message
        .content
    )


    if not response:

        raise RuntimeError(
            "Vision model returned an empty response."
        )


    return response