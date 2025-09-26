import sqlite3
import csv

conn = sqlite3.connect('data/astrobid.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS teams (
    team_name TEXT PRIMARY KEY,
    credits INTEGER NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS planets (
    name TEXT PRIMARY KEY,
    description TEXT,
    image TEXT,
    value INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS ownership (
    planet TEXT PRIMARY KEY,
    team TEXT,
    FOREIGN KEY (planet) REFERENCES planets (name),
    FOREIGN KEY (team) REFERENCES teams (team_name)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS bids (
    planet TEXT,
    team TEXT,
    amount INTEGER,
    PRIMARY KEY (planet, team),
    FOREIGN KEY (planet) REFERENCES planets (name),
    FOREIGN KEY (team) REFERENCES teams (team_name)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS current_auction (
    planet_name TEXT,
    FOREIGN KEY (planet_name) REFERENCES planets (name)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS last_update (
    time REAL
)
''')

# Migrate data from users.csv
with open('data/users.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (row[0], row[1]))

# Migrate data from teams.csv
with open('data/teams.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        cursor.execute("INSERT INTO teams (team_name, credits) VALUES (?, ?)", (row[0], int(row[1])))

# Migrate data from planets.csv
with open('data/planets.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        cursor.execute("INSERT INTO planets (name, description, image, value) VALUES (?, ?, ?, ?)", (row[0], row[1], row[2], int(row[3]) if row[3] else 0))

# Migrate data from ownership.csv
with open('data/ownership.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        cursor.execute("INSERT INTO ownership (planet, team) VALUES (?, ?)", (row[0], row[1]))

# Migrate data from bids.csv
with open('data/bids.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        cursor.execute("INSERT INTO bids (planet, team, amount) VALUES (?, ?, ?)", (row[0], row[1], int(row[2])))

# Migrate data from current_auction.txt
with open('data/current_auction.txt', 'r') as f:
    planet_name = f.read().strip()
    if planet_name:
        cursor.execute("INSERT INTO current_auction (planet_name) VALUES (?)", (planet_name,))

# Migrate data from last_update.txt
with open('data/last_update.txt', 'r') as f:
    last_update_time = f.read().strip()
    if last_update_time:
        cursor.execute("INSERT INTO last_update (time) VALUES (?)", (float(last_update_time),))

conn.commit()
conn.close()

print("Data migration to SQLite is complete.")
