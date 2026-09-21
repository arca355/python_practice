def check_file(filename):
    result = {}
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            password = line.strip()
            problems = check_strenght(password)
            result[password] = problems if problems else ["Нет проблем"]
    return result

def check_strenght(password):
    common_password = ['123456','admin','password','admin123','qwerty','qwerty123']
    problems = []
    special_characters = "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~"
    if password.lower() in common_password: 
        problems.append("Не надеждный пароль как у всех")
    if len(password) < 8:
        problems.append("Пароль должен иметь более 8 символов. ")
    if not any(c.isupper() for c in password):
        problems.append("Пароль должен содержать хотя бы одну заглавную букву")
    if not any(c in special_characters for c in password):
        problems.append("Пароль должен содержать хотя бы один специальный символ")
    if not any(c.isdigit() for c in password):
        problems.append("Пароль должен содержать хотя бы одну цифру")
    return problems

def save_report(result,filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for password, problems in result.items():
            file.write(f"Пароль: {password} Проблемы: {', '.join(problems)}\n")

save_report(check_file('passwords.txt'),'report.txt')