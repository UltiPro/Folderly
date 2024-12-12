from orm import db


class BlocklistModel(db.Model):
    __tablename__ = "blocklist"

    token = db.Column(db.String, primary_key=True)
