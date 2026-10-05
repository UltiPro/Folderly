import hashlib
import secrets
from functools import wraps

from flask_smorest import abort
from flask_jwt_extended import get_jwt_identity

from orm import db

from models.user import UserModel

# No I, L, O, 0 or 1: those are the characters people get wrong.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 16
GROUP_SIZE = 4


def new_code():
    """A fresh code, e.g. `K7M2-PX94-TB3H-QR8F`.

    `secrets`, not `random` - this is a credential. 16 characters of a 31
    character alphabet is about 79 bits, far past anything guessable, which is
    why redeeming needs no rate limit of its own.
    """
    raw = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
    return "-".join(raw[i : i + GROUP_SIZE] for i in range(0, CODE_LENGTH, GROUP_SIZE))


def normalize(code):
    """Strip the formatting people add or drop, so `k7m2 px94...` still matches."""
    return "".join(character for character in code.upper() if character in ALPHABET)


def hash_code(code):
    return hashlib.sha256(normalize(code).encode()).hexdigest()


def active_required(fn):
    """Refuse the request unless the caller's account has been activated.

    Every endpoint that touches folders, files or storage needs this - an
    unactivated account may only manage the account itself. It is separate from
    `jwt_required`, which answers "who is this", not "may they use the app".
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = db.session.get(UserModel, int(get_jwt_identity()))
        if user is None or not user.active:
            abort(403, message="Account is not activated. Enter an activation code first.")
        return fn(*args, **kwargs)

    return wrapper
