from models.user_model import db

class Notification(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    message = db.Column(
        db.String(255)
    )
    is_read = db.Column(
    db.Boolean,
    default=False
)

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )