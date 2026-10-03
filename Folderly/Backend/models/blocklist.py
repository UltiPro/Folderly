from orm import db


class BlocklistModel(db.Model):
    __tablename__ = "blocklist"

    token = db.Column(db.String, primary_key=True)
    # Naive UTC, matching what SQLite stores. A revoked token only has to stay
    # here until it would have expired on its own; see resources/user.py's logout,
    # which prunes everything past this point.
    expires_at = db.Column(db.DateTime, nullable=False)
