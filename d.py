import base64
import json
import re


def get_logged_in_user():
    try:
        principal = request.headers.get("X-MS-CLIENT-PRINCIPAL")

        # Localhost / Easy Auth header unavailable
        if not principal:
            return "", ""

        decoded = base64.b64decode(principal).decode("utf-8")
        data = json.loads(decoded)

        claims = {
            claim.get("typ"): claim.get("val")
            for claim in data.get("claims", [])
        }

        user_name = (
            claims.get("name")
            or claims.get(
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
            )
            or ""
        )

        user_email = (
            claims.get("preferred_username")
            or claims.get("email")
            or claims.get("upn")
            or request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME", "")
        )

        return user_name, user_email

    except Exception as e:
        print("Easy Auth error:", e)

        # IMPORTANT: login problem should not break chatbot
        return "", ""


def clean_text(text):
    try:
        if text is None:
            return ""

        text = str(text)

        # Remove only control characters
        text = re.sub(
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',
            '',
            text
        )

        return text.strip()

    except Exception as e:
        print("Clean text error:", e)

        # IMPORTANT: cleaning problem should not break chatbot
        return str(text) if text is not None else ""
