from orm import db


class ActivationCodeModel(db.Model):
    __tablename__ = "activation_codes"

    id = db.Column(db.Integer, primary_key=True)
    # sha256 of the normalised code
    code_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    # Free text so the owner can tell one handed-out code from another.
    label = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)

    # Set together when redeemed; used_at is what makes a code spent, so it
    # survives the account being deleted and cannot be redeemed a second time.
    used_at = db.Column(db.DateTime, nullable=True)
    used_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
