from datetime import datetime, timezone
import hashlib
import os
import sqlite3
import argparse

BASEDIR = os.path.dirname(os.path.abspath(__file__))


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
    except OSError as e:
        print(f"Ошибка при открытии файла {filepath}: {e}")
        return None
    return sha256.hexdigest()

# Хеширование всех файлов в папке и возврат вместе с путями
def scan_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не существует.")
        return None, []
    folder_path = os.path.abspath(folder_path)
    result = {}
    unreadable_files = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(full_path)).astimezone()  # Получаем время последнего изменения файла и преобразуем в локальное время
            formated_mtime = mtime.strftime("%d.%m.%Y %H:%M:%S")
            file_hash = hash_file(full_path)
            if file_hash is not None:# Проверяем, что хеш не None
                result[full_path] = (file_hash, formated_mtime)
            else:
                unreadable_files.append(full_path)
    return result, unreadable_files

# Основная функция сравнения "Предыдущего" состояния папки и "Нового" на момент сканирования
def check_integrity(folder_path,db_path='fim.db'):
    
    old_snapshot = get_baseline(db_path)
    new_snapshot, unreadable_files = scan_folder(folder_path)
    
    if new_snapshot is None:
        return None
    
    old_files = set(old_snapshot.keys())
    new_files = set(new_snapshot.keys())

    deleted = (old_files - new_files) - set(unreadable_files)  # Исключаем файлы, к которым нет доступа на чтение
    added = new_files - old_files
    common = old_files & new_files
    
    modified = {f for f in common if old_snapshot[f][0] != new_snapshot[f][0]}  # Проверка хеша для определения изменений
    unchanged = common - modified
    
    return{
        "deleted" : deleted,
        "added" : added,
        "modified" : modified,
        "unchanged" : unchanged,
        "new_snapshot" : new_snapshot,
        "unreadable_files" : unreadable_files
    }

# Вывод получившихся результатов
def print_report(result):
    if result is None:
        print("Ошибка при сканировании папки.")
        return

    print(f"Удалено файлов {len(result['deleted'])}")
    for f in result['deleted']:
        print(f" - {f}")  # Выводим путь и время последнего изменения удаленных файлов
    
    print(f"Создано файлов {len(result['added'])}")
    for f in result['added']:
        print(f" + {f}")    
    
    print(f"Изменено файлов {len(result['modified'])}")
    for f in result["modified"]:
        print(f" ~ {f}")    
    print(f"Без изменений {len(result['unchanged'])}")   
    print(f"Нет доступа на чтение {len(result['unreadable_files'])}")   
    
def parse_args():
    parser = argparse.ArgumentParser(description="File Integrity Monitoring")
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument("--path","-p", required=True, help="Путь к папке для мониторинга")
    parser.add_argument("--db", default=os.path.join(BASEDIR, "fim.db"), help="Путь к базе данных (по умолчанию fim.db)")
    group.add_argument("--init", action="store_true", help="Инициализация базы данных")
    group.add_argument("--check", action="store_true", help="Проверка целостности файлов в указанной папке")
    parser.add_argument("--update","-u", action="store_true", help="Обновление базы данных с текущим состоянием папки")
    args = parser.parse_args()
    if args.update and not args.check:
        parser.error("--update может использоваться только с --check")
    return args


if __name__ == "__main__":

    args = parse_args()
    init_db(args.db)  # Инициализация базы данных при запуске скрипта
    if args.init:
        snapshot, unreadable_files = scan_folder(args.path)  # Сканирование указанной папки
        if snapshot is not None:
            save_baseline(snapshot, args.db) # Сохранение текущего состояния папки в базу данных
    elif args.check:
        result = check_integrity(args.path, args.db)  # Сравнение состояния указанной папки
        if args.update and result is not None:
            save_baseline(result["new_snapshot"], args.db)
        print_report(result)

    