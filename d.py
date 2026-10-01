def get_logged_in_user():
    user_name = ""
    user_email = ""

    try:
        principal = request.headers.get("X-MS-CLIENT-PRINCIPAL")

        if principal:
            decoded = base64.b64decode(principal).decode("utf-8")
            principal_data = json.loads(decoded)

            claims = {
                claim.get("typ"): claim.get("val")
                for claim in principal_data.get("claims", [])
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
                or claims.get(
                    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
                )
                or ""
            )

        # fallback
        if not user_email:
            user_email = request.headers.get(
                "X-MS-CLIENT-PRINCIPAL-NAME", ""
            )

    except Exception as e:
        logger.error("Error reading Easy Auth user: %s", str(e))

    return user_name, user_email
