import hashlib
import os
import sqlite3

def hash_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def scan_folder(folder_path):
    result = {}
    for file in (os.listdir(folder_path)):
        full_path = os.path.join(folder_path,file)
        result[full_path]=hash_file(full_path)
    return result

def init_db(db_path='fim.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS baseline(
                       filepath TEXT PRIMARY KEY,
                       hash TEXT
                   )
                   """)
    conn.commit()
    conn.close()
    
def save_baseline(snapshot, db_path='fim.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM baseline")
    for filepath, file_hash in snapshot.items():
        cursor.execute(
            "INSERT INTO baseline (filepath, hash) VALUES (?, ?)",
            (filepath, file_hash)
            )
    
    conn.commit()
    conn.close()    

init_db()
snapshot = scan_folder('./monitor_folder')
save_baseline(snapshot)