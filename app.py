import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from werkzeug.utils import secure_filename
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def get_db_connection():
    conn = sqlite3.connect('data/astrobid.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = {row['username']: row['password'] for row in cursor.fetchall()}
    conn.close()
    return users

def get_users_sno():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = {row['username']: row['sno'] for row in cursor.fetchall()}
    conn.close()
    return users

def get_planets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM planets")
    planets = cursor.fetchall()
    conn.close()
    return planets

def get_ownership():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ownership")
    ownership = {row['planet']: row['team'] for row in cursor.fetchall()}
    conn.close()
    return ownership

def get_teams():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teams")
    teams = {row['team_name']: int(row['credits']) for row in cursor.fetchall()}
    conn.close()
    return teams

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        if session['username'] == "root":
            return redirect(url_for("admin"))
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = get_users()
        if username in users and users[username] == password:
            session['username'] = username
            if username == "root":
                return redirect(url_for("admin"))
            teams = get_teams()
            session['credits'] = teams.get(username, 0)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['username'] == 'root':
        return redirect(url_for('admin'))

    teams = get_teams()
    session['credits'] = teams.get(session['username'], 0)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT planet_name FROM current_auction LIMIT 1")
    row = cursor.fetchone()
    current_auction_planet_name = row[0] if row else None

    current_planet = None
    if current_auction_planet_name:
        planets = get_planets()
        for planet in planets:
            if planet['name'] == current_auction_planet_name:
                current_planet = planet
                break

    highest_bid = {'team': 'N/A', 'amount': 0}
    if current_planet:
        cursor.execute("SELECT * FROM bids WHERE planet = ? ORDER BY amount DESC LIMIT 1", (current_planet['name'],))
        highest_bid = cursor.fetchone() or highest_bid
    
    team_name = session['username']
    owned_planets_names = []
    cursor.execute("SELECT planet FROM ownership WHERE team = ?", (team_name,))
    for row in cursor.fetchall():
        owned_planets_names.append(row['planet'])

    owned_planets = []
    if owned_planets_names:
        planets = get_planets()
        for planet in planets:
            if planet['name'] in owned_planets_names:
                owned_planets.append(planet)
    conn.close()

    resp = make_response(render_template('dashboard.html', current_planet=current_planet, highest_bid=highest_bid, credits=session.get('credits'), owned_planets=owned_planets))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('credits', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'username' not in session or session['username'] != 'root':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT planet_name FROM current_auction LIMIT 1")
    row = cursor.fetchone()
    current_auction_planet_name = row[0] if row else None

    current_planet = None
    if current_auction_planet_name:
        planets = get_planets()
        for planet in planets:
            if planet['name'] == current_auction_planet_name:
                current_planet = planet
                break

    highest_bid = {'team': 'N/A', 'amount': 0}
    if current_planet:
        cursor.execute("SELECT * FROM bids WHERE planet = ? ORDER BY amount DESC LIMIT 1", (current_planet['name'],))
        highest_bid = cursor.fetchone() or highest_bid
    
    users = get_users_sno()
    teams = [(user, users[user]) for user in users if user != 'root']
    conn.close()

    return render_template('admin.html', current_planet=current_planet, highest_bid=highest_bid, teams=teams)

@app.route('/admin/planets', methods=['GET', 'POST'])
def planet_management():
    if 'username' not in session or session['username'] != 'root':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        value = request.form['value']
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor.execute("INSERT INTO planets (name, description, image, value) VALUES (?, ?, ?, ?)", (name, description, filename, value))
            conn.commit()
            conn.close()
            return redirect(url_for('planet_management'))

    planets = get_planets()
    ownership = get_ownership()
    cursor.execute("UPDATE last_update SET time = ?", (time.time(),))
    conn.commit()
    conn.close()
    return render_template('planet_management.html', planets=planets, ownership=ownership)

@app.route('/set_auction', methods=['POST'])
def set_auction():
    if 'username' not in session or session['username'] != 'root':
        return redirect(url_for('login'))

    planet_name = request.form['planet_name']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE current_auction SET planet_name = ?", (planet_name,))
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO current_auction (planet_name) VALUES (?)", (planet_name,))
    conn.commit()
    conn.close()
    return redirect(url_for('planet_management'))

@app.route('/last_update')
def last_update():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM last_update")
    time = str(cursor.fetchone()[0])
    conn.close()
    return time

@app.route('/sell_planet', methods=['POST'])
def sell_planet():
    if 'username' not in session or session['username'] != 'root':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT planet_name FROM current_auction LIMIT 1")
    planet_name = cursor.fetchone()[0]

    if not planet_name:
        return "No planet is currently being auctioned.", 400

    team_name = request.form['team_name']
    amount = int(request.form['amount'])

    # Update ownership
    cursor.execute("INSERT INTO ownership (planet, team) VALUES (?, ?)", (planet_name, team_name))
    conn.commit()

    # Update credits
    cursor.execute("UPDATE teams SET credits = credits - ? WHERE team_name = ?", (amount, team_name))
    conn.commit()

    # Clear current auction
    cursor.execute("UPDATE current_auction SET planet_name = ''")
    conn.commit()

    # Clear bids for the sold planet
    cursor.execute("DELETE FROM bids WHERE planet = ?", (planet_name,))
    conn.commit()

    cursor.execute("UPDATE last_update SET time = ?", (time.time(),))
    conn.commit()
    conn.close()

    return redirect(url_for('admin'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        if 'new_username' in request.form:
            new_username = request.form['new_username']
            old_username = session['username']
            
            # Update username in users table
            cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
            conn.commit()
            
            # Update username in teams table
            cursor.execute("UPDATE teams SET team_name = ? WHERE team_name = ?", (new_username, old_username))
            conn.commit()
            
            cursor.execute("UPDATE ownership SET team = ? WHERE team = ?", (new_username, old_username))
            conn.commit()

            session['username'] = new_username
        elif 'new_password' in request.form:
            new_password = request.form['new_password']
            username = session['username']
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
            conn.commit()
        
        conn.close()
        return redirect(url_for('settings'))

    conn.close()
    return render_template('settings.html')

@app.route('/leaderboard')
def leaderboard():
    if 'username' not in session or session['username'] != 'root':
        return redirect(url_for('login'))

    teams = get_teams()
    planets = get_planets()
    ownership = get_ownership()

    planet_values = {planet['name']: planet['value'] for planet in planets}

    leaderboard_data = []
    for team_name, credits in teams.items():
        planet_value = 0
        num_planets = 0
        for planet, owner in ownership.items():
            if owner == team_name:
                planet_value += planet_values.get(planet, 0)
                num_planets += 1
        
        leaderboard_data.append({
            'team_name': team_name,
            'credits': credits,
            'planet_value': planet_value,
            'total_score': credits + planet_value,
            'num_planets': num_planets
        })

    leaderboard_data.sort(key=lambda x: x['total_score'], reverse=True)

    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)

if __name__ == '__main__':
    app.run(debug=True)
