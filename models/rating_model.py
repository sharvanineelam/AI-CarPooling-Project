from models.user_model import db

class Rating(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=False
    )

    ride_id = db.Column(
        db.Integer,
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    review = db.Column(
        db.String(500),
        nullable=True
    )