import config
import datetime
import random
import pymysql


#Добавити агента
def add_agent(agent_id):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"INSERT INTO agents (`agent_id`) VALUES ('{agent_id}')")
    con.commit()

    cur.close()
    con.close()


#Добавити файл
def add_file(req_id, file_id, file_name, type):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"INSERT INTO files (`req_id`, `file_id`, `file_name`, `type`) VALUES ('{req_id}', '{file_id}', '{file_name}', '{type}')")
    con.commit()

    cur.close()
    con.close()


#Створити запис
def new_req(user_id, request):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    #Добавити запис в БД
    cur.execute(f"INSERT INTO requests (`user_id`, `req_status`) VALUES ('{user_id}', 'waiting')") 

    #Отримати айді добавленого запису
    req_id = cur.lastrowid

    dt = datetime.datetime.now()
    date_now = dt.strftime('%d.%m.%Y %H:%M:%S')

    #Добавити повідомлення з запису
    cur.execute(f"INSERT INTO messages (`req_id`, `message`, `user_status`, `date`) VALUES ('{req_id}', '{request}', 'user', '{date_now}')")

    con.commit()

    cur.close()
    con.close()

    return req_id


#Добавити повідомлення 
def add_message(req_id, message, user_status):
    if user_status == 'user':
        req_status = 'waiting'
    elif user_status == 'agent':
        req_status = 'answered'

    dt = datetime.datetime.now()
    date_now = dt.strftime('%d.%m.%Y %H:%M:%S')

    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    #Добавити повідолменнЯ для запису 
    cur.execute(f"INSERT INTO messages (`req_id`, `message`, `user_status`, `date`) VALUES ('{req_id}', '{message}', '{user_status}', '{date_now}')")
    
    #Змінити статус запису 
    cur.execute(f"UPDATE requests SET `req_status` = '{req_status}' WHERE `req_id` = '{req_id}'")
    
    con.commit()

    cur.close()
    con.close()


#Добавити паролі
def add_passwords(passwords):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    for password in passwords:
        cur.execute(f"INSERT INTO passwords (`password`) VALUES ('{password}')")
        
    con.commit()

    cur.close()
    con.close()


#Перевірити  статус агента
def check_agent_status(user_id):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT * FROM agents WHERE `agent_id` = '{user_id}'")
    agent = cur.fetchone()

    cur.close()
    con.close()

    if agent == None:
        return False
    else:
        return True


#Перевірити валідність пароля
def valid_password(password):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT * FROM passwords WHERE `password` = '{password}'")
    password = cur.fetchone()

    cur.close()
    con.close()

    if password == None:
        return False
    else:
        return True


#Перевірити чи відправляє користувач файл, якщо так - повернути його
def get_file(message):
    """
    Атрибут file_name доступен только в типах файлов - document и video.
    Если пользователь отправляет не документ и не видео - в качестве имени файла передать дату и время отправки (date_now)
    """

    types = ['document', 'video', 'audio', 'voice']
    dt = datetime.datetime.now()
    date_now = dt.strftime('%d.%m.%Y %H:%M:%S')

    #Спочатку перевірити чи відправляє користувач фото 
    try:
        return {'file_id': message.json['photo'][-1]['file_id'], 'file_name': date_now, 'type': 'photo', 'text': str(message.caption)}

    #Якщо ні - перевірити чи відправляє документ, відео, аудіо, голосове повідомлення 
    except:
        for type in types:
            try:
                if type == 'document' or type == 'video':
                    file_name = message.json[type]['file_name']
                else:
                    file_name = date_now

                return {'file_id': message.json[type]['file_id'], 'file_name': file_name, 'type': type, 'text': str(message.caption)}
            except:
                pass
    
        return None


#Отримати іконку статуса запиту 
def get_icon_from_status(req_status, user_status):
    if req_status == 'confirm':
        return '✅'

    elif req_status == 'waiting':
        if user_status == 'user':
            return '⏳'
        elif user_status == 'agent':
            return '❗️'

    elif req_status == 'answered':
        if user_status == 'user':
            return '❗️'
        elif user_status == 'agent':
            return '⏳'


#Отримати текст для кнопки з файлом 
def get_file_text(file_name, type):
    if type == 'photo':
        return f'📷 | Фото {file_name}'
    elif type == 'document':
        return f'📄 | Документ {file_name}'
    elif type == 'video':
        return f'🎥 | Видео {file_name}'
    elif type == 'audio':
        return f'🎵 | Аудио {file_name}'
    elif type == 'voice':
        return f'🎧 | Голосовое сообщение {file_name}'
            

#Згенерувати паролі 
def generate_passwords(number, lenght):
    chars = 'abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

    passsords = []
    for _ in range(number):
        password = ''
        for _ in range(lenght):
            password += random.choice(chars)

        passsords.append(password)

    return passsords


#Отримати User ID користувача, створившого запит 
def get_user_id_of_req(req_id):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `user_id` FROM requests WHERE `req_id` = '{req_id}'")
    user_id = cur.fetchone()[0]

    cur.close()
    con.close()

    return user_id


#Отримати file_id із id запису в БД
def get_file_id(id):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `file_id` FROM files WHERE `id` = '{id}'")
    file_id = cur.fetchone()[0]

    cur.close()
    con.close()

    return file_id


#Отримати статус запису
def get_req_status(req_id):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `req_status` FROM requests WHERE `req_id` = '{req_id}'")
    req_status = cur.fetchone()[0]

    cur.close()
    con.close()

    return req_status


#Видалити пароль
def delete_password(password):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"DELETE FROM {config.MySQL[3]}.passwords WHERE `password` = '{password}'")
    con.commit()

    cur.close()
    con.close()


#Видалити агента
def delete_agent(agent_id):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"DELETE FROM {config.MySQL[3]}.agents WHERE `agent_id` = '{agent_id}'")
    con.commit()

    cur.close()
    con.close()


#Завершити запис 
def confirm_req(req_id):
    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"UPDATE requests SET `req_status` = 'confirm' WHERE `req_id` = '{req_id}'")
    con.commit()

    cur.close()
    con.close()


#Отримати паролі з лімітом
def get_passwords(number):
    limit = (int(number) * 10) - 10

    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `password` FROM passwords LIMIT {limit}, 10")
    passwords = cur.fetchall()

    cur.close()
    con.close()

    return passwords


#Отримати агентів з лімітом
def get_agents(number):
    limit = (int(number) * 10) - 10

    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `agent_id` FROM agents LIMIT {limit}, 10")
    agents = cur.fetchall()

    cur.close()
    con.close()

    return agents


#Отримати мої запити з лімітом 
def my_reqs(number, user_id):
    limit = (int(number) * 10) - 10

    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `req_id`, `req_status` FROM requests WHERE `user_id` = '{user_id}' ORDER BY `req_id` DESC LIMIT {limit}, 10")
    reqs = cur.fetchall()

    cur.close()
    con.close()

    return reqs


#Отримати записи статусу з лімітами
def get_reqs(number, callback):
    limit = (int(number) * 10) - 10
    req_status = callback.replace('_reqs', '')

    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `req_id`, `req_status` FROM requests WHERE `req_status` = '{req_status}' ORDER BY `req_id` DESC LIMIT {limit}, 10")
    reqs = cur.fetchall()

    cur.close()
    con.close()

    return reqs


#Отримати файли по запиту з лімітом 
def get_files(number, req_id):
    limit = (int(number) * 10) - 10

    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `id`, `file_name`, `type` FROM files WHERE `req_id` = '{req_id}' ORDER BY `id` DESC LIMIT {limit}, 10")
    files = cur.fetchall()

    cur.close()
    con.close()

    return files


#Отримати історію запроса 
def get_request_data(req_id, callback):
    if 'my_reqs' in callback:
        get_dialog_user_status = 'user'
    else:
        get_dialog_user_status = 'agent'

    con = pymysql.connect(host=config.MySQL[0], user=config.MySQL[1], passwd=config.MySQL[2], db=config.MySQL[3])
    cur = con.cursor()

    cur.execute(f"SELECT `message`, `user_status`, `date` FROM messages WHERE `req_id` = '{req_id}'")
    messages = cur.fetchall()

    cur.close()
    con.close()

    data = []
    text = ''
    i = 1

    for message in messages:
        message_value = message[0]
        user_status = message[1]
        date = message[2] 

        if user_status == 'user':
            if get_dialog_user_status == 'user':
                text_status = '👤 Ваше сообщение'
            else:
                text_status = '👤 Сообщение пользователя'
        elif user_status == 'agent':
            text_status = '🧑‍💻 Агент поддержки'

        #Бекап для тексту
        backup_text = text
        text += f'{text_status}\n{date}\n{message_value}\n\n'

        #Якщо розмір тексту перевищує допустимі в Телеграм, то добавити першу частину тексту і почати другу частину.
        if len(text) >= 4096:
            data.append(backup_text)
            text = f'{text_status}\n{date}\n{message_value}\n\n'

        #Якщо зараз остання ітерація, щоб перевірити, чи частина тексту перевищує допустимий розмір (4096 символів). Якщо вище - додайте частину і надрукуйте наступну. Якщо немає - просто додайте останню частину списку.
        if len(messages) == i:
            if len(text) >= 4096:
                data.append(backup_text)
                text = f'{text_status}\n{date}\n{message_value}\n\n'
            
            data.append(text)   

        i += 1

    return data