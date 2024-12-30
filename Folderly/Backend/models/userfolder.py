from orm import db


class UserFolderModel(db.Model):
    __tablename__ = "usersfolders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    folder_id = db.Column(db.Integer, db.ForeignKey("folders.id"))
