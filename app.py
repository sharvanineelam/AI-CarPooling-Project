from flask import Flask, render_template, request, redirect, session, flash

from werkzeug.security import generate_password_hash, check_password_hash

from models.user_model import db, User
from models.ride_model import Ride
from models.booking_model import Booking
from sqlalchemy import func
from models.notification_model import Notification
from models.rating_model import Rating
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import random
from datetime import datetime
import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)
load_dotenv()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carpool.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Load trained model
knn_model = joblib.load("ML/ride_match_model.pkl")

# Encoders
pickup_encoder = LabelEncoder()
destination_encoder = LabelEncoder()
time_encoder = LabelEncoder()

vehicle_encoder = LabelEncoder()

# Training dataset load
dataset = pd.read_csv("ML/dataset.csv")

pickup_encoder.fit(dataset["pickup"])
destination_encoder.fit(dataset["destination"])
time_encoder.fit(dataset["time_slot"])
vehicle_encoder.fit(dataset["vehicle_type"])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test_email')
def test_email():

    msg = Message(
        'AI Car Pooling Test Email',
        sender=app.config['MAIL_USERNAME'],
        recipients=[app.config['MAIL_USERNAME']]
    )

    msg.body = "Email Notifications Working Successfully 🚀"

    mail.send(msg)

    return "Email Sent Successfully!"
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:

            flash("Email already exists!")

            return redirect('/register')

        user = User(
            name=name,
            email=email,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session['user_id'] = user.id
            session['user_name'] = user.name
            session['email'] = user.email

            return redirect('/dashboard')

        flash("Invalid Email or Password")

    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form['email']

        user = User.query.filter_by(email=email).first()

        if user:

            otp = random.randint(100000, 999999)
            session['otp_time'] = datetime.now().timestamp()

            session['reset_otp'] = str(otp)
            session['reset_email'] = email

            msg = Message(
                'Password Reset OTP',
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )

            msg.body = f"Your OTP is: {otp}"

            mail.send(msg)

            return redirect('/verify_otp')

        flash("Email not found")

    return render_template('forgot_password.html')
@app.route('/resend_otp')
def resend_otp():

    email = session.get('reset_email')

    if not email:
        return redirect('/forgot_password')

    otp = random.randint(100000, 999999)

    session['reset_otp'] = str(otp)
    session['otp_time'] = datetime.now().timestamp()

    msg = Message(
        'Password Reset OTP',
        sender=app.config['MAIL_USERNAME'],
        recipients=[email]
    )

    msg.body = f"Your new OTP is: {otp}"

    mail.send(msg)

    flash("A new OTP has been sent to your email.")

    return redirect('/verify_otp')
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():

    if not session.get('otp_verified'):
        return redirect('/forgot_password')

    if request.method == 'POST':

        new_password = generate_password_hash(
            request.form['password']
        )

        user = User.query.filter_by(
            email=session['reset_email']
        ).first()

        if user:

            user.password = new_password

            db.session.commit()

            session.pop('reset_otp', None)
            session.pop('reset_email', None)
            session.pop('otp_verified', None)
            session.pop('otp_time', None)

            flash("Password Updated Successfully!")

            return redirect('/login')

    return render_template('reset_password.html')
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():

    if request.method == 'POST':

        entered_otp = request.form['otp']
        otp_time = session.get('otp_time')

        if otp_time:

            current_time = datetime.now().timestamp()

            if current_time - otp_time > 120:

                flash("OTP has expired. Please request a new OTP.")
                session.pop('otp_time', None)
                session.pop('reset_otp', None)

                return redirect('/forgot_password')

        if entered_otp == session.get('reset_otp'):

            session['otp_verified'] = True

            return redirect('/reset_password')

        flash("Invalid OTP")

    return render_template('verify_otp.html')

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    total_rides = Ride.query.count()

    total_bookings = Booking.query.filter_by(
        user_id=session['user_id']
    ).count()

    active_rides = Ride.query.filter(
        Ride.seats > 0
    ).count()

    full_rides = Ride.query.filter(
        Ride.seats == 0
    ).count()

    recent_rides = Ride.query.order_by(
        Ride.id.desc()
    ).limit(5).all()

    avg_price = db.session.query(
        func.avg(Ride.price)
    ).scalar() or 0

    avg_price = round(avg_price, 0)

    most_used_vehicle = db.session.query(
        Ride.vehicle
    ).group_by(
        Ride.vehicle
    ).order_by(
        func.count(Ride.vehicle).desc()
    ).first()

    if most_used_vehicle:
        most_used_vehicle = most_used_vehicle[0]
    else:
        most_used_vehicle = "N/A"

    popular_route = db.session.query(
        Ride.source,
        Ride.destination
    ).group_by(
        Ride.source,
        Ride.destination
    ).order_by(
        func.count().desc()
    ).first()

    if popular_route:
        popular_route = (
            f"{popular_route[0]} → {popular_route[1]}"
        )
    else:
        popular_route = "N/A"

    booking_success_rate = 0

    if total_rides > 0:
        booking_success_rate = min(
            round((total_bookings / total_rides) * 100, 1),
            100
        )

    active_bookings = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Active'
    ).count()

    upcoming_rides = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Active'
    ).count()

    completed_bookings = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Completed'
    ).count()

    cancelled_bookings = Booking.query.filter_by(
        user_id=session['user_id'],
        status='Cancelled'
    ).count()

    return render_template(
        'dashboard.html',
        total_rides=total_rides,
        total_bookings=total_bookings,
        active_rides=active_rides,
        full_rides=full_rides,
        recent_rides=recent_rides,
        booking_success_rate=booking_success_rate,
        active_bookings=active_bookings,
        completed_bookings=completed_bookings,
        cancelled_bookings=cancelled_bookings,
        upcoming_rides=upcoming_rides,
        avg_price=avg_price,
        most_used_vehicle=most_used_vehicle,
        popular_route=popular_route
    )
        


@app.route('/post_ride', methods=['GET', 'POST'])
def post_ride():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        seats = int(request.form['seats'])
        price = int(request.form['price'])

        if seats <= 0:

            flash("Seats should be greater than 0")

            return redirect('/post_ride')

        if price <= 0:

            flash("Price should be greater than 0")

            return redirect('/post_ride')

        ride = Ride(

            source=request.form['source'],
            destination=request.form['destination'],

            date=request.form['date'],
            time=request.form['time'],

            seats=seats,

            price=price,

            description=request.form['description'],

            vehicle=request.form['vehicle'],

            pickup=request.form['pickup'],

            gender=request.form['gender'],

            phone=request.form['phone'],

            user_id=session['user_id']
        )

        db.session.add(ride)

        db.session.commit()
        msg = Message(
    'Ride Posted Successfully',
    sender=app.config['MAIL_USERNAME'],
    recipients=[app.config['MAIL_USERNAME']]
)

        msg.body = f"""
Hi,

Your ride has been posted successfully.

Route: {ride.source} → {ride.destination}
Date: {ride.date}
Time: {ride.time}

Thank you for using AI Car Pooling 🚗
"""

        mail.send(msg)
        notification = Notification(
                user_id=session['user_id'],
                message="🚗 Your ride has been posted successfully."
            )

        db.session.add(notification)
        db.session.commit()
        return redirect('/search_rides')
    return render_template('post_ride.html')

@app.route('/search_rides')
def search_rides():

    source = request.args.get('source')
    destination = request.args.get('destination')
    max_price = request.args.get('max_price')
    min_seats = request.args.get('min_seats')
    vehicle = request.args.get('vehicle')
    gender = request.args.get('gender')

    rides = Ride.query

    if source:
        rides = rides.filter(
            Ride.source.ilike(f"%{source}%")
        )

    if destination:
        rides = rides.filter(
            Ride.destination.ilike(f"%{destination}%")
        )

    if max_price:
        rides = rides.filter(
            Ride.price <= int(max_price)
        )

    if min_seats:
        rides = rides.filter(
            Ride.seats >= int(min_seats)
        )

    if vehicle:
        rides = rides.filter(
            Ride.vehicle.ilike(f"%{vehicle}%")
        )

    if gender and gender != "Any":
        rides = rides.filter(
            Ride.gender.ilike(f"%{gender}%")
        )

    rides = rides.all()

    city_distances = {
        ("Hyderabad", "Mumbai"): 710,
        ("Hyderabad", "Bangalore"): 570,
        ("Hyderabad", "Chennai"): 630,
        ("Hyderabad", "Delhi"): 1550,
        ("Mumbai", "Delhi"): 1400,
        ("Mumbai", "Bangalore"): 980,
        ("Bangalore", "Chennai"): 350,
        ("Delhi", "Chennai"): 2200
    }

    from datetime import datetime

    for ride in rides:

        route = (ride.source, ride.destination)
        distance = city_distances.get(route, 300)

        estimated_time = round(distance / 60)

        if distance > 1000:
            traffic = "High"
        elif distance > 500:
            traffic = "Moderate"
        else:
            traffic = "Low"

        if distance > 1000:
            suggestion = "Start before 6:00 AM due to long-distance travel."
        elif distance > 500:
            suggestion = "Best to start before 7:00 AM for smoother travel."
        else:
            suggestion = "Flexible departure time recommended."

        ride.trip_summary = {
            "distance": distance,
            "time": estimated_time,
            "traffic": traffic,
            "suggestion": suggestion
        }

        ride.ai_assistant = {
            "departure": suggestion,
            "traffic": traffic,
            "duration": f"{estimated_time} Hours"
        }

        score = 50
        expected_price = distance * 5

        if ride.price <= expected_price:
            score += 25

        if ride.seats >= 3:
            score += 15

        if ride.vehicle in ["Car", "SUV"]:
            score += 10

        ride.ai_score = min(score, 100)

        reasons = []

        if ride.price <= expected_price:
            reasons.append("Affordable Fare")

        if ride.seats >= 3:
            reasons.append("More Seats Available")

        if ride.vehicle in ["Car", "SUV"]:
            reasons.append("Preferred Vehicle")

        if score >= 80:
            reasons.append("Highly Recommended")

        ride.recommendation_reasons = reasons

        trust_score = 40

        if ride.seats >= 3:
            trust_score += 20

        if ride.vehicle in ["Car", "SUV"]:
            trust_score += 20

        if ride.price <= expected_price:
            trust_score += 20

        ride.trust_score = min(trust_score, 100)
        if ride.trust_score >= 90:
            ride.badge = "🏆 Top Driver"
        elif ride.trust_score >= 70:
            ride.badge = "⭐ Reliable Driver"
        else:
            ride.badge = "🚗 Standard Driver"

        explanation = []

        if ride.price <= expected_price:
            explanation.append(
                "Fare is within the recommended range"
            )

        if ride.seats >= 3:
            explanation.append(
                "Sufficient seats are available"
            )

        if ride.vehicle in ["Car", "SUV"]:
            explanation.append(
                "Preferred vehicle type is available"
            )

        if score >= 80:
            explanation.append(
                "Overall ride compatibility is high"
            )

        ride.compatibility_explanation = explanation
        if distance > 1000:
            ride.demand_level = "🔥 High Demand"
            ride.predicted_bookings = "12-15 rides tomorrow"

        elif distance > 500:
            ride.demand_level = "📈 Medium Demand"
            ride.predicted_bookings = "7-10 rides tomorrow"

        else:
            ride.demand_level = "📉 Low Demand"
            ride.predicted_bookings = "2-5 rides tomorrow"
        carbon_saved = round(distance * 0.08)

        ride.carbon_saved = carbon_saved
        try:

            pickup = pickup_encoder.transform(
                [ride.source]
            )[0]

            destination_encoded = destination_encoder.transform(
                [ride.destination]
            )[0]

            vehicle_encoded = vehicle_encoder.transform(
                [ride.vehicle]
            )[0]

            current_hour = datetime.now().hour

            if current_hour < 12:
                time_slot = "Morning"
            elif current_hour < 18:
                time_slot = "Evening"
            else:
                time_slot = "Night"

            time_encoded = time_encoder.transform(
                [time_slot]
            )[0]

            prediction = knn_model.predict([[
                pickup,
                destination_encoded,
                time_encoded,
                ride.seats,
                ride.price,
                4.5,
                vehicle_encoded
            ]])

           
           
            if ride.ai_score >= 90:
                ride.match_level = "Best Match"
            elif ride.ai_score >= 70:
                ride.match_level = "Suitable Match"
            else:
                ride.match_level = "Low Match"
        except Exception as e:

            print("KNN Error:", e)
            ride.match_level = "Suitable Match"

    rides = sorted(
        rides,
        key=lambda x: x.ai_score,
        reverse=True
    )

    ride_locations = []

    city_coords = {
        "Hyderabad": [17.3850, 78.4867],
        "Bangalore": [12.9716, 77.5946],
        "Mumbai": [19.0760, 72.8777],
        "Chennai": [13.0827, 80.2707],
        "Delhi": [28.7041, 77.1025],
        "Jaipur": [26.9124, 75.7873],
"Agra": [27.1767, 78.0081],
"Pune": [18.5204, 73.8567],
"Vijayawada": [16.5062, 80.6480],
"Vizag": [17.6868, 83.2185],
"Warangal": [17.9689, 79.5941],
"Goa": [15.2993, 74.1240],
"Tirupati": [13.6288, 79.4192],
"Chandigarh": [30.7333, 76.7794]
    }

    for ride in rides:

        if ride.source in city_coords and ride.destination in city_coords:

         ride_locations.append({
    "source": ride.source,
    "destination": ride.destination,
    "source_coords": city_coords[ride.source],
    "destination_coords": city_coords[ride.destination]
    }) 
    print("RIDE LOCATIONS =", ride_locations)

    return render_template(
        'search_rides.html',
        rides=rides,
        ride_locations=ride_locations
    )

@app.route('/book_ride/<int:ride_id>')
def book_ride(ride_id):

    if 'user_id' not in session:
        return redirect('/login')

    ride = Ride.query.get(ride_id)

    if ride and ride.seats > 0:

        booking = Booking(
            user_id=session['user_id'],
            ride_id=ride.id
        )

        db.session.add(booking)

        ride.seats -= 1

        notification = Notification(
            user_id=session['user_id'],
            message="🎟️ Ride booked successfully."
        )

        db.session.add(notification)

        msg = Message(
            'Ride Booking Confirmed',
            sender=app.config['MAIL_USERNAME'],
            recipients=[app.config['MAIL_USERNAME']]
        )

        msg.body = f"""
Hi,

Your booking has been confirmed.

Route: {ride.source} → {ride.destination}
Date: {ride.date}
Time: {ride.time}

Thank you for using AI Car Pooling 🚗
"""

        mail.send(msg)

        db.session.commit()

        flash("Ride Booked Successfully!")

    return redirect('/my_bookings')
@app.route('/my_bookings')
def my_bookings():

    if 'user_id' not in session:
        return redirect('/login')

    bookings = Booking.query.filter_by(
        user_id=session['user_id']
    ).all()

    booked_rides = []

    for booking in bookings:

        ride = Ride.query.get(booking.ride_id)
        driver = User.query.get(ride.user_id)

        if ride:

            booked_rides.append({
            'ride': ride,
            'status': booking.status,
            'driver_name': driver.name if driver else "Unknown"
        })
    return render_template(
'bookings.html',
bookings=booked_rides
)
@app.route('/my_rides')
def my_rides():

    if 'user_id' not in session:
        return redirect('/login')

    rides = Ride.query.filter_by(
        user_id=session['user_id']
    ).all()

    return render_template(
        'my_rides.html',
        rides=rides
    )
@app.route('/notifications')
def notifications():

    if 'user_id' not in session:
        return redirect('/login')

    notifications = Notification.query.filter_by(
        user_id=session['user_id']
    ).order_by(
        Notification.id.desc()
    ).all()

    for notification in notifications:

        notification.is_read = True

    db.session.commit()

    return render_template(
        'notifications.html',
        notifications=notifications
    )
@app.route('/test_notification')
def test_notification():

    notification = Notification(
        user_id=session['user_id'],
        message='Test Notification'
    )

    db.session.add(notification)
    db.session.commit()

    return "Notification Added"
@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if request.method == 'POST':

        user.name = request.form['name']

        user.email = request.form['email']
        user.phone = request.form['phone']
        user.city = request.form['city']
        user.bio = request.form['bio']

        db.session.commit()

        session['user_name'] = user.name

        flash("Profile Updated Successfully!")

        return redirect('/dashboard')

    return render_template(
        'profile.html',
        user=user
    )
@app.route('/delete_ride/<int:ride_id>')
def delete_ride(ride_id):

    if 'user_id' not in session:
        return redirect('/login')

    ride = Ride.query.get_or_404(ride_id)

    if ride.user_id != session['user_id']:

        flash("Unauthorized Action")

        return redirect('/my_rides')

    db.session.delete(ride)

    db.session.commit()

    flash("Ride Deleted Successfully!")

    return redirect('/my_rides')
@app.context_processor
def notification_count():

    if 'user_id' in session:

        count = Notification.query.filter_by(
            user_id=session['user_id'],
            is_read=False
        ).count()

        return dict(
            notification_count=count
        )

    return dict(
        notification_count=0
    )
@app.route('/edit_ride/<int:ride_id>', methods=['GET', 'POST'])
def edit_ride(ride_id):

    if 'user_id' not in session:
        return redirect('/login')

    ride = Ride.query.get_or_404(ride_id)

    if ride.user_id != session['user_id']:

        flash("Unauthorized Action")

        return redirect('/my_rides')

    if request.method == 'POST':

        ride.date = request.form['date']
        ride.time = request.form['time']

        ride.seats = int(request.form['seats'])
        ride.price = int(request.form['price'])

        ride.vehicle = request.form['vehicle']
        ride.pickup = request.form['pickup']
        ride.description = request.form['description']

        db.session.commit()

        flash("Ride Updated Successfully!")

        return redirect('/my_rides')

    return render_template(
        'edit_ride.html',
        ride=ride
    )
@app.route('/ride_details/<int:ride_id>')
def ride_details(ride_id):

    if 'user_id' not in session:
        return redirect('/login')

    ride = Ride.query.get_or_404(ride_id)

    user = User.query.get(ride.user_id)
    reviews = Rating.query.filter_by(
    ride_id=ride_id
).all()
    return render_template(
        'ride_details.html',
        ride=ride,
        user=user,
        reviews=reviews
    )
@app.route('/cancel_booking/<int:ride_id>')
def cancel_booking(ride_id):

    if 'user_id' not in session:
        return redirect('/login')

    booking = Booking.query.filter_by(
        user_id=session['user_id'],
        ride_id=ride_id,
        status="Active"
    ).first()

    if booking:

        ride = Ride.query.get(ride_id)

        if ride:
            ride.seats += 1

        booking.status = "Cancelled"
        notification = Notification(
    user_id=session['user_id'],
    message="❌ Ride booking cancelled."
)

        db.session.add(notification)
        db.session.commit()

        flash("Booking Cancelled Successfully!")

    return redirect('/my_bookings')
@app.route('/complete_booking/<int:ride_id>')
def complete_booking(ride_id):

    if 'user_id' not in session:
        return redirect('/login')

    booking = Booking.query.filter_by(
        user_id=session['user_id'],
        ride_id=ride_id
    ).first()

    if booking:
        booking.status = "Completed"
        db.session.commit()

    return redirect('/my_bookings')
@app.route('/rate_ride/<int:ride_id>', methods=['GET', 'POST'])
def rate_ride(ride_id):

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        new_rating = Rating(
            user_id=session['user_id'],
            ride_id=ride_id,
            rating=int(request.form['rating']),
            review=request.form['review']
        )

        db.session.add(new_rating)
        db.session.commit()

        flash("Review Submitted Successfully!")

        return redirect('/my_bookings')

    return render_template(
        'rate_ride.html',
        ride_id=ride_id
    )
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


if __name__ == '__main__':

    with app.app_context():

        print(db.Model.metadata.tables.keys())

        db.create_all()

    app.run(debug=True)