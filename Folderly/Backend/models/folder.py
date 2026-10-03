from orm import db


class FolderModel(db.Model):
    __tablename__ = "folders"
    # Gives every new folder an id that has never been used before. Reusing a
    # deleted folder's id would hand a new folder whatever still points at the
    # old one, such as a share row left behind.
    __table_args__ = {"sqlite_autoincrement": True}

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String, unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # How someone the folder is shared with addresses it (`share=` in requests).
    # Random rather than the row id so it cannot be enumerated and says nothing
    # about how many shares exist; stable across renames because it is not
    # derived from the path. Assigned the first time the folder is shared.
    share_token = db.Column(db.String(16), unique=True, nullable=True, index=True)

    shares = db.relationship(
        "FolderShareModel",
        back_populates="folder",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
