from orm import db

# Weakest first. Each role includes everything the ones before it allow.
#   read  view and download
#   add   also create folders and upload files that do not exist yet
#   edit  also overwrite, rename and delete
# "add" has to exclude overwriting: replacing a file with an empty one of the
# same name deletes it just as surely as DELETE does, so a role that may
# overwrite but not delete promises something it cannot keep.
ROLES = ("read", "add", "edit")


class FolderShareModel(db.Model):
    """One folder shared with one user, with the role they were given."""

    __tablename__ = "folder_shares"
    __table_args__ = (db.UniqueConstraint("folder_id", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(8), nullable=False, default="read")

    user = db.relationship("UserModel")
    folder = db.relationship("FolderModel", back_populates="shares")
