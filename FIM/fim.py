import hashlib
import os
import sqlite3

# Инициализация БД
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
    
# Сохранение путей файлов и их хешей в базе
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

# Достать предыдущее значение хешей файлов и их названия из БД
def get_baseline(db_path='fim.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT filepath, hash FROM baseline")
    rows = cursor.fetchall() #загрузка данных из SELECT
    conn.close()
    return dict(rows)

# Хеширование файла
def hash_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# Хеширование всех файлов в папке и возврат вместе с путями
def scan_folder(folder_path):
    folder_path = os.path.abspath(folder_path)
    result = {}
    for file in (os.listdir(folder_path)):
        full_path = os.path.join(folder_path,file)
        result[full_path]=hash_file(full_path)
    return result

# Основная функция сравнения "Предыдущего" состояния папки и "Нового" на момент сканирования
def check_integrity(folder_path,db_path='fim.db'):
    old_snapshot = get_baseline(db_path)
    new_snapshot = scan_folder(folder_path)
    
    old_files = set(old_snapshot.keys())
    new_files = set(new_snapshot.keys())

    deleted = old_files - new_files
    added = new_files - old_files
    common = old_files & new_files
    
    modeified = {f for f in common if old_snapshot[f] != new_snapshot[f]}
    unchanget = common - modeified
    
    return{
        "deleted" : deleted,
        "added" : added,
        "modified" : modeified,
        "unchanget" : unchanget,
        "new_snapshot" : new_snapshot
    }

# Вывод получившихся результатов
def print_report(result):
    print(f"Удлено файлов {len(result['deleted'])}")
    for f in result['deleted']:
        print(f" - {f}")
    
    print(f"Созданных файлов {len(result['added'])}")
    for f in result['added']:
        print(f" + {f}")    
    
    print(f"Изменено файлов {len(result["modified"])}")
    for f in result["modified"]:
        print(f" ~ {f}")
    print(f"Без изменений {len(result["unchanget"])}")   


BASE_DIR = os.path.dirname(os.path.abspath(__file__)) #Директория с текущим файлом "fim.py"
MONITOR_FOLDER = os.path.join(BASE_DIR, "monitor_folder") #Соседняя с файлом папка для мониторинга

result = check_integrity(MONITOR_FOLDER) #Сравнение состояния папки
print_report(result)

save_baseline(result["new_snapshot"]) # Загрузка "Измененного" состояния в базу
