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
        for item in print_summary(result):
            file.write(item)
            
def print_summary(passwords_and_problem):
    result = []
    yes,no = 0,0
    result.append(f"Общее число паролей - {len(passwords_and_problem)}\n")
    
    problem_count = {}
    
    for item in passwords_and_problem.values():
        if "Нет проблем" in item:
            yes+= 1
        else:
            no += 1
            for problem in item:
                problem_count[problem] = problem_count.get(problem,0)+1
                
    result.append(f"\nОбщее число надежных паролей - {yes}\n")
    result.append(f"Общее число НЕ надежных паролей - {no}\n")
    
    if problem_count:
        most_common = max(problem_count, key=problem_count.get)
        result.append(f"Самая частая проблемма - '{most_common}' ({problem_count[most_common]} раз)\n")
        
    return result
    

result = check_file('passwords.txt')
save_report(result,'report.txt')