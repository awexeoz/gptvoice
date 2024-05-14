from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import telegram
import openai
from gtts import gTTS
import os
from io import BytesIO
import PyPDF2
from docx import Document
from moviepy.editor import AudioFileClip
from telegram.ext import CommandHandler

openai.api_key = "your-api-key"
TELEGRAM_API_TOKEN = "token"

messages = [{"role": "system", "content": "You are SuperTelegramGPT, a helpful telegram bot who is always concise and polite in its answers."}]

def text_message(update, context):
    try:
        messages.append({"role": "user", "content": update.message.text})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=3000  # Устанавливаем максимальное количество символов
        )
        ChatGPT_reply = response["choices"][0]["message"]["content"]
        update.message.reply_text("Я получил текстовое сообщение! Пожалуйста, дайте мне секунду, чтобы ответить :)")
        update.message.reply_text(text=f"*[Bot]:* {ChatGPT_reply}", parse_mode=telegram.ParseMode.MARKDOWN)
        messages.append({"role": "assistant", "content": ChatGPT_reply})
    except openai.OpenAIException as e:
        update.message.reply_text("Извините, я не могу обработать ваш запрос из-за ограничений на количество символов. Попробуйте сократить текст.")
        # Дополнительная обработка исключения, если необходимо

def voice_message(update, context):
    update.message.reply_text("Я получил голосовое сообщение! Пожалуйста, дайте мне секунду, чтобы ответить :)")
    voice_file = context.bot.getFile(update.message.voice.file_id)
    voice_file.download("voice_message.ogg")
    audio_clip = AudioFileClip("voice_message.ogg")
    audio_clip.write_audiofile("voice_message.mp3")
    audio_file = open("voice_message.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file).text
    update.message.reply_text(text=f"*[You]:* _{transcript}_", parse_mode=telegram.ParseMode.MARKDOWN)
    messages.append({"role": "user", "content": transcript})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=3000  # Устанавливаем максимальное количество символов
        )
        ChatGPT_reply = response["choices"][0]["message"]["content"]
        
        # Преобразование текста ответа GPT в аудио
        tts = gTTS(text=ChatGPT_reply, lang='ru')
        tts.save("gpt_reply.ogg")

        # Отправка голосового сообщения пользователю
        context.bot.send_voice(chat_id=update.effective_chat.id, voice=open("gpt_reply.ogg", "rb"))
        
        messages.append({"role": "assistant", "content": ChatGPT_reply})
    except openai.OpenAIException as e:
        update.message.reply_text("Извините, я не могу обработать ваш запрос из-за ограничений на количество символов. Попробуйте сократить текст.")
        # Дополнительная обработка исключения, если необходимо

def start(update, context):
    # Приветственное голосовое сообщение
    welcome_message = "Добро пожаловать! Я ваш личный ассистент. Чем я могу помочь?"
    tts = gTTS(text=welcome_message, lang='ru')
    tts.save("welcome_message.ogg")
    context.bot.send_voice(chat_id=update.effective_chat.id, voice=open("welcome_message.ogg", "rb"))

def document_message(update, context):
    document = update.message.document
    file_id = document.file_id
    file = context.bot.get_file(file_id)
    file_extension = document.file_name.split(".")[-1].lower()
    
    # Скачивание документа
    if file_extension == "txt":
        file.download("document.txt")
        with open("document.txt", "r", encoding="utf-8") as f:
            document_text = f.read()
    elif file_extension == "pdf":
        file.download("document.pdf")
        with open("document.pdf", "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            document_text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                document_text += page.extract_text()
    elif file_extension == "docx":
        file.download("document.docx")
        doc = Document("document.docx")
        document_text = ""
        for paragraph in doc.paragraphs:
            document_text += paragraph.text + "\n"
    else:
        update.message.reply_text("Извините, я могу обрабатывать только файлы TXT, PDF и DOCX.")
        return
    
    try:
        # Добавление текста документа в сообщения
        messages.append({"role": "user", "content": document_text})
        update.message.reply_text("Я получил документ! Пожалуйста, дайте мне секунду, чтобы ответить :)")
        # Генерация ответа с использованием текста документа
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=3000  # Устанавливаем максимальное количество символов
        )
        ChatGPT_reply = response["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": ChatGPT_reply})
        
        # Преобразование текста ответа GPT в аудио
        tts = gTTS(text=ChatGPT_reply, lang='ru')
        tts.save("gpt_reply.ogg")
        
        # Отправка голосового сообщения пользователю
        context.bot.send_voice(chat_id=update.effective_chat.id, voice=open("gpt_reply.ogg", "rb"))
    except openai.OpenAIException as e:
        update.message.reply_text("Извините, я не могу обработать ваш запрос из-за ограничений на количество символов. Попробуйте сократить текст.")
        # Дополнительная обработка исключения, если необходимо

updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), text_message))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_message))
dispatcher.add_handler(MessageHandler(Filters.document, document_message))
dispatcher.add_handler(CommandHandler("start", start))
updater.start_polling()
updater.idle()
