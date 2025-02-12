from orm import db


class FolderModel(db.Model):
    __tablename__ = "folders"

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String, unique=True, nullable=False)
    users = db.relationship(
        "UserModel", back_populates="folders", secondary="usersfolders"
    )
