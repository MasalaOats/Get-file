from pyrogram import Client, filters
from telethon import TelegramClient

# Telegram API credentials
api_id = 2954857  # Replace with your API ID
api_hash = "54e813f8239e419c323f99d44729b40e"  # Replace with your API Hash
bot_token = "7880185936:AAE1Lrr02aWw19XdiTVTchXXg6m9hdpSGr8"  # Replace with your Bot Token

# Owner ID
owner_id = 572308845  # Replace with your own Telegram user ID

# Channel Username instead of ID
logs_chat_username = "@logsofoatsarchive"  # Replace with your channel's username

# Initialize the Pyrogram Client
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Initialize the Telethon Client
telethon_client = TelegramClient('session_name', api_id, api_hash)

media_log = {}  # {file_id: {"name": ..., "batch_id": ...}}
file_counter = 1   # File counter for single file uploads
batch_counter = 1  # Batch counter for series or multiple file uploads

# Handle incoming media (documents, audio, video)
@app.on_message(filters.media)
async def handle_media(client, message):
    global file_counter, batch_counter
    media = message.video or message.document or message.audio  # Supports different media types
    file_name = media.file_name if media else "Unknown file"

    # Resolve logs_chat_id from username
    logs_chat = await client.get_chat(logs_chat_username)
    logs_chat_id = logs_chat.id

    # If part of a media group
    if message.media_group_id:
        if batch_counter not in media_log:
            media_log[batch_counter] = []
        media_log[batch_counter].append({"name": file_name})

        # Log this action
        log_text = f"Batch ID: {batch_counter}\nFile Name: {file_name}\n\n"
        await client.send_message(logs_chat_id, log_text)

        batch_counter += 1
    else:
        media_log[file_counter] = {"name": file_name}

        # Log this action
        log_text = f"File ID: {file_counter}\nFile Name: {file_name}\n\n"
        await client.send_message(logs_chat_id, log_text)

        file_counter += 1

# Command to show logged media IDs and file names
@app.on_message(filters.command("show_ids"))
async def show_ids(client, message):
    output = "List of logged files:\n\n"
    for key, value in media_log.items():
        if isinstance(value, list):  # It's a batch
            output += f"Batch ID: {key}\n"
            for file in value:
                output += f"{file['name']}\n\n"
        else:  # Single file
            output += f"File ID: {key}, Name: {value['name']}\n\n"
    await client.send_message(message.chat.id, output)

# Command to check the database using Telethon
@app.on_message(filters.command("check_database"))
async def check_database(client, message):
    if message.from_user.id != owner_id:
        await client.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    async with telethon_client:
        output = "Messages in Database:\n\n"
        async for msg in telethon_client.iter_messages(logs_chat_username):
            output += f"{msg.text}\n\n"  # Append message text to the output

        # Send the collected messages back to the chat
        if output.strip():  # Check if output is not empty
            await client.send_message(message.chat.id, output)
        else:
            await client.send_message(message.chat.id, "No messages found in the database.")

# Command to delete duplicate entries in the media log
@app.on_message(filters.command("delete_duplicates"))
async def delete_duplicates(client, message):
    if message.from_user.id != owner_id:
        await client.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    unique_files = {}
    duplicates = []

    for key, value in media_log.items():
        if isinstance(value, list):  # Batch
            for file in value:
                if file['name'] in unique_files:
                    duplicates.append(file['name'])
                else:
                    unique_files[file['name']] = key
        else:  # Single file
            if value['name'] in unique_files:
                duplicates.append(value['name'])
            else:
                unique_files[value['name']] = key

    for duplicate in duplicates:
        del unique_files[duplicate]  # Remove duplicates

    # Rebuild media_log without duplicates
    media_log.clear()
    for name, id in unique_files.items():
        media_log[id] = {"name": name}

    await client.send_message(message.chat.id, "Duplicate files deleted.")

# Command to start the bot
@app.on_message(filters.command("start"))
async def start(client, message):
    await client.send_message(message.chat.id, "Bot started! Use /show_ids to view logged files, /check_database to check the media database, and /delete_duplicates to remove duplicate files.")

# Run the bot
app.run()
