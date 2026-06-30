import os
import mysql.connector
from flask import Flask, request, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps


app = Flask(__name__, static_folder='public')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')


DB_CONFIG = {
    'host':     os.environ.get('DB_HOST', 'localhost'),
    'user':     os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'venuesync'),
    'charset':  'utf8mb4'
}


def get_db():
    """Opens a new MySQL connection and returns it."""
    return mysql.connector.connect(**DB_CONFIG)


def login_required(f):
    """Blocks the route if user is not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': 'Please log in'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Blocks the route if user is not an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': 'Please log in'}), 401
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password']

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid username or password'}), 401

    session['user_id'] = user['id']

    return jsonify({
        'user': {
            'id':       user['id'],
            'username': user['username'],
            'role':     user['role']
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password']

    if len(username) < 3:
        return jsonify({'message': 'Username must be at least 3 characters'}), 400

    if len(password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters'}), 400

    hashed = generate_password_hash(password)

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'INSERT INTO users (username, password, role) VALUES (%s, %s, %s)',
            (username, hashed, 'user')
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Account created successfully'}), 201
    except mysql.connector.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Username already taken'}), 409


@app.route('/api/venues/available', methods=['GET'])
@login_required
def get_available_venues():
    date = request.args.get('date')
    time = request.args.get('time')

    if not date or not time:
        return jsonify({'message': 'Date and time are required'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.id, v.name
        FROM venues v
        WHERE v.id NOT IN (
            SELECT b.venue_id
            FROM bookings b
            WHERE b.date = %s
              AND b.time = %s
              AND b.status != 'cancelled'
        )
    """, (date, time))

    venues = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(venues)


@app.route('/api/bookings', methods=['POST'])
@login_required
def create_booking():
    data = request.get_json()

    required = ['venueId', 'eventName', 'date', 'time']
    for field in required:
        if not data.get(field):
            return jsonify({'message': f'{field} is required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bookings
            (user_id, venue_id, event_name, purpose,
             event_id, special_guests, date, time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        session['user_id'],
        data['venueId'],
        data['eventName'],
        data.get('purpose', ''),
        data.get('eventId', ''),
        data.get('specialGuests', ''),
        data['date'],
        data['time']
    ))

    conn.commit()
    booking_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({'id': booking_id, 'message': 'Booking created'}), 201


@app.route('/api/bookings', methods=['GET'])
@login_required
def get_my_bookings():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            b.id,
            b.event_name,
            CAST(b.date AS CHAR) AS date,
            CAST(b.time AS CHAR) AS time,
            b.status,
            v.name AS venue_name
        FROM bookings b
        JOIN venues v ON b.venue_id = v.id
        WHERE b.user_id = %s
        ORDER BY b.created_at DESC
    """, (session['user_id'],))

    bookings = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(bookings)


@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
@login_required
def cancel_booking(booking_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        'SELECT user_id, status FROM bookings WHERE id = %s',
        (booking_id,)
    )
    booking = cursor.fetchone()

    if not booking:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Booking not found'}), 404

    if booking['user_id'] != session['user_id']:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Not your booking'}), 403

    if booking['status'] != 'pending':
        cursor.close()
        conn.close()
        return jsonify({'message': 'Only pending bookings can be cancelled'}), 400

    cursor.execute(
        'UPDATE bookings SET status = %s WHERE id = %s',
        ('cancelled', booking_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Booking cancelled'})


@app.route('/api/bookings/pending', methods=['GET'])
@login_required
@admin_required
def get_pending_bookings():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            b.id,
            b.event_name,
            CAST(b.date AS CHAR) AS date,
            CAST(b.time AS CHAR) AS time,
            b.status,
            v.name     AS venue_name,
            u.username AS booked_by
        FROM bookings b
        JOIN venues v ON b.venue_id = v.id
        JOIN users  u ON b.user_id  = u.id
        WHERE b.status = 'pending'
        ORDER BY b.created_at
    """)
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(bookings)


@app.route('/api/bookings/<int:booking_id>/approve', methods=['PATCH'])
@login_required
@admin_required
def approve_booking(booking_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE bookings SET status = %s WHERE id = %s',
        ('approved', booking_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Booking approved'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
