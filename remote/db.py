

import sqlite3

def init_db():
    conn = sqlite3.connect('remote.db')
    cursor = conn.cursor()
    
    # Create the remote table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS remote (
            ip TEXT PRIMARY KEY,
            date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_remote(ip, date):
    conn = sqlite3.connect('remote.db')
    cursor = conn.cursor()
    
    # Insert a new remote entry
    cursor.execute('''
        REPLACE INTO remote (ip, date) VALUES (?, ?)
    ''', (ip, date))
    
    conn.commit()
    conn.close()

def get_remotes():
    conn = sqlite3.connect('remote.db')
    cursor = conn.cursor()
    
    # Retrieve all remote entries
    cursor.execute('SELECT remote.ip FROM remote')
    remotes = cursor.fetchall()
    
    conn.close()
    return remotes

# init upon import
init_db()
