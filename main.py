import speech_recognition
import soundfile
import telebot
import time
import datetime
import os
import os.path
import threading
import random
import shutil
from moviepy.editor import VideoFileClip


DEBUG = False
API_TOKEN = '...'
reply_text = \
"""Привет, я \- [remaudio_bot](https://t.me/...)\!
Я предназначен для перевода речи из голосовых сообщений и видеосообщений в текст\. Чтобы перевести сообщение в текст, отправь мне его \(или перешли из другого чата\)\.

Автор\: [Leonid Briskindov](https://t.me/LeonBrisk)
Вдохновители\: [SebastienDubal](https://t.me/SebastienDubal) и [SkyLand](https://t.me/Turboskyland)"""




bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['help', 'start'])
def commands_handler(message):
    global reply_text
    bot.reply_to(message, reply_text, parse_mode='MarkdownV2')

@bot.message_handler(content_types=['text'])
def text_handler(message):
    global reply_text
    bot.reply_to(message, reply_text, parse_mode='MarkdownV2')

@bot.message_handler(content_types=['voice'])
def voice_handler(message):
    handle(message, "voice")

@bot.message_handler(content_types=["video_note"])
def video_handler(message):
    handle(message, 'video_note')

def handle(message, mtype):
    global DEBUG
    dir_ = ""
    while os.path.exists(f"temp\\{dir_}") or dir_ == "":
        dir_ = str(random.randint(0, 1000))

    os.mkdir(f"temp\\{dir_}")

    if mtype == "voice":
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(f'temp\\{dir_}\\audio.ogg', 'wb') as new_file:
            new_file.write(downloaded_file)

    elif mtype == "video_note":
        file_info = bot.get_file(message.video_note.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(f'temp\\{dir_}\\video.mp4', 'wb') as new_file:
            new_file.write(downloaded_file)
        clip = VideoFileClip(f'temp\\{dir_}\\video.mp4')
        clip.audio.write_audiofile(f"temp\\{dir_}\\audio.ogg", logger = None)
        time.sleep(0.5)
        clip.close()


    audio_handler = speech_recognition.Recognizer()

    data, samplerate = soundfile.read(f'temp\\{dir_}\\audio.ogg')
    soundfile.write(f'temp\\{dir_}\\audio.wav', data, samplerate)

    audio_file = speech_recognition.AudioFile(f'temp\\{dir_}\\audio.wav')
    with audio_file as source:
        audio = audio_handler.record(source)
    try:
        if (message.forward_from_chat != None) or (message.from_user != None and message.forward_from != None):
            if message.forward_from_chat != None:
                bot.reply_to(message,
                             f"""Канал <a href="https://t.me/{message.forward_from_chat.username}">{message.forward_from_chat.title}</a> ({datetime.datetime.utcfromtimestamp(int(message.forward_date) + 3 * 60 * 60).strftime('%H:%M / %d.%m.%Y / UTC+3')}):\n\n{audio_handler.recognize_google(audio, language="ru-RU")}""", parse_mode='HTML')

            elif message.from_user.username != message.forward_from.username:
                bot.reply_to(message,
                             f"""Пользователь "{message.forward_from.username}" ({datetime.datetime.utcfromtimestamp(int(message.forward_date) + 3*60*60).strftime('%H:%M / %d.%m.%Y / UTC+3')}):\n\n{audio_handler.recognize_google(audio, language="ru-RU")}""")
            else:
                raise Exception(f"message.from_user.username == message.forward_from.username and message.forward_from_chat == None ({message.from_user.username} == {message.forward_from.username})")
        else:
            raise Exception(f"(message.forward_from_chat != None) or (message.from_user != None and message.forward_from != None)")
    except Exception as warn:
        if DEBUG:
            print(warn)
        try:
            bot.reply_to(message,
                         f"""{audio_handler.recognize_google(audio, language="ru-RU")}""")
        except Exception as error:
            if DEBUG:
                print(f"ERROR: {error}")
                bot.reply_to(message, f"Непредвиденная ошибка: {error}")
            else:
                bot.reply_to(message, f"Непредвиденная ошибка!")
    clip = None
    new_file = None
    downloaded_file = None
    clear_thread = threading.Thread(target=clear_temp, args=(dir_, ))
    clear_thread.start()

def clear_temp(dir_):
    time.sleep(0.5)
    shutil.rmtree(f'temp\\{dir_}')


bot.infinity_polling()
