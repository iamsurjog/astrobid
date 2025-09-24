import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from werkzeug.utils import secure_filename
import csv
import time

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DATA_FOLDER'] = 'data'

def get_users():
    users = {}
    with open(os.path.join(app.config['DATA_FOLDER'], 'users.csv'), 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            users[row[0]] = row[1]
    return users

def get_planets():
    planets = []
    with open(os.path.join(app.config['DATA_FOLDER'], 'planets.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            planets.append(row)
    return planets

def get_ownership():
    ownership = {}
    with open(os.path.join(app.config['DATA_FOLDER'], 'ownership.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ownership[row['planet']] = row['team']
    return ownership

def get_teams():
    teams = {}
    with open(os.path.join(app.config['DATA_FOLDER'], 'teams.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams[row['team_name']] = int(row['credits'])
    return teams

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

    with open(os.path.join(app.config['DATA_FOLDER'], 'current_auction.txt'), 'r') as f:
        current_auction_planet_name = f.read().strip()

    current_planet = None
    if current_auction_planet_name:
        planets = get_planets()
        for planet in planets:
            if planet['name'] == current_auction_planet_name:
                current_planet = planet
                break

    highest_bid = {'team': 'N/A', 'amount': 0}
    if current_planet:
        with open(os.path.join(app.config['DATA_FOLDER'], 'bids.csv'), 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['planet'] == current_planet['name'] and int(row['amount']) > int(highest_bid['amount']):
                    highest_bid = row
    
    team_name = session['username']
    owned_planets_names = []
    with open(os.path.join(app.config['DATA_FOLDER'], 'ownership.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['team'] == team_name:
                owned_planets_names.append(row['planet'])

    owned_planets = []
    if owned_planets_names:
        planets = get_planets()
        for planet in planets:
            if planet['name'] in owned_planets_names:
                owned_planets.append(planet)

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
    
    with open(os.path.join(app.config['DATA_FOLDER'], 'current_auction.txt'), 'r') as f:
        current_auction_planet_name = f.read().strip()

    current_planet = None
    if current_auction_planet_name:
        planets = get_planets()
        for planet in planets:
            if planet['name'] == current_auction_planet_name:
                current_planet = planet
                break

    highest_bid = {'team': 'N/A', 'amount': 0}
    if current_planet:
        with open(os.path.join(app.config['DATA_FOLDER'], 'bids.csv'), 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['planet'] == current_planet['name'] and int(row['amount']) > int(highest_bid['amount']):
                    highest_bid = row
    
    users = get_users()
    teams = [user for user in users if user != 'root']

    return render_template('admin.html', current_planet=current_planet, highest_bid=highest_bid, teams=teams)




@app.route('/admin/planets', methods=['GET', 'POST'])
def planet_management():
    if 'username' not in session or session['username'] != 'root':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        value = request.form['value']
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open(os.path.join(app.config['DATA_FOLDER'], 'planets.csv'), 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([name, description, filename, value])
            return redirect(url_for('planet_management'))

    planets = get_planets()
    ownership = get_ownership()
    with open(os.path.join(app.config['DATA_FOLDER'], 'last_update.txt'), 'w') as f:
        f.write(str(time.time()))
    return render_template('planet_management.html', planets=planets, ownership=ownership)


@app.route('/set_auction', methods=['POST'])
def set_auction():
    if 'username' not in session or session['username'] != 'root':
        return redirect(url_for('login'))

    planet_name = request.form['planet_name']
    with open(os.path.join(app.config['DATA_FOLDER'], 'current_auction.txt'), 'w') as f:
        f.write(planet_name)
    return redirect(url_for('planet_management'))

@app.route('/last_update')
def last_update():
    with open(os.path.join(app.config['DATA_FOLDER'], 'last_update.txt'), 'r') as f:
        return f.read().strip()

@app.route('/sell_planet', methods=['POST'])
def sell_planet():
    if 'username' not in session or session['username'] != 'root':
        return redirect(url_for('login'))

    with open(os.path.join(app.config['DATA_FOLDER'], 'current_auction.txt'), 'r') as f:
        planet_name = f.read().strip()

    if not planet_name:
        return "No planet is currently being auctioned.", 400

    team_name = request.form['team_name']
    amount = int(request.form['amount'])

    # Update ownership
    with open(os.path.join(app.config['DATA_FOLDER'], 'ownership.csv'), 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([planet_name, team_name])

    # Update credits
    teams = get_teams()
    teams[team_name] -= amount
    with open(os.path.join(app.config['DATA_FOLDER'], 'teams.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['team_name', 'credits'])
        for team, credits in teams.items():
            writer.writerow([team, credits])

    # Clear current auction
    with open(os.path.join(app.config['DATA_FOLDER'], 'current_auction.txt'), 'w') as f:
        f.write('')

    # Clear bids for the sold planet
    rows = []
    with open(os.path.join(app.config['DATA_FOLDER'], 'bids.csv'), 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)
        for row in reader:
            if row[0] != planet_name:
                rows.append(row)
    with open(os.path.join(app.config['DATA_FOLDER'], 'bids.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    with open(os.path.join(app.config['DATA_FOLDER'], 'last_update.txt'), 'w') as f:
        f.write(str(time.time()))

    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)

