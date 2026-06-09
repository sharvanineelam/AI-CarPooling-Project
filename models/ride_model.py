from models.user_model import db

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    source = db.Column(db.String(100))
    destination = db.Column(db.String(100))

    date = db.Column(db.String(50))
    time = db.Column(db.String(50))

    seats = db.Column(db.Integer)

    price = db.Column(db.Integer)

    description = db.Column(db.String(500))

    vehicle = db.Column(db.String(100))

    pickup = db.Column(db.String(200))

    gender = db.Column(db.String(50))

    phone = db.Column(db.String(20))

    user_id = db.Column(db.Integer)