from flask_jwt_extended import create_access_token, create_refresh_token


def issue_tokens(user):
    """A fresh access/refresh pair for `user`, as handed out at login.

    `uk` ties both tokens to this exact account; see app.py's user_lookup_loader.
    """
    claims = {"uk": user.token_key}
    return {
        "access_token": create_access_token(identity=str(user.id), fresh=True, additional_claims=claims),
        "refresh_token": create_refresh_token(identity=str(user.id), additional_claims=claims),
    }
