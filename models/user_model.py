from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100))
    bio = db.Column(db.Text)