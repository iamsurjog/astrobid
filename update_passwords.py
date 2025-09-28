import sqlite3
import random
import string

def generate_password(length=5):
    """Generate a random password of a given length."""
    # Exclude characters that can be confused
    chars = string.ascii_letters + string.digits
    chars = chars.replace('0', '').replace('O', '').replace('o', '').replace('1', '').replace('l', '').replace('I', '')
    return ''.join(random.choice(chars) for i in range(length))

def update_passwords():
    """Update passwords for all users in the database."""
    conn = sqlite3.connect('data/astrobid.db')
    c = conn.cursor()

    # Get all usernames
    c.execute("SELECT username FROM users")
    usernames = [row[0] for row in c.fetchall()]

    # Update password for each user
    for username in usernames:
        new_password = generate_password()
        c.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
        print(f"Updated password for {username} to {new_password}")

    conn.commit()

    # Write the updated passwords to a new csv file
    c.execute("SELECT username, password FROM users")
    with open('data/new_passwords.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'password'])
        writer.writerows(c.fetchall())

    conn.close()
    print("\nNew passwords written to data/new_passwords.csv")

if __name__ == '__main__':
    import csv
    update_passwords()
