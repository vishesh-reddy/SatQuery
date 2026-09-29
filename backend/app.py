import os
import uuid

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory
)

from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from agent import run_satquery_agent

from hindsight_memory import (
    initialize_memory,
    retain_correction
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)


# ============================================================
# CONFIGURATION
# ============================================================

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


# ============================================================
# FILE VALIDATION
# ============================================================

def allowed_file(filename):

    if "." not in filename:
        return False

    extension = (
        filename
        .rsplit(".", 1)[1]
        .lower()
    )

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "success": True,

        "status": "healthy",

        "service": "SatQuery AI"

    })


# ============================================================
# ANALYZE SATELLITE IMAGE
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    try:

        # ----------------------------------------------------
        # CHECK IMAGE
        # ----------------------------------------------------

        if "image" not in request.files:

            return jsonify({

                "success": False,

                "error":
                    "No satellite image was provided."

            }), 400


        image = request.files["image"]


        if image.filename == "":

            return jsonify({

                "success": False,

                "error":
                    "No image was selected."

            }), 400


        if not allowed_file(
            image.filename
        ):

            return jsonify({

                "success": False,

                "error":
                    "Unsupported image type. "
                    "Use JPG, JPEG, PNG, or WEBP."

            }), 400


        # ----------------------------------------------------
        # QUESTION
        # ----------------------------------------------------

        question = (
            request.form.get(
                "question",
                ""
            )
            .strip()
        )


        if not question:

            return jsonify({

                "success": False,

                "error":
                    "Please enter a question."

            }), 400


        # ----------------------------------------------------
        # SAVE IMAGE
        # ----------------------------------------------------

        original_name = secure_filename(
            image.filename
        )


        unique_name = (
            f"{uuid.uuid4().hex}_"
            f"{original_name}"
        )


        image_path = os.path.join(
            UPLOAD_DIR,
            unique_name
        )


        image.save(
            image_path
        )


        print()
        print(
            f"[UPLOAD] {unique_name}"
        )


        # ----------------------------------------------------
        # RUN SATQUERY AGENT
        # ----------------------------------------------------

        result = run_satquery_agent(
            image_path=image_path,
            question=question
        )


        return jsonify({

            "success": True,

            "answer":
                result["answer"],

            "memories_used":
                result["memories_used"],

            "memory_saved":
                result["memory_saved"]

        })


    except Exception as error:

        print()
        print("=" * 65)
        print("[ANALYZE ERROR]")
        print(str(error))
        print("=" * 65)

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ============================================================
# ANALYST CORRECTION
# ============================================================

@app.route(
    "/correct",
    methods=["POST"]
)
def correct_analysis():

    try:

        print()
        print("=" * 65)
        print("SATQUERY ANALYST CORRECTION")
        print("=" * 65)


        # ----------------------------------------------------
        # READ JSON
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )


        if not data:

            print("[CORRECTION] No JSON data received.")

            return jsonify({

                "success": False,

                "error":
                    "No correction data was provided."

            }), 400


        # ----------------------------------------------------
        # EXTRACT DATA
        # ----------------------------------------------------

        question = str(
            data.get(
                "question",
                ""
            )
        ).strip()


        ai_analysis = str(
            data.get(
                "ai_analysis",
                ""
            )
        ).strip()


        correction = str(
            data.get(
                "correction",
                ""
            )
        ).strip()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not question:

            print(
                "[CORRECTION] Missing original question."
            )

            return jsonify({

                "success": False,

                "error":
                    "Original question is missing."

            }), 400


        if not ai_analysis:

            print(
                "[CORRECTION] Missing AI analysis."
            )

            return jsonify({

                "success": False,

                "error":
                    "Original AI analysis is missing."

            }), 400


        if not correction:

            print(
                "[CORRECTION] Empty correction."
            )

            return jsonify({

                "success": False,

                "error":
                    "Please enter a correction."

            }), 400


        # ----------------------------------------------------
        # DISPLAY WHAT IS BEING SAVED
        # ----------------------------------------------------

        print()
        print("Original question:")
        print(question)

        print()
        print("Original AI analysis:")
        print(ai_analysis[:1000])

        print()
        print("Human correction:")
        print(correction)


        # ----------------------------------------------------
        # SAVE TO HINDSIGHT
        # ----------------------------------------------------

        print()
        print(
            "[HINDSIGHT] Saving analyst correction..."
        )


        saved = retain_correction(
            question=question,
            ai_analysis=ai_analysis,
            correction=correction
        )


        # ----------------------------------------------------
        # CHECK RESULT
        # ----------------------------------------------------

        if not saved:

            print()
            print(
                "[HINDSIGHT ERROR] "
                "retain_correction() returned False."
            )

            return jsonify({

                "success": False,

                "error":
                    "Hindsight rejected or failed to "
                    "store the correction. "
                    "Check the Flask terminal for the "
                    "Hindsight error."

            }), 500


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print()
        print(
            "[HINDSIGHT] Analyst correction stored successfully."
        )

        print("=" * 65)
        print()


        return jsonify({

            "success": True,

            "message":
                "Correction saved to Hindsight.",

            "memory_saved": True

        })


    except Exception as error:

        print()
        print("=" * 65)
        print("[CORRECTION ERROR]")
        print(str(error))
        print("=" * 65)


        return jsonify({

            "success": False,

            "error":
                "Correction could not be saved: "
                + str(error)

        }), 500


# RUN SERVER
# ============================================================

# Gunicorn imports this module instead of executing __main__.
# Initialize Hindsight during worker startup.
initialize_memory()


if __name__ == "__main__":

    print()
    print("=" * 65)
    print("                 SATQUERY AI")
    print("=" * 65)

    print("Server: http://127.0.0.1:5000")
    print("Frontend: served by Flask")
    print("Vision: Qwen 3.8 27B via Groq")
    print("Memory: Hindsight")

    print("=" * 65)
    print()

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
