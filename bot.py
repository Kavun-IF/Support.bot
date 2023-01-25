import config
import core
import telebot
import random
import datetime
import markup
import sys
from telebot import apihelper

if config.PROXY_URL:
    apihelper.proxy = {'https': config.PROXY_URL}

bot = telebot.TeleBot(config.TOKEN, skip_pending=True)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, '👋🏻 Привіт! Це бот технічної підтримки підписників.\n Якщо в тебе виникла проблема чи пропозиція - жми кнопку <b>Написати звернення</b> і наші співробітники тобі нададуть відповідь! Всього доброго, @cyberlegions', parse_mode='html', reply_markup=markup.markup_main())


@bot.message_handler(commands=['agent'])
def agent(message):
    user_id = message.from_user.id

    if core.check_agent_status(user_id) == True: 
        bot.send_message(message.chat.id, '🔑 Ви Авторизовані як агент підтримки.', parse_mode='html', reply_markup=markup.markup_agent())

    else:
        take_password_message = bot.send_message(message.chat.id, '⚠️ Тебе немає в базі. Відправ одноразовий ключ відповіді.', reply_markup=markup.markup_cancel())

        bot.clear_step_handler_by_chat_id(message.chat.id)
        bot.register_next_step_handler(take_password_message, get_password_message)


@bot.message_handler(commands=['admin'])
def admin(message):
    user_id = message.from_user.id

    if str(user_id) == config.ADMIN_ID:
        bot.send_message(message.chat.id, '🔑 Ви авторизовані як Адмін', reply_markup=markup.markup_admin())
    else:
        bot.send_message(message.chat.id, '🚫 Ця команда доступна тільки адміністраторам.')


@bot.message_handler(content_types=['text'])
def send_text(message):
    user_id = message.from_user.id 

    if message.text == '✏️ Написати звернення':
        take_new_request = bot.send_message(message.chat.id, 'Введіть свій запит і наші співробітники скоро з вами зв`яжуться.', reply_markup=markup.markup_cancel())

        bot.clear_step_handler_by_chat_id(message.chat.id)
        bot.register_next_step_handler(take_new_request, get_new_request)

    elif message.text == '✉️ Мої запити':
        markup_and_value = markup.markup_reqs(user_id, 'my_reqs', '1')
        markup_req = markup_and_value[0]
        value = markup_and_value[1]

        if value == 0:
            bot.send_message(message.chat.id, 'У вас поки, що немає запитів.', reply_markup=markup.markup_main())
        else:
            bot.send_message(message.chat.id, 'Ваші запити:', reply_markup=markup_req)
    
    else:
        bot.send_message(message.chat.id, 'Ви повернуті в головне меню.', parse_mode='html', reply_markup=markup.markup_main())


def get_password_message(message):
    password = message.text
    user_id = message.from_user.id

    if password == None:
        send_message = bot.send_message(message.chat.id, '⚠️ Ви відправляєте не текст. Спробуйте ще раз.', reply_markup=markup.markup_cancel())

        bot.clear_step_handler_by_chat_id(message.chat.id)
        bot.register_next_step_handler(send_message, get_password_message)

    elif password.lower() == 'відміна':
        bot.send_message(message.chat.id, 'Відмінено.', reply_markup=markup.markup_main())
        return

    elif core.valid_password(password) == True:
        core.delete_password(password)
        core.add_agent(user_id)

        bot.send_message(message.chat.id, '🔑 Ви авторизовані як Агент підтримки', parse_mode='html', reply_markup=markup.markup_main())
        bot.send_message(message.chat.id, 'Виберіть панель технічної підтримки:', parse_mode='html', reply_markup=markup.markup_agent())

    else:
        send_message = bot.send_message(message.chat.id, '⚠️ Неправильний пароль. Спробуйте ще раз.', reply_markup=markup.markup_cancel())

        bot.clear_step_handler_by_chat_id(message.chat.id)
        bot.register_next_step_handler(send_message, get_password_message)


def get_agent_id_message(message):
    agent_id = message.text

    if agent_id == None:
        take_agent_id_message = bot.send_message(message.chat.id, '⚠️ Ви відправляєте не текст. Спробуйте ще раз.', reply_markup=markup.markup_cancel())

        bot.clear_step_handler_by_chat_id(message.chat.id)
        bot.register_next_step_handler(take_agent_id_message, get_agent_id_message)

    elif agent_id.lower() == 'відміна':
        bot.send_message(message.chat.id, 'Відмінено.', reply_markup=markup.markup_main())
        return

    else:
        core.add_agent(agent_id)
        bot.send_message(message.chat.id, '✅ Агент успішно добавлений.', reply_markup=markup.markup_main())
        bot.send_message(message.chat.id, 'Виберіть розділ адмін панелі:', reply_markup=markup.markup_admin())


def get_new_request(message):
    request = message.text
    user_id = message.from_user.id
    check_file = core.get_file(message)

    #Якщо користувач відправляє файл
    if check_file != None:
        file_id = check_file['file_id']
        file_name = check_file['file_name']
        type = check_file['type']
        request = check_file['text']

        if str(request) == 'None':
            take_new_request = bot.send_message(message.chat.id, '⚠️ Ви не ввели ваш запит. Спробуйт ще раз, відправивши текст разом з файлом.', reply_markup=markup.markup_cancel())

            bot.clear_step_handler_by_chat_id(message.chat.id)
            bot.register_next_step_handler(take_new_request, get_new_request)

        else:
            req_id = core.new_req(user_id, request)
            core.add_file(req_id, file_id, file_name, type)

            bot.send_message(message.chat.id, f'✅ Ваш запит під ID {req_id} створено. Подивитись Активні запити можна нажавши кнопку <b>Мої активні запити </b>', parse_mode='html', reply_markup=markup.markup_main())        
    
    #Якщо користувач надсилає тільки текст
    else:
        if request == None:
            take_new_request = bot.send_message(message.chat.id, '⚠️ Відправлений вами тип даних не підтримується ботом. Спробуйте ще раз відправити ваш запит, використавши тільки доступний тип даних, (текст, файли, фото, відео, аудіо, голосове повідомлення.)', reply_markup=markup.markup_cancel())

            bot.clear_step_handler_by_chat_id(message.chat.id)
            bot.register_next_step_handler(take_new_request, get_new_request)

        elif request.lower() == 'відміна':
            bot.send_message(message.chat.id, 'Відміна.', reply_markup=markup.markup_main())
            return

        else:
            req_id = core.new_req(user_id, request)
            bot.send_message(message.chat.id, f'✅ Ваш запит під ID {req_id} створено. Подивитись ваші активні запити можна нажавши кнопку<b>Мої активні запити</b>', parse_mode='html', reply_markup=markup.markup_main())


def get_additional_message(message, req_id, status):
    additional_message = message.text
    check_file = core.get_file(message)
    
    #Якщо користувач відправляє файл
    if check_file != None:
        file_id = check_file['file_id']
        file_name = check_file['file_name']
        type = check_file['type']
        additional_message = check_file['text']

        core.add_file(req_id, file_id, file_name, type)

    if additional_message == None:
        take_additional_message = bot.send_message(chat_id=message.chat.id, text='⚠️ Відправлений вами тим даних не підтримується ботом. Спробуйте ще раз надіслати ваше повідомлення, Використовуючи один з типів даних, (текст, файли, фото, відео, аудіо, голосове повідомлення).', reply_markup=markup.markup_cancel())

        bot.clear_step_handler_by_chat_id(message.chat.id)
        bot.register_next_step_handler(take_additional_message, get_additional_message, req_id, status)

    elif additional_message.lower() == 'відміна':
        bot.send_message(message.chat.id, 'Відміна.', reply_markup=markup.markup_main())
        return

    else:
        if additional_message != 'None':
            core.add_message(req_id, additional_message, status)

        if check_file != None:
            if additional_message != 'None':
                text = '✅ Ваш файл і повідолмення було успішно відправлене!'
            else:
                text = '✅ Ваш файл успішно надіслано!'
        else:
            text = '✅ Ваше повідомлення успішно надіслано!'
        
        bot.send_message(message.chat.id, text, reply_markup=markup.markup_main())

        if status == 'agent':
            user_id = core.get_user_id_of_req(req_id)
            try:
                if additional_message == 'None':
                    additional_message = ''

                bot.send_message(user_id, f'⚠️ Отримати нову відповідь на ваш запит ID {req_id}!\n\n🧑‍💻 Відповідь агента підтримки:\n{additional_message}', reply_markup=markup.markup_main())

                if type == 'photo':
                    bot.send_photo(user_id, photo=file_id, reply_markup=markup.markup_main())
                elif type == 'document':
                    bot.send_document(user_id, data=file_id, reply_markup=markup.markup_main())
                elif type == 'video':
                    bot.send_video(user_id, data=file_id, reply_markup=markup.markup_main())
                elif type == 'audio':
                    bot.send_audio(user_id, audio=file_id, reply_markup=markup.markup_main())
                elif type == 'voice':
                    bot.send_voice(user_id, voice=file_id, reply_markup=markup.markup_main())
                else:
                    bot.send_message(user_id, additional_message, reply_markup=markup.markup_main())
            except:
                pass
        

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id

    if call.message:
        if ('my_reqs:' in call.data) or ('waiting_reqs:' in call.data) or ('answered_reqs:' in call.data) or ('confirm_reqs:' in call.data):
            """
            Обробник кнопок для:

            ✉️ Мої запити
            ❗️ Чекають відповідь від підтримки,
            ⏳ Чекають відповідь від користувача
            ✅ Завершені запити 
            """

            parts = call.data.split(':')
            callback = parts[0]
            number = parts[1]
            markup_and_value = markup.markup_reqs(user_id, callback, number)
            markup_req = markup_and_value[0]
            value = markup_and_value[1]

            if value == 0:
                bot.send_message(chat_id=call.message.chat.id, text='⚠️ Запит не знайдено.', reply_markup=markup.markup_main())
                bot.answer_callback_query(call.id)
                return

            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Нажміть на запит, щоб подивитись історію листування, або добавити повідомлення:', reply_markup=markup_req)
            except:
                bot.send_message(chat_id=call.message.chat.id, text='Ваші запити:', reply_markup=markup_req)

            bot.answer_callback_query(call.id)

        #Відкрити запит
        elif 'open_req:' in call.data:
            parts = call.data.split(':')
            req_id = parts[1]
            callback = parts[2]

            req_status = core.get_req_status(req_id)
            request_data = core.get_request_data(req_id, callback)
            len_req_data = len(request_data)

            i = 1
            for data in request_data:
                if i == len_req_data:
                    markup_req = markup.markup_request_action(req_id, req_status, callback)
                else:
                    markup_req = None

                bot.send_message(chat_id=call.message.chat.id, text=data, parse_mode='html', reply_markup=markup_req)

                i += 1

            bot.answer_callback_query(call.id)

        #Добавити повідомлення в запит
        elif 'add_message:' in call.data:
            parts = call.data.split(':')
            req_id = parts[1]
            status_user = parts[2]

            take_additional_message = bot.send_message(chat_id=call.message.chat.id, text='Відправте ваше повідомлення, Використавши один з видівданих: (текст, файли, фото, відео, аудіо, голосове повідолмення)', reply_markup=markup.markup_cancel())

            bot.register_next_step_handler(take_additional_message, get_additional_message, req_id, status_user)

            bot.answer_callback_query(call.id)

        #Завершити запит
        elif 'confirm_req:' in call.data:
            parts = call.data.split(':')
            confirm_status = parts[1]
            req_id = parts[2]

            if core.get_req_status(req_id) == 'confirm':
                bot.send_message(chat_id=call.message.chat.id, text="⚠️ Цей запит вже завершений .", reply_markup=markup.markup_main())
                bot.answer_callback_query(call.id)

                return
            
            #Запросити підтвердження завершення
            if confirm_status == 'wait':
                bot.send_message(chat_id=call.message.chat.id, text="Для завершення запиту - нажміть кнопку <b>Підтвердити</b>", parse_mode='html', reply_markup=markup.markup_confirm_req(req_id))
            
            #Підтвердити завершення
            elif confirm_status == 'true':
                core.confirm_req(req_id)
                
                try:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✅ Запит успішно завершений.", reply_markup=markup.markup_main())
                except:
                    bot.send_message(chat_id=call.message.chat.id, text="✅ Запит успішно завершений.", reply_markup=markup.markup_main())

                bot.answer_callback_query(call.id)

        #Файли запису
        elif 'req_files:' in call.data:
            parts = call.data.split(':')
            req_id = parts[1]
            callback = parts[2]
            number = parts[3]

            markup_and_value = markup.markup_files(number, req_id, callback)
            markup_files = markup_and_value[0]
            value = markup_and_value[1]

            if value == 0:
                bot.send_message(chat_id=call.message.chat.id, text='⚠️ Файли не знайдені.', reply_markup=markup.markup_main())
                bot.answer_callback_query(call.id)
                return

            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Нажміть на файл, щоб отримати його.', reply_markup=markup_files)
            except:
                bot.send_message(chat_id=call.message.chat.id, text='Нажміть на файл, щоб отримати його.', reply_markup=markup_files)

            bot.answer_callback_query(call.id)

        #Відправити файл.
        elif 'send_file:' in call.data:
            parts = call.data.split(':')
            id = parts[1]
            type = parts[2]

            file_id = core.get_file_id(id)

            if type == 'photo':
                bot.send_photo(call.message.chat.id, photo=file_id, reply_markup=markup.markup_main())
            elif type == 'document':
                bot.send_document(call.message.chat.id, data=file_id, reply_markup=markup.markup_main())
            elif type == 'video':
                bot.send_video(call.message.chat.id, data=file_id, reply_markup=markup.markup_main())
            elif type == 'audio':
                bot.send_audio(call.message.chat.id, audio=file_id, reply_markup=markup.markup_main())
            elif type == 'voice':
                bot.send_voice(call.message.chat.id, voice=file_id, reply_markup=markup.markup_main())
            
            bot.answer_callback_query(call.id)

        #Повернутись назад в панель агента
        elif call.data == 'back_agent':
            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🔑 Ви авторизовані як Агент підтримки', parse_mode='html', reply_markup=markup.markup_agent())
            except:
                bot.send_message(call.message.chat.id, '🔑 Ви авторизовані як Агент підтримки', parse_mode='html', reply_markup=markup.markup_agent())

            bot.answer_callback_query(call.id)

        #Повернутись назад в панель адміна
        elif call.data == 'back_admin':
            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='🔑 Ви авторизовані як Адмін.', parse_mode='html', reply_markup=markup.markup_admin())
            except:
                bot.send_message(call.message.chat.id, '🔑 Ви авторизовані як Адмін', parse_mode='html', reply_markup=markup.markup_admin())

            bot.answer_callback_query(call.id)

        #Добавити Агента
        elif call.data == 'add_agent':
            take_agent_id_message = bot.send_message(chat_id=call.message.chat.id, text='Щоб добавити Агента підтримки - введіть його ID Telegram.', reply_markup=markup.markup_cancel())
            bot.register_next_step_handler(take_agent_id_message, get_agent_id_message)

        #Всі агенти
        elif 'all_agents:' in call.data:
            number = call.data.split(':')[1]
            markup_and_value = markup.markup_agents(number)
            markup_agents = markup_and_value[0]
            len_agents = markup_and_value[1]

            if len_agents == 0:
                bot.send_message(chat_id=call.message.chat.id, text='⚠️ Агентів не знайдено.', reply_markup=markup.markup_main())
                bot.answer_callback_query(call.id)
                return

            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Нажміть на Агента підтримки, щоб видалити його.', parse_mode='html', reply_markup=markup_agents)
            except:
                bot.send_message(call.message.chat.id, 'Нажміть на Агента підтримки, щоб видалити його', parse_mode='html', reply_markup=markup_agents)

            bot.answer_callback_query(call.id)

        #Видалити агента
        
        elif 'delete_agent:' in call.data:
            agent_id = call.data.split(':')[1]
            core.delete_agent(agent_id)

            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Нажміть на Агента підтримки, щоб видалити його', parse_mode='html', reply_markup=markup.markup_agents('1')[0])
            except:
                bot.send_message(call.message.chat.id, 'Нажміть на агента підтримки, щоб видалити його', parse_mode='html', reply_markup=markup.markup_agents('1')[0])

            bot.answer_callback_query(call.id)

        #Всі паролі
        elif 'all_passwords:' in call.data:
            number = call.data.split(':')[1]
            markup_and_value = markup.markup_passwords(number)
            markup_passwords = markup_and_value[0]
            len_passwords = markup_and_value[1]

            if len_passwords == 0:
                bot.send_message(chat_id=call.message.chat.id, text='⚠️ Паролі не знайдено.', reply_markup=markup.markup_main())
                bot.answer_callback_query(call.id)
                return

            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Нажміть на пароль, щоб видалити його', parse_mode='html', reply_markup=markup_passwords)
            except:
                bot.send_message(call.message.chat.id, 'Нажміть на пароль, щоб видалити його ', parse_mode='html', reply_markup=markup_passwords)

            bot.answer_callback_query(call.id)

        #Видалити пароль
        elif 'delete_password:' in call.data:
            password = call.data.split(':')[1]
            core.delete_password(password)

            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Нажміть на пароль, щоб видалити його', parse_mode='html', reply_markup=markup.markup_passwords('1')[0])
            except:
                bot.send_message(call.message.chat.id, 'Нажміть на пароль, щоб видалити його', parse_mode='html', reply_markup=markup.markup_passwords('1')[0])

            bot.answer_callback_query(call.id)

        #Згенерувати пароль
        elif call.data == 'generate_passwords':
            #10 - кількість паролів, 16 - довжина пароля
            passwords = core.generate_passwords(10, 16) 
            core.add_passwords(passwords)

            text_passwords = ''
            i = 1
            for password in passwords:
                text_passwords += f'{i}. {password}\n'
                i += 1
            
            bot.send_message(call.message.chat.id, f"✅ Згенеровано {i-1} паролів:\n\n{text_passwords}", parse_mode='html', reply_markup=markup.markup_main())
            bot.send_message(call.message.chat.id, 'Нажміть на пароль, щоб видалити его', parse_mode='html', reply_markup=markup.markup_passwords('1')[0])

            bot.answer_callback_query(call.id)

        #Зупинити бота
        elif 'stop_bot:' in call.data:
            status = call.data.split(':')[1]

            #Запросити підтвердження на вимкнення
            if status == 'wait':
                try:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Ви точно хочете зупинити бота ?", parse_mode='html', reply_markup=markup.markup_confirm_stop())
                except:
                    bot.send_message(call.message.chat.id, f"Ви точно хочете зупинити бота?", parse_mode='html', reply_markup=markup.markup_confirm_stop())

            #Підтверддення получено
            elif status == 'confirm':
                try:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='✅ Бот вимкнено.')
                except:
                    bot.send_message(chat_id=call.message.chat.id, text='✅ Бот вимкнено.')

                bot.answer_callback_query(call.id)
                bot.stop_polling()
                sys.exit()


if __name__ == "__main__":
    bot.polling(none_stop=True)