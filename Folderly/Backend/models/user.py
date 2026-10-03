import secrets

from orm import db


def new_token_key():
    return secrets.token_hex(16)


class UserModel(db.Model):
    __tablename__ = "users"

    # Never reuse a deleted account's id.
    __table_args__ = {"sqlite_autoincrement": True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    # Registration is open, but a new account can do nothing with folders or
    # files until an activation code is redeemed. Clearing this flag later takes
    # the access away again without deleting the account.
    active = db.Column(db.Boolean, nullable=False, default=False)

    # Goes into every token and is checked on every request (app.py's
    # user_lookup_loader). It ties a token to this account, not just to an id
    # that another account could hold after a database reset. Setting a new
    # value logs the account out everywhere.
    token_key = db.Column(db.String(32), nullable=False, default=new_token_key)

    owned_folders = db.relationship("FolderModel", backref="owner", foreign_keys="FolderModel.owner_id")
