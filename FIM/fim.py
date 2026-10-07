from datetime import datetime, timezone
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
                       hash TEXT,
                       mtime TEXT 
                   )
                   """)
    conn.commit()
    conn.close()

# Достать предыдущее значение хешей файлов и их названия из БД
def get_baseline(db_path='fim.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT filepath, hash, mtime FROM baseline")
    rows = cursor.fetchall() #загрузка данных из SELECT
    conn.close()
    result = {row[0]: (row[1], row[2]) for row in rows} #формирование словаря из полученных данных
    return result

# Сохранение путей файлов и их хешей в базе
def save_baseline(snapshot, db_path='fim.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM baseline")
    for filepath, (file_hash, mtime) in snapshot.items():
        cursor.execute(
            "INSERT INTO baseline (filepath, hash, mtime) VALUES (?, ?, ?)",
            (filepath, file_hash, mtime)
        )
    
    conn.commit()
    conn.close()    

# Хеширование файла
def hash_file(filepath):
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
    except Exception as e:
        print(f"Ошибка при открытии файла {filepath}: {e}")
    return sha256.hexdigest()

# Хеширование всех файлов в папке и возврат вместе с путями
def scan_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не существует.")
        return None
    folder_path = os.path.abspath(folder_path)
    result = {}
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(full_path)).astimezone()  # Получаем время последнего изменения файла и преобразуем в локальное время
            formated_mtime = mtime.strftime("%d.%m.%Y %H:%M:%S")
            result[full_path] = (hash_file(full_path), formated_mtime)
    return result

# Основная функция сравнения "Предыдущего" состояния папки и "Нового" на момент сканирования
def check_integrity(folder_path,db_path='fim.db'):
    
    old_snapshot = get_baseline(db_path)
    new_snapshot = scan_folder(folder_path)
    
    if new_snapshot is None:
        return None
    
    old_files = set(old_snapshot.keys())
    new_files = set(new_snapshot.keys())

    deleted = old_files - new_files
    added = new_files - old_files
    common = old_files & new_files
    
    modified = {f for f in common if old_snapshot[f][0] != new_snapshot[f][0]}  # Проверка хеша для определения изменений
    unchanged = common - modified
    
    return{
        "deleted" : deleted,
        "added" : added,
        "modified" : modified,
        "unchanged" : unchanged,
        "new_snapshot" : new_snapshot
    }

# Вывод получившихся результатов
def print_report(result):
    if result is None:
        print("Ошибка при сканировании папки.")
        return

    print(f"Удалено файлов {len(result['deleted'])}")
    for f in result['deleted']:
        print(f" - {f}")
    
    print(f"Создано файлов {len(result['added'])}")
    for f in result['added']:
        print(f" + {f}")    
    
    print(f"Изменено файлов {len(result['modified'])}")
    for f in result["modified"]:
        print(f" ~ {f}")
    print(f"Без изменений {len(result['unchanged'])}")   



if __name__ == "__main__":
    init_db() #Инициализация БД
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) #Директория с текущим файлом "fim.py"
    MONITOR_FOLDER = os.path.join(BASE_DIR, "monitor_folder") #Соседняя с файлом папка для мониторинга

    result = check_integrity(MONITOR_FOLDER) #Сравнение состояния папки
    print_report(result)
    if result is not None:  
        save_baseline(result["new_snapshot"]) # Загрузка "Измененного" состояния в базу
