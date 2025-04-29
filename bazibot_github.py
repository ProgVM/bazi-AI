import os
import json
import time
import random
import telebot
import shutil
import subprocess
from telebot.apihelper import ApiTelegramException
import threading
from threading import Timer
from gtts import gTTS
from googletrans import Translator # Нужна версия 4.0.0-rc1
import pretty_midi
import pymorphy2
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Путь к директории с кодом

# Директория для хранения словарей чатов и резервных копий
DATA_DIR = 'chats'
BACKUP_DIR = 'backup_chats'
SOURCE_DIR = 'src'

# Создаем директории, если они не существуют
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(SOURCE_DIR, exist_ok=True)

# Инициализация переводчика
translator = Translator()

# Список реакций (эмодзи)
reactions = [
    "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱",
    "🤬", "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡",
    "🥱", "🥴", "😍", "🐳", "❤️", "🔥", "🌚", "🌭", "💯", "🤣",
    "⚡️", "🍌", "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕",
    "😈", "😴", "😭", "🤓", "👻", "👨", "👀", "🎃", "🙈", "😇",
    "😨", "🤝", "✍", "🤗", "🫡", "🎅", "🎄", "☃️", "💅", "🤪",
    "🗿", "🆒", "💘", "🙉", "🦄", "😘", "💊", "🙊", "😎", "👾",
    "🤷", "😡", "СОСАЛ?"
]

# Список текстовых эмодзи
text_emojis = [":)", ":_)", ";)", ";_)", ":(", ":_(", ";(", ";_(", "=)", "=_)", "=( ", "=_(", ":1", "=1", ":3", "3:", "=3", "3=", ":D", "D:", ";D", "D;", "=D", "D=", ":0", "=0", "XD", "xd", ":c", "=c", ":o", "=o", ":>", ":<", "=>", "=<", "8)", "8(", "8o", ":/", ";/", "=/", "0_0", "-_-", "-_,-", "~_~", "~-~", "T_T", "U_U", "^_^", "^-^", "X)", "X(", "x)", "x(", "0w0", "UwU", "-w-", "%)", "$_$", ":]", ":[", "=]", "=[", "0~0", "-~-", ">:)", "<:)", ">:(", "<:(", ">;)", "<;)", ">;(", "<;(", ">=)", "<=)", ">=(", "<=(", ">:D", "<:D", "D:<", "D:>", ">;D", "<;D", "D;<", "D;>", ">=D", "<=D", "D=<", "D=>", ">:3", "<:3", "3:<", "3:>", ">=3", "<=3", "3=<", "3=>", ">:0", "<:0", ">=0", "<=0", ">:>", "<:>", ">:<", "<:<", ">=>", "<=>", ">=<", "<=<", ">:]", "<:]", ">:[", "<:[", ">;]", "<;]", ">;[", "<;[", ">=]", "<=]", "]=[", "<=[", "}:)", "{:)", "}:(", "{:(", "};)", "{;)", "};(", "{;(", "}=)", "{=)", "}=(", "{=(", "}:D", "{:D", "D:{", "D:}", "};D", "{;D", "D;{", "D;}", "}=D", "{=D", "D={", "D=}", "}:3", "{:3", "3:{", "3:}", "}=3", "{=3", "3={", "3=}", "}:0", "{:0", "}=0", "{=0", "}:>", "{:>", "}:<", "{:<", "}=>", "{=>", "}=<", "{=<", "}:]", "{:]", "}:[", "{:[", "};]", "{;]", "};[", "{;[", "}=]", "{=]", "}=[", "{=[", ":&", ";&", "=&", ":?", ";?", "=?" , "'_'", "'-'", "( ‌° ‌ʖ ‌°)", "(◕‿◕✿)"]


morph = pymorphy2.MorphAnalyzer()

adjectives = ["красивый", "большой", "маленький", "умный", "добрый", "сильный", "быстрый", "медленный", "интересный", "скучный"]
verbs = ["бегает", "прыгает", "летает", "спит", "ест", "читает", "пишет", "работает", "играет", "мечтает"]

# Список доступных инструментов (названия и их номера)
INSTRUMENTS = {
    "пианино" or "фортепиано": 0,
    "гитара": 24,
    "вибрафон": 11,
    "саксофон": 65,
    "труба": 56,
    "скрипка": 40,
    "флейта": 73,
    "ударные": 118,
    "орган": 19,
    "синтезатор": 90,
}

# Создаем экземпляр бота
TOKEN = "токен крутой"  # Замените на ваш токен
bot = telebot.TeleBot(TOKEN)

# Логирование
def log(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

# Функция для загрузки словаря из файла
def load_chat_data(chat_id):
    chat_dir = os.path.join(DATA_DIR, str(chat_id))
    os.makedirs(chat_dir, exist_ok=True)
    file_path = os.path.join(chat_dir, 'data.json')
    settings_path = os.path.join(chat_dir, 'settings.json')
    timers_path = os.path.join(chat_dir, 'timers.json')  # Путь для таймеров
    stickers_dir = os.path.join(chat_dir, 'stickers')  # Папка для стикеров

    # Создаем директорию для стикеров, если она не существует
    os.makedirs(stickers_dir, exist_ok=True)

    # Создание файла настроек, если он не существует
    if not os.path.exists(settings_path):
        settings = {
            "activity": 5,
            "voice": "ru",
            "restart_count": 0,
            "language": "en",  # Установим язык по умолчанию
            "auto_translate": False  # Авто-перевод выключен по умолчанию
        }
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    # Проверка наличия файла данных
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'last_message_sent' not in data:
                    data['last_message_sent'] = 0
                # Обновляем title на основе названия чата
                chat_info = bot.get_chat(chat_id)
                data['title'] = chat_info.title
                return data
        except (json.JSONDecodeError, UnicodeDecodeError):
            log(f"Ошибка декодирования JSON в файле {file_path}. Восстанавливаем из резервной копии.")
            backup_chat_dir = os.path.join(BACKUP_DIR, str(chat_id))
            backup_file_path = os.path.join(backup_chat_dir, 'data.json')
            if os.path.exists(backup_file_path):
                shutil.copy(backup_file_path, file_path)  # Восстанавливаем из резервной копии
                log(f"Данные успешно восстановлены из резервной копии для чата {chat_id}.")
                return load_chat_data(chat_id)  # Загружаем восстановленные данные
            else:
                log(f"Резервная копия для чата {chat_id} не найдена. Создаем новый файл.")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({'messages': [], 'last_active': time.time(), 'active_count': 0, 'last_message_sent': 0, 'chat_id': chat_id, 'title': f"ID{chat_id}"}, f, ensure_ascii=False, indent=4)
                return load_chat_data(chat_id)
    else:
        # Если файла нет, создаем его с начальными значениями
        chat_info = bot.get_chat(chat_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'messages': [], 'last_active': time.time(), 'active_count': 0, 'last_message_sent': 0, 'chat_id': chat_id, 'title': chat_info.title}, f, ensure_ascii=False, indent=4)

    # Создание файла для таймеров, если он не существует
    if not os.path.exists(timers_path):
        with open(timers_path, 'w', encoding='utf-8') as f:
            json.dump([], f)  # Инициализируем пустой список таймеров

    return {'messages': [], 'last_active': time.time(), 'active_count': 0, 'last_message_sent': 0, 'chat_id': chat_id, 'title': chat_info.title}

# Функция для сохранения словаря в файл
def save_chat_data(chat_id, data):
    chat_dir = os.path.join(DATA_DIR, str(chat_id))
    os.makedirs(chat_dir, exist_ok=True)
    file_path = os.path.join(chat_dir, 'data.json')

    backup_chat_dir = os.path.join(BACKUP_DIR, str(chat_id))
    if os.path.exists(chat_dir):
        shutil.copytree(chat_dir, backup_chat_dir, dirs_exist_ok=True)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        log(f"Ошибка записи в файл {file_path}: {e}")
        if os.path.exists(backup_chat_dir):
            shutil.rmtree(chat_dir)
            shutil.copytree(backup_chat_dir, chat_dir)
            log(f"Восстановлена резервная копия для чата {chat_id}.")

# Обработка медиа-сообщений
@bot.message_handler(content_types=['photo', 'audio', 'video', 'document'])
def handle_media(message):
    chat_id = message.chat.id
    chat_dir = os.path.join(DATA_DIR, str(chat_id), 'media')
    os.makedirs(chat_dir, exist_ok=True)

    # Определяем, какой файл загружается
    if message.content_type == 'document':
        file_info = bot.get_file(message.document.file_id)
        file_size = message.document.file_size
        file_name = message.document.file_name
    else:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_size = message.photo[-1].file_size
        file_name = file_info.file_path.split('/')[-1]

    # Проверка на размер файла
    if file_size > 50 * 1024 * 1024:  # 20 МБ
        bot.reply_to(message, "Я хотел использовать это медиа, но мне разработчик запретил скачивать файлы размером больше 20 МБ.")
        return

    downloaded_file = bot.download_file(file_info.file_path)
    with open(os.path.join(chat_dir, file_name), 'wb') as new_file:
        new_file.write(downloaded_file)

    log(f"Файл {file_name} загружен в чат {chat_id}.")

# Функция для генерации сообщения из слов
def generate_response(chat_data):
    if not chat_data['messages']:
        return "Я настолько тупой (Ваш IQ × мой IQ = 0, благодаря мне), что я не могу ничего сказать."

    words = []
    for message in chat_data['messages']:
        words.extend(message.split())

    if not words:
        return "Я настолько тупой (Ваш IQ × мой IQ = 0, благодаря мне), что я не могу ничего сказать."

    if random.random() < 0.1:  # 10% шанс вставить текстовый эмодзи
        words.append(random.choice(text_emojis))

    response_length = random.randint(1, 15)
    response = ' '.join(random.choice(words) for _ in range(response_length))
    return response

# Функция для генерации голосового сообщения
def generate_voice_message(text, chat_id):
    chat_dir = os.path.join(DATA_DIR, str(chat_id), 'voice')
    os.makedirs(chat_dir, exist_ok=True)

    output_file = os.path.join(chat_dir, f"voice_message_{int(time.time())}.ogg")

    # Загружаем настройки чата
    settings_path = os.path.join(DATA_DIR, str(chat_id), 'settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            voice = settings.get('voice', 'ru')  # По умолчанию используем 'ru'

    try:
        tts = gTTS(text=text, lang=voice)
        tts.save(output_file)
    except ValueError as e:
        log(f"Ошибка при генерации голоса: {e}")
        return None  # Возвращаем None, если язык не поддерживается

    return output_file

# Функция для сохранения стикеров, отправленных пользователями
def save_user_sticker(chat_id, sticker_id):
    stickers_file = os.path.join(DATA_DIR, str(chat_id), 'stickers.json')
    stickers_dir = os.path.join(DATA_DIR, str(chat_id), 'stickers')
    os.makedirs(stickers_dir, exist_ok=True)

    # Сохраняем стикер в формате .webp
    file_info = bot.get_file(sticker_id)
    sticker_path = os.path.join(stickers_dir, f"{sticker_id}.webp")
    downloaded_file = bot.download_file(file_info.file_path)

    with open(sticker_path, 'wb') as f:
        f.write(downloaded_file)

    if os.path.exists(stickers_file):
        with open(stickers_file, 'r', encoding='utf-8') as f:
            stickers = json.load(f)
    else:
        stickers = []

    if sticker_id not in stickers:
        stickers.append(sticker_id)

    with open(stickers_file, 'w', encoding='utf-8') as f:
        json.dump(stickers, f, ensure_ascii=False)

# Функция для загрузки таймеров из файла
def load_timers(chat_id):
    timers_file = os.path.join(DATA_DIR, str(chat_id), 'timers.json')
    if os.path.exists(timers_file):
        with open(timers_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Функция для сохранения таймеров в файл
def save_timers(chat_id, timers):
    timers_file = os.path.join(DATA_DIR, str(chat_id), 'timers.json')
    with open(timers_file, 'w', encoding='utf-8') as f:
        json.dump(timers, f, ensure_ascii=False, indent=4)

# Функция для обработки завершения таймера
def timer_thread(chat_id, duration, command, user_id):
    time.sleep(duration)

    # Отправляем сообщение о завершении таймера
    bot.send_message(chat_id, f"Таймер завершен! Выполняем команду: {command}")

    # Выполняем команду, если это возможно
    commands = command.splitlines()  # Разделяем команды по строкам
    for cmd in commands:
        if cmd.startswith('/'):
            if cmd.startswith('/genv '):
                user_input = cmd[len('/genv '):].strip()  # Получаем текст после команды
                if not user_input:  # Если нет данных, генерируем случайное сообщение
                    user_input = generate_response({'messages': []})  # Генерируем случайное сообщение
                voice_file = generate_voice_message(user_input, chat_id)
                if voice_file is not None:
                    with open(voice_file, 'rb') as f:
                        bot.send_voice(chat_id, f)
                else:
                    bot.send_message(chat_id, "Указанный язык не дружит с TTS. Пожалуйста, выберите другой язык, например /voice ru.")
            elif cmd.startswith('/gent '):
                user_input = cmd[len('/gent '):].strip()  # Получаем текст после команды
                if not user_input:  # Если нет данных, генерируем случайное сообщение
                    user_input = generate_response({'messages': []})  # Генерируем случайное сообщение
                response = generate_response({'messages': [user_input]})
                bot.send_message(chat_id, response)
            elif cmd.startswith('/genm '):
                user_input = cmd[len('/genm '):].strip()  # Получаем текст после команды
                media_files = os.listdir(os.path.join(DATA_DIR, str(chat_id), 'media'))
                if media_files:
                    selected_files = random.sample(media_files, min(len(media_files), 3))  # Выбираем до 3 медиафайлов
                    for media_file in selected_files:
                        media_path = os.path.join(DATA_DIR, str(chat_id), 'media', media_file)
                        caption = generate_response({'messages': [user_input]}) if user_input else generate_response({'messages': []})  # Генерируем подпись
                        if media_file.endswith(('.jpg', '.png')):
                            with open(media_path, 'rb') as f:
                                bot.send_photo(chat_id, f, caption=caption)
                        elif media_file.endswith(('.mp4', '.avi')):
                            with open(media_path, 'rb') as f:
                                bot.send_video(chat_id, f, caption=caption)
                        elif media_file.endswith(('.ogg', '.mp3')):
                            with open(media_path, 'rb') as f:
                                bot.send_audio(chat_id, f, caption=caption)
                        else:
                            with open(media_path, 'rb') as f:
                                bot.send_document(chat_id, f, caption=caption)
                else:
                    bot.send_message(chat_id, "Извини, но на данный момент в папке чата в моей системе нет медиа.")

    # Удаляем таймер из файла после завершения
    timers = load_timers(chat_id)
    timers = [timer for timer in timers if timer['command'] != command]  # Удаляем завершенный таймер
    save_timers(chat_id, timers)  # Сохраняем обновленный список таймеров

# Команда для установки таймера
@bot.message_handler(commands=['timer'])
def set_timer(message):
    chat_id = message.chat.id
    user_id = message.from_user.id  # Получаем ID пользователя
    lines = message.text.splitlines()

    if len(lines) < 2:
        bot.send_message(chat_id, "Пожалуйста, введите таймер и команду на двух строках.")
        return

    timer_string = lines[0].strip()
    # Объединяем все строки, начиная со второй, в одну команду
    command = '\n'.join(lines[1:]).strip()

    # Загружаем текущие таймеры
    timers = load_timers(chat_id)

    # Проверяем лимит таймеров
    if len(timers) >= 25:
        bot.send_message(chat_id, "Достигнут лимит в 25 таймеров. Пожалуйста, остановите некоторые из них.")
        return

    # Парсим строку таймера
    time_components = {
        'years': 0,
        'months': 0,
        'days': 0,
        'hours': 0,
        'minutes': 0,
        'seconds': 0
    }

    # Разбиваем строку по пробелам и обрабатываем
    for part in timer_string.split():
        if part.endswith('y'):
            time_components['years'] = int(part[:-1])
        elif part.endswith('m'):
            time_components['months'] = int(part[:-1])
        elif part.endswith('d'):
            time_components['days'] = int(part[:-1])
        elif part.endswith('h'):
            time_components['hours'] = int(part[:-1])
        elif part.endswith('min'):
            time_components['minutes'] = int(part[:-3])
        elif part.endswith('s'):
            time_components['seconds'] = int(part[:-1])

    # Преобразуем все в секунды
    total_seconds = (time_components['years'] * 365 * 24 * 3600 +
                     time_components['months'] * 30 * 24 * 3600 +
                     time_components['days'] * 24 * 3600 +
                     time_components['hours'] * 3600 +
                     time_components['minutes'] * 60 +
                     time_components['seconds'])

    # Создаем новый таймер и добавляем его в список
    timers.append({'duration': total_seconds, 'command': command, 'user_id': user_id})

    # Сохраняем обновленные таймеры
    save_timers(chat_id, timers)

    # Запускаем поток для таймера
    threading.Thread(target=timer_thread, args=(chat_id, total_seconds, command, user_id)).start()
    bot.send_message(chat_id, f"Таймер установлен на {total_seconds} секунд. Команда: {command}")

# Команда для остановки таймера
@bot.message_handler(commands=['stoptimer'])
def stop_timer(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Проверка, является ли пользователь администратором
    admins = bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]
    if user_id not in admin_ids:
        bot.send_message(chat_id, "Эта команда доступна только администраторам.")
        return

    # Получаем номер таймера
    try:
        timer_number = int(message.text.split()[1]) - 1  # Номера таймеров начинаются с 0
    except (IndexError, ValueError):
        bot.send_message(chat_id, "Пожалуйста, укажите номер таймера для остановки.")
        return

    # Загружаем текущие таймеры
    timers = load_timers(chat_id)

    # Проверяем, существует ли таймер
    if 0 <= timer_number < len(timers):
        del timers[timer_number]  # Удаляем таймер из списка
        save_timers(chat_id, timers)  # Сохраняем обновленный список таймеров
        bot.send_message(chat_id, f"Таймер номер {timer_number + 1} остановлен.")
    else:
        bot.send_message(chat_id, "Такого таймера не существует.")

# Команда для отображения активных таймеров
@bot.message_handler(commands=['timers'])
def show_timers(message):
    chat_id = message.chat.id
    timers = load_timers(chat_id)

    if not timers:
        bot.send_message(chat_id, "Нет активных таймеров.")
        return

    response = "Активные таймеры:\n"
    for i, timer in enumerate(timers, start=1):
        duration = timer['duration']
        command = timer['command']
        response += f"{i}. Таймер на {duration} секунд. Команда: {command}\n"

    bot.send_message(chat_id, response)

# Функция для очистки медиа и голосовых сообщений
def clean_media_files(chat_id):
    # Очистка медиа и голосовых файлов в основной папке
    media_dir = os.path.join(DATA_DIR, str(chat_id), 'media')
    voice_dir = os.path.join(DATA_DIR, str(chat_id), 'voice')
    music_dir = os.path.join(DATA_DIR, str(chat_id), 'music')  # Папка для музыки

    # Очистка медиа и голосовых файлов в резервной папке
    backup_media_dir = os.path.join(BACKUP_DIR, str(chat_id), 'media')
    backup_voice_dir = os.path.join(BACKUP_DIR, str(chat_id), 'voice')
    backup_music_dir = os.path.join(BACKUP_DIR, str(chat_id), 'music')  # Резервная папка для музыки

    # Удаляем содержимое папок
    if os.path.exists(media_dir):
        shutil.rmtree(media_dir)
        os.makedirs(media_dir)  # Создаем заново
    if os.path.exists(voice_dir):
        shutil.rmtree(voice_dir)
        os.makedirs(voice_dir)  # Создаем заново
    if os.path.exists(music_dir):
        shutil.rmtree(music_dir)
        os.makedirs(music_dir)  # Создаем заново
    if os.path.exists(backup_media_dir):
        shutil.rmtree(backup_media_dir)
        os.makedirs(backup_media_dir)  # Создаем заново
    if os.path.exists(backup_voice_dir):
        shutil.rmtree(backup_voice_dir)
        os.makedirs(backup_voice_dir)  # Создаем заново
    if os.path.exists(backup_music_dir):
        shutil.rmtree(backup_music_dir)
        os.makedirs(backup_music_dir)  # Создаем заново

# Запуск потока для консольного ввода
def console_input():
    while True:
        command = input()
        if command.startswith('/send '):
            message_text = command.replace('/send ', '')
            for chat_id in os.listdir(DATA_DIR):
                try:
                    chat_id_int = int(chat_id)
                    bot.send_message(chat_id_int, message_text)
                except ValueError:
                    continue
                except ApiTelegramException as e:
                    log(f"Ошибка при отправке сообщения в чат {chat_id_int}: {e}")

# Запуск потока для консольного ввода
threading.Thread(target=console_input, daemon=True).start()


@bot.message_handler(commands=['gent2'])
def generate_gent2_sentence(message):
    adj = random.choice(adjectives)
    verb = random.choice(verbs)

    adj_form = morph.parse(adj)[0]
    verb_form = morph.parse(verb)[0]

    #  Простая попытка согласования, но может быть не всегда корректной
    sentence = f"{adj_form.make_agree_with_number(1).word} {verb_form.make_agree_with_number(1).word}."
    bot.reply_to(message, sentence)


@bot.message_handler(commands=['gent2t'])
def generate_gent2t_sentence(message):
    adj = random.choice(adjectives)
    noun = "бази"

    # Analyze the noun to get its grammatical features
    noun_parse = morph.parse(noun)[0]
    noun_gram = noun_parse.tag

    # Extract relevant grammatical features from noun_gram (case, number, gender)
    gram_info = {
        'case': noun_gram.case,
        'number': noun_gram.number,
        'gender': noun_gram.gender
    }

    # Analyze the adjective and inflect it to agree with the noun
    adj_parse = morph.parse(adj)[0]
    try:
        adj_form = adj_parse.inflect(gram_info).word
    except Exception as e:  # Handle potential inflection errors
        adj_form = adj  # Fallback to original adjective if inflection fails

    # Analyze the verb and inflect it to agree with the noun. Handle person separately.
    verb = random.choice(verbs)
    verb_parse = morph.parse(verb)[0]

    # Choose person (1st or 2nd) randomly
    person = random.choice([1, 2])  # 1 for I/we, 2 for you

    #  Inflect the verb.  Note that person is handled separately from the noun agreement.
    try:
        verb_form = verb_parse.inflect({gram_info['number'], 'VERB', f'pers={person}'}).word
    except Exception as e:
        verb_form = verb


    sentence = f"У {adj_form} {noun} {verb_form}."
    bot.reply_to(message, sentence)











# Пасхалки
@bot.message_handler(commands=["baziVozmiPrimer"])
def vozmi_primer_message(message):
    bot.send_message(message.chat.id, "Сэр, взял, сэр!")

@bot.message_handler(commands=["baziOtpustiPrimer"])
def otpusti_primer_message(message):
    bot.send_message(message.chat.id, "Уже отпустил, сэр!")

@bot.message_handler(commands=["baziCyeshTapok"])
def cyesh_tapok_message(message):
    bot.send_message(message.chat.id, "Уже ем тапок, сэр... но это точно вкуснее, чем гоголь-моголь...")

@bot.message_handler(commands=['gena'])
def gena_message(message):
    bot.send_message(message.chat.id, "Вы нашли пасхалку шлепы класического :)))) здесь он поселелися")

@bot.message_handler(commands=['effect'])
def effect_message(message):
    bot.send_message(message.chat.id, "Эффектов не дам")

@bot.message_handler(commands=["zapou"])
def zapou_message(message):
    chance = random.randint(1, 1000)
    if chance == 1:
        bot.reply_to(message, f'ВЫ СЛОВИЛИ ЗАПОЙ ВЫ ВЕЗУНЧИК! {message.from_user.first_name} @{message.from_user.username} ')
    else:
        bot.reply_to(message, f'ВЫ не СЛОВИЛИ ЗАПОЙ:( {message.from_user.first_name} @{message.from_user.username} ')

@bot.message_handler(commands=["zapou_code_10_arab"])
def zapou_code_10_arab_message(message):
    chance2 = random.randint(1, 10)
    if chance2 == 1:
        bot.reply_to(message, f'ВЫ СЛОВИЛИ ЗАПОЙ ВЫ ВЕЗУНЧИК! {message.from_user.first_name} @{message.from_user.username} ')
    else:
        bot.reply_to(message, f'ВЫ не СЛОВИЛИ ЗАПОЙ:( {message.from_user.first_name} @{message.from_user.username} ')


# Функция для создания опроса
@bot.message_handler(commands=['poll'])
def create_poll(message):
    log("Команда /poll получена")
    chat_id = message.chat.id
    chat_data = load_chat_data(chat_id)

    # Проверяем активность
    if chat_data.get('activity', 5) == 0:
        return

    user_input = message.text[len('/poll ' or '/poll@bazi_ai_bot '):].strip()  # Получаем текст после команды
    if user_input:
        question = user_input
        options = random.sample(chat_data['messages'], min(4, len(chat_data['messages'])))  # Выбираем случайные сообщения как варианты
    else:
        if len(chat_data['messages']) < 2:
            bot.send_message(chat_id, "Базарьте, пожалуйста, чтоб я мог сделать нескучный опрос.")
            return

        question = random.choice(chat_data['messages'])
        options = random.sample(chat_data['messages'], min(4, len(chat_data['messages'])))  # Выбираем случайные сообщения как варианты

    try:
        bot.send_poll(chat_id, question, options, is_anonymous=random.choice([True, False]))
        log("Опрос успешно отправлен.")
    except ApiTelegramException as e:
        log(f"Ошибка при отправке опроса: {e}")

# Команда /info
@bot.message_handler(commands=['info'])
def chat_info(message):
    chat_id = message.chat.id
    chat_data = load_chat_data(chat_id)
    num_chats = len(os.listdir(DATA_DIR))

    # Загрузка настроек для получения информации о голосе, активности и авто-переводе
    settings_path = os.path.join(DATA_DIR, str(chat_id), 'settings.json')
    voice = "не установлен"  # Значение по умолчанию, если файл не найден
    activity = "не установлена"  # Значение по умолчанию, если файл не найден
    restart_count = 0  # Значение по умолчанию для количества перезапусков
    language = "не установлен"  # Значение по умолчанию для языка
    auto_translate = "выключен"  # Значение по умолчанию для авто-перевода
    natural_language = "выключен"  # Значение по умолчанию для естественного языка

    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            voice = settings.get('voice', "не установлен")
            activity = settings.get('activity', "не установлена")
            restart_count = settings.get('restart_count', 0)  # Получаем количество перезапусков
            language = settings.get('language', "не установлен")  # Получаем установленный язык
            auto_translate = "включен" if settings.get('auto_translate', False) else "выключен"  # Получаем состояние авто-перевода
            natural_language = "включен" if settings.get('natural_language', False) else "выключен"  # Получаем состояние естественного языка

    # Получение места группы в топе
    groups_data = {}
    for chat_folder in os.listdir(DATA_DIR):
        chat_path = os.path.join(DATA_DIR, chat_folder, 'data.json')
        if os.path.exists(chat_path):
            try:
                with open(chat_path, 'r', encoding='utf-8') as f:
                    chat_info = json.load(f)
                    group_name = chat_info.get('title', f"ID{chat_folder}")
                    message_count = len(chat_info.get('messages', []))
                    groups_data[group_name] = message_count
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue  # Пропускаем, если файл поврежден

    # Сортируем группы по количеству сообщений
    sorted_groups = sorted(groups_data.items(), key=lambda x: x[1], reverse=True)

    # Определяем место группы
    group_place = next((index + 1 for index, (group, count) in enumerate(sorted_groups) if group == chat_data['title']), len(sorted_groups) + 1)

    info_message = (f"Информация о чате:\n"
                    f"ID чата: {chat_id}\n"
                    f"Название чата: {chat_data['title']}\n"
                    f"Количество зарегистрированных чатов: {num_chats}\n"
                    f"Количество сообщений в этом чате: {len(chat_data['messages'])}\n"
                    f"Последнее сообщение отправлено: {time.ctime(chat_data['last_message_sent']) if chat_data['last_message_sent'] else 'Нет сообщений'}\n"
                    f"Установленная активность бота: {activity}\n"
                    f"Установленный голос бота: {voice}\n"
                    f"Количество перезапусков словаря: {restart_count}\n"
                    f"Установленный язык: {language}\n"
                    f"Авто-перевод: {auto_translate}\n"
                    f"Естественный язык: {natural_language}\n"
                    f"Место группы в топе: {group_place} (всего групп: {len(groups_data)})")

    bot.send_message(chat_id, info_message)

# Команда для мгновенной генерации текстового сообщения
@bot.message_handler(commands=['gent'])
def generate_message(message):
    chat_id = message.chat.id
    chat_data = load_chat_data(chat_id)

    # Проверяем активность
    if chat_data.get('activity', 5) == 0:
        return

    user_input = message.text[len('/gent ' or '/gent@bazi_ai_bot '):].strip()  # Получаем текст после команды
    if user_input:
        response = generate_response({'messages': [user_input]})
    else:
        response = generate_response(chat_data)

    bot.send_message(chat_id, response)

# Команда для мгновенной генерации голосового сообщения
@bot.message_handler(commands=['genv'])
def generate_voice(message):
    chat_id = message.chat.id
    chat_data = load_chat_data(chat_id)

    if chat_data.get('activity', 5) == 0:
        return

    user_input = message.text[len('/genv ' or '/genv@bazi_ai_bot '):].strip()  # Получаем текст после команды
    if user_input:
        response = generate_response({'messages': [user_input]})
    else:
        response = generate_response(chat_data)

    voice_file = generate_voice_message(response, chat_id)
    if voice_file is None:
        bot.send_message(chat_id, "Указанный язык не дружит с TTS. Пожалуйста, выберите другой язык, например /voice ru.")
    else:
        with open(voice_file, 'rb') as f:
            bot.send_voice(chat_id, f)

@bot.message_handler(commands=['genm'])
def generate_media(message):
    chat_id = message.chat.id
    chat_data = load_chat_data(chat_id)

    if chat_data.get('activity', 5) == 0:
        return

    user_input = message.text[len('/genm ' or '/genm@bazi_ai_bot '):].strip()  # Получаем текст после команды
    if user_input:
        response = generate_response({'messages': [user_input]})
    else:
        response = generate_response(chat_data)

    media_files = os.listdir(os.path.join(DATA_DIR, str(chat_id), 'media'))
    if media_files:
        selected_files = random.sample(media_files, min(len(media_files), 3))  # Выбираем до 3 медиафайлов
        for media_file in selected_files:
            media_path = os.path.join(DATA_DIR, str(chat_id), 'media', media_file)
            caption = response  # Используем сгенерированное сообщение как подпись

            if media_file.endswith(('.jpg', '.png')):
                with open(media_path, 'rb') as f:
                    bot.send_photo(chat_id, f, caption=caption)
            elif media_file.endswith(('.mp4', '.avi')):
                with open(media_path, 'rb') as f:
                    bot.send_video(chat_id, f, caption=caption)
            elif media_file.endswith(('.ogg', '.mp3')):
                with open(media_path, 'rb') as f:
                    bot.send_audio(chat_id, f, caption=caption)
            else:
                with open(media_path, 'rb') as f:
                    bot.send_document(chat_id, f, caption=caption)
    else:
        bot.send_message(chat_id, "Извини, но на данный момент в папке чата в моей системе нет медиа. Отправь какое-нибудь медиа (например, фото), чтобы я смог генерировать такие сообщения :)")

# Команда мгновенной отправки случайного стикера
@bot.message_handler(commands=['rs'])
def random_sticker(message):
    chat_id = message.chat.id
    stickers_dir = os.path.join(DATA_DIR, str(chat_id), 'stickers')

    if os.path.exists(stickers_dir):
        sticker_files = [f for f in os.listdir(stickers_dir) if f.endswith('.webp')]
        if sticker_files:
            random_sticker_file = random.choice(sticker_files)
            sticker_path = os.path.join(stickers_dir, random_sticker_file)
            with open(sticker_path, 'rb') as f:
                bot.send_sticker(chat_id, f)
        else:
            bot.send_message(chat_id, "Извините, но в этом чате нет сохраненных стикеров.")
    else:
        bot.send_message(chat_id, "Извините, но в этом чате нет сохраненных стикеров.")

# Команда для изменения активности
@bot.message_handler(commands=['activity'])
def set_activity(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    admins = bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]

    if user_id in admin_ids:
        try:
            activity = int(message.text.split()[1])
            if 0 <= activity <= 10:  # Проверка диапазона активности
                # Сохранение активности в файл
                with open(os.path.join(DATA_DIR, str(chat_id), 'settings.json'), 'r+') as f:
                    settings = json.load(f)
                    settings['activity'] = activity
                    f.seek(0)
                    json.dump(settings, f, ensure_ascii=False, indent=4)
                    f.truncate()  # Обрезаем файл до новой длины
                bot.send_message(chat_id, f"Активность изменена на {activity}.")
            else:
                bot.send_message(chat_id, "Пожалуйста, укажите значение активности от 0 до 10.")
        except (IndexError, ValueError):
            bot.send_message(chat_id, "Что это за число такое?")
    else:
        bot.send_message(chat_id, "Извини, но ты малоадминен для этой команды, участник.")

# Команда для изменения голоса
@bot.message_handler(commands=['voice'])
def set_voice(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    admins = bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]

    if user_id in admin_ids:
        try:
            new_voice = message.text.split(maxsplit=1)[1]
            settings_path = os.path.join(DATA_DIR, str(chat_id), 'settings.json')

            if os.path.exists(settings_path):
                with open(settings_path, 'r+') as f:
                    settings = json.load(f)
                    settings['voice'] = new_voice
                    f.seek(0)
                    json.dump(settings, f, ensure_ascii=False, indent=4)
                    f.truncate()
            else:
                settings = {'voice': new_voice}
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=4)

            bot.send_message(chat_id, f"Голос изменен на '{new_voice}'.")
        except IndexError:
            bot.send_message(chat_id, "Пожалуйста, укажите название голоса. Например: 'ru' или 'en'.")
        except ValueError as e:
            bot.send_message(chat_id, "Указанный язык не дружит с TTS. Пожалуйста, выберите другой язык, например /voice ru.")
            log(f"Ошибка при изменении голоса: {e}")
    else:
        bot.send_message(chat_id, "Извини, но у тебя нет прав админа для этой команды.")

# Команда для установки языка
@bot.message_handler(commands=['lang'])
def set_language(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    admins = bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]

    if user_id in admin_ids:
        try:
            new_language = message.text.split()[1]
            settings_path = os.path.join(DATA_DIR, str(chat_id), 'settings.json')

            # Загружаем текущие настройки
            if os.path.exists(settings_path):
                with open(settings_path, 'r+') as f:
                    settings = json.load(f)
                    settings['language'] = new_language  # Устанавливаем новый язык
                    f.seek(0)
                    json.dump(settings, f, ensure_ascii=False, indent=4)
                    f.truncate()  # Обрезаем файл до новой длины
            else:
                # Если файла нет, создаем его с начальными значениями
                settings = {
                    "activity": 5,
                    "voice": "ru",
                    "restart_count": 0,
                    "language": new_language,  # Установим язык
                    "auto_translate": False  # Авто-перевод выключен по умолчанию
                }
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=4)

            bot.send_message(chat_id, f"Язык установлен на '{new_language}'.")
        except IndexError:
            bot.send_message(chat_id, "Пожалуйста, укажите язык. Например: /lang en.")
    else:
        bot.send_message(chat_id, "Извините, но вы не имеете прав админа для этой команды.")

# Команда для перевода текста
@bot.message_handler(commands=['tl'])
def translate_text(message):
    chat_id = message.chat.id
    text_to_translate = message.text[len('/tl '):].strip()

    # Загружаем настройки из settings.json
    settings_path = os.path.join(DATA_DIR, str(chat_id), 'settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            target_language = settings.get('language', 'en')  # По умолчанию на английский
    else:
        target_language = 'en'  # По умолчанию на английский

    # Определяем язык текста
    detected_language = translator.detect(text_to_translate)
    detected_language_lang = detected_language.lang  # Получаем язык

    # Если текст на установленном языке, переводим на английский
    if detected_language_lang == target_language:
        target_language = 'en' if target_language != 'en' else 'ru'

    translated_text = translator.translate(text_to_translate, dest=target_language).text  # Переводим текст
    bot.send_message(chat_id, translated_text)  # Отправляем переведенный текст

# Команда для включения/выключения авто-перевода
@bot.message_handler(commands=['autotl'])
def toggle_auto_translate(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    admins = bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]

    if user_id in admin_ids:
        command = message.text.split()[1].lower()
        settings_path = os.path.join(DATA_DIR, str(chat_id), 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r+') as f:
                settings = json.load(f)
                settings['auto_translate'] = (command in ['on', '1'])
                f.seek(0)
                json.dump(settings, f, ensure_ascii=False, indent=4)
                f.truncate()  # Обрезаем файл до новой длины
        else:
            settings = {'auto_translate': (command in ['on', '1'])}
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)

        if command in ['on', '1']:
            bot.send_message(chat_id, "Авто-перевод включен.")
        elif command in ['off', '0']:
            bot.send_message(chat_id, "Авто-перевод выключен.")
        else:
            bot.send_message(chat_id, "Пожалуйста, используйте 'on' или 'off'.")
    else:
        bot.send_message(chat_id, "Извините, но вы не имеете прав админа для этой команды.")

# Команда для включения/выключения естественного языка
@bot.message_handler(commands=['natural'])
def set_natural_language(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    admins = bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]

    if user_id in admin_ids:
        try:
            command = message.text.split()[1].lower()
            settings_path = os.path.join(DATA_DIR, str(chat_id), 'settings.json')

            if os.path.exists(settings_path):
                with open(settings_path, 'r+') as f:
                    settings = json.load(f)
                    settings['natural_language'] = (command in ['on', '1'])
                    f.seek(0)
                    json.dump(settings, f, ensure_ascii=False, indent=4)
                    f.truncate()  # Обрезаем файл до новой длины
            else:
                settings = {'natural_language': (command in ['on', '1'])}
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=4)

            if command in ['on', '1']:
                bot.send_message(chat_id, "Функция естественного языка включена.")
            elif command in ['off', '0']:
                bot.send_message(chat_id, "Функция естественного языка выключена.")
            else:
                bot.send_message(chat_id, "Пожалуйста, используйте 'on' или 'off'.")
        except IndexError:
            bot.send_message(chat_id, "Пожалуйста, укажите 'on' или 'off'.")
    else:
        bot.send_message(chat_id, "Извините, но вы не имеете прав админа для этой команды.")

# Команда для очистки словаря чата
@bot.message_handler(commands=['cm'])
def clear_memory(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    admins = bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]

    if user_id in admin_ids:
        if len(message.text.split()) == 2 and message.text.split()[1].lower() == 'true':
            chat_dir = os.path.join(DATA_DIR, str(chat_id))
            data_file_path = os.path.join(chat_dir, 'data.json')

            if os.path.exists(data_file_path):
                # Очищаем содержимое файла
                with open(data_file_path, 'w', encoding='utf-8') as f:
                    json.dump({'messages': [], 'last_active': time.time(), 'active_count': 0, 'last_message_sent': 0}, f, ensure_ascii=False, indent=4)

                # Увеличиваем счетчик перезапусков
                settings_path = os.path.join(chat_dir, 'settings.json')
                if os.path.exists(settings_path):
                    with open(settings_path, 'r+') as f:
                        settings = json.load(f)
                        settings['restart_count'] = settings.get('restart_count', 0) + 1
                        f.seek(0)
                        json.dump(settings, f, ensure_ascii=False, indent=4)
                        f.truncate()

                bot.send_message(chat_id, "Память бота успешно очищена.")
            else:
                bot.send_message(chat_id, "Ошибка: файл данных не найден.")
        else:
            bot.send_message(chat_id, "Используйте команду в формате: /cm true")
    else:
        bot.send_message(chat_id, "Извините, но вы не имеете прав админа для этой команды.")

# Команда для получения топ-листа 10 групп по сообщениям
@bot.message_handler(commands=['top'])
def top_groups(message):
    chat_id = message.chat.id
    groups_data = {}

    # Проходим по всем директориям в DATA_DIR
    for chat_folder in os.listdir(DATA_DIR):
        chat_path = os.path.join(DATA_DIR, chat_folder, 'data.json')
        if os.path.exists(chat_path):
            try:
                with open(chat_path, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    group_name = chat_data.get('title', f"ID{chat_folder}")  # Используем title или ID как имя группы
                    message_count = len(chat_data.get('messages', []))  # Получаем количество сообщений
                    groups_data[group_name] = message_count  # Сохраняем в словаре
            except (json.JSONDecodeError, UnicodeDecodeError):
                log(f"Ошибка при чтении файла {chat_path}. Пропускаем.")
                continue  # Пропускаем, если файл поврежден

    # Сортируем группы по количеству сообщений
    sorted_groups = sorted(groups_data.items(), key=lambda x: x[1], reverse=True)

    # Формируем сообщение для отправки
    if not sorted_groups:
        bot.send_message(chat_id, "Нет данных о группах.")
        return

    top_list = "Топ 10 групп по количеству сообщений:\n"
    for index, (group, count) in enumerate(sorted_groups[:10], start=1):
        if index == 1:
            top_list += f"🥇 {group}: {count} сообщений\n"
        elif index == 2:
            top_list += f"🥈 {group}: {count} сообщений\n"
        elif index == 3:
            top_list += f"🥉 {group}: {count} сообщений\n"
        else:
            top_list += f"🏅 {group}: {count} сообщений\n"

    bot.send_message(chat_id, top_list)

# Обработка случайного сообщения
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    chat_data = load_chat_data(chat_id)

    # Игнорируем сообщения, отправленные ботом
    if message.from_user.id == bot.get_me().id:
        return

    # Игнорируем команды
    if message.text.startswith('/'):
        return

    # Загружаем настройки из settings.json
    settings_path = os.path.join(DATA_DIR, str(chat_id), 'settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            target_language = settings.get('language', 'ru')  # По умолчанию на английский
            auto_translate = settings.get('auto_translate', False)  # Проверяем авто-перевод
            natural_language = settings.get('natural_language', False)  # Проверяем естественный язык
            activity_level = settings.get('activity', 5)  # Получаем уровень активности (по умолчанию 5)
    else:
        target_language = 'ru'
        auto_translate = False
        natural_language = False
        activity_level = 5  # Если файла нет, используем значения по умолчанию

    # Проверяем активность
    if activity_level == 0:
        return

    # Добавляем новое сообщение в словарь
    chat_data['messages'].append(message.text)
    chat_data['last_active'] = time.time()
    chat_data['last_message_sent'] = time.time()  # Обновляем время последнего сообщения

    #  Увеличиваем счетчик активности
    if time.time() - chat_data['last_message_sent'] > 120:
        chat_data['active_count'] += 1

    save_chat_data(chat_id, chat_data)

    # Если авто-перевод включен
    if auto_translate:
        detected_language = translator.detect(message.text).lang
        if detected_language != target_language:
            translated_text = translator.translate(message.text, dest=target_language).text
            user_name = message.from_user.first_name or "Пользователь"
            bot.send_message(chat_id, f"{user_name}: {translated_text}")

    # Генерация ответа
    response = None
    send_probability = activity_level / 100 # Вероятность от 0 до 1

    # Проверяем, достаточно ли активных сообщений для генерации ответа
    if chat_data['active_count'] >= 25 and random.random() < send_probability:
        response = generate_response(chat_data)

        # 10% шанс на отправку голосового сообщения вместо текстового
        if random.random() < 0.10:
            voice_file = generate_voice_message(response, chat_id)
            if voice_file is not None:  # Проверяем, что файл был успешно создан
                with open(voice_file, 'rb') as f:
                    bot.send_voice(chat_id, f)
            return  # Выходим, чтобы не отправлять текстовое сообщение

        # Эффект "печатает"
        bot.send_chat_action(chat_id, 'typing')
        time.sleep(2)  # Задержка для эффекта печати
        bot.send_message(chat_id, response)
        chat_data['last_message_sent'] = time.time()  # Обновляем время последнего сообщения

    # Логика для генерации медиа-сообщений
    if random.random() < send_probability:  # Используем вероятность отправки медиа-сообщений
        media_files = os.listdir(os.path.join(DATA_DIR, str(chat_id), 'media'))
        if media_files:
            random_media_file = random.choice(media_files)
            media_path = os.path.join(DATA_DIR, str(chat_id), 'media', random_media_file)

            # Определяем тип медиафайла для отправки
            caption = generate_response(chat_data)
            if random_media_file.endswith(('.jpg', '.png')):
                with open(media_path, 'rb') as f:
                    bot.send_photo(chat_id, f, caption=caption)
            elif random_media_file.endswith(('.mp4', '.avi')):
                with open(media_path, 'rb') as f:
                    bot.send_video(chat_id, f, caption=caption)
            elif random_media_file.endswith(('.ogg', '.mp3')):
                with open(media_path, 'rb') as f:
                    bot.send_audio(chat_id, f, caption=caption)
            else:
                with open(media_path, 'rb') as f:
                    bot.send_document(chat_id, f, caption=caption)

    # Логика для установки реакции на случайное сообщение
    if random.random() < send_probability:  # Используем вероятность для установки реакции
        reactions_file = os.path.join(DATA_DIR, str(chat_id), 'reactions.json')
        if os.path.exists(reactions_file):
            with open(reactions_file, 'r', encoding='utf-8') as f:
                reactions = json.load(f)
            if reactions:  # Проверяем, есть ли реакции
                reaction = random.choice(reactions)
                # Ставим реакцию на случайное сообщение
                bot.send_chat_action(chat_id, 'typing')
                time.sleep(2)  # Эффект "выбирает реакцию"
                bot.send_message(chat_id, reaction)

# Функция для периодической очистки медиафайлов
def periodic_cleanup(chat_id):
    clean_media_files(chat_id)
    Timer(21600, periodic_cleanup, args=[chat_id]).start()  # Запланировать следующий запуск через 6 часов

# Запуск периодической очистки для каждого чата
def start_periodic_cleanups():
    for chat_id in os.listdir(DATA_DIR):
        try:
            periodic_cleanup(int(chat_id))  # Запускаем для каждого чата
        except ValueError:
            continue  # Игнорируем, если не удалось преобразовать в i



# Запуск бота
if __name__ == "__main__":
    log("Бот запущен...")
    start_periodic_cleanups()  # Запускаем периодическую очистку
    bot.infinity_polling(none_stop=True)
