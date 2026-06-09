from models.user_model import db

class Booking(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    ride_id = db.Column(db.Integer)
    status = db.Column(
    db.String(20),
    default='Active'
)