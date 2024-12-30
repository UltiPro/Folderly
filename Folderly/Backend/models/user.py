from orm import db


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    ban = db.Column(db.Boolean, default=False, nullable=False)
    folders = db.relationship(
        "FolderModel", back_populates="users", secondary="usersfolders"
    )
