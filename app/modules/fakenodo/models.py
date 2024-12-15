from app import db

class Deposition(db.Model):
    __tablename__ = 'deposition'
    id = db.Column(db.Integer, primary_key=True)
    dep_metadata = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(50), nullable=True, default="draft")
    doi = db.Column(db.String(250), unique=True, nullable=True)
    def repr(self):
        return f'Deposition<{self.id}>'