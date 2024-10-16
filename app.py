from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'


@app.route('/')
def index():
    return render_template('index.html')


# Initialize the database
def init_db():
    with sqlite3.connect('parking.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
        conn.execute(
            'CREATE TABLE IF NOT EXISTS parking_centers (id INTEGER PRIMARY KEY, name TEXT, user_id INTEGER, FOREIGN KEY(user_id) REFERENCES users(id))')
        conn.execute(
            'CREATE TABLE IF NOT EXISTS cars (id INTEGER PRIMARY KEY, car_number TEXT UNIQUE, parking_center_id INTEGER, FOREIGN KEY(parking_center_id) REFERENCES parking_centers(id))')
        conn.commit()


# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        with sqlite3.connect('parking.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
                conn.commit()
                flash('Registration successful. You can log in now.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists.', 'error')

    return render_template('register.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('parking.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Login successful.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials.', 'error')

    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# Dashboard route to show user’s parking centers
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with sqlite3.connect('parking.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parking_centers WHERE user_id = ?', (user_id,))
        parking_centers = cursor.fetchall()

    return render_template('dashboard.html', parking_centers=parking_centers)


# Create a parking center
@app.route('/create_parking_center', methods=['POST'])
def create_parking_center():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form['center_name']
    user_id = session['user_id']

    with sqlite3.connect('parking.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO parking_centers (name, user_id) VALUES (?, ?)', (name, user_id))
        conn.commit()

    flash('Parking center created.', 'success')
    return redirect(url_for('dashboard'))


# Delete a parking center
@app.route('/delete_parking_center/<int:center_id>', methods=['POST'])
def delete_parking_center(center_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    with sqlite3.connect('parking.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM parking_centers WHERE id = ? AND user_id = ?', (center_id, user_id))
        conn.commit()

    flash('Parking center deleted.', 'success')
    return redirect(url_for('dashboard'))


# Show cars within a parking center
@app.route('/parking_center/<int:center_id>')
def view_parking_center(center_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('parking.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cars WHERE parking_center_id = ?', (center_id,))
        cars = cursor.fetchall()

    return render_template('view_parking_center.html', cars=cars, center_id=center_id)


# Manage cars within a parking center
@app.route('/manage_car/<int:center_id>', methods=['POST'])
def manage_car_in_center(center_id):
    car_number = request.form['car_number']
    action = request.form['action']

    with sqlite3.connect('parking.db') as conn:
        cursor = conn.cursor()

        if action == 'add':
            try:
                cursor.execute('INSERT INTO cars (car_number, parking_center_id) VALUES (?, ?)',
                               (car_number, center_id))
                conn.commit()
                flash(f'Car {car_number} added successfully.', 'success')
            except sqlite3.IntegrityError:
                flash(f'Car {car_number} is already in the list.', 'error')

        elif action == 'remove':
            cursor.execute('DELETE FROM cars WHERE car_number = ? AND parking_center_id = ?', (car_number, center_id))
            if cursor.rowcount == 0:
                flash(f'Car {car_number} is not in the list.', 'error')
            else:
                conn.commit()
                flash(f'Car {car_number} removed successfully.', 'success')

    return redirect(url_for('view_parking_center', center_id=center_id))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
