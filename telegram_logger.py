from telethon import TelegramClient, events, sync
import asyncio
import os
import traceback
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re
import logging

# API from https://my.telegram.org/
API_ID = 12345678  # Replace with your own
API_HASH = 'abcdef1234567890abcdef1234567890'  # Replace with your own

# Target chat identifier (username, phone, or chat ID)
TARGET_CHAT = '+1234567890'  
TARGET_CHAT_ID = None  # Will be filled during runtime

# Logging setup
current_dir = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(current_dir, 'chat_logs')
os.makedirs(LOGS_DIR, exist_ok=True)
print(f"Logs will be saved in: {LOGS_DIR}")

# Debug mode and logging configuration
DEBUG = True  # Set to False to disable verbose output
logging.basicConfig(level=logging.INFO if DEBUG else logging.ERROR)

# Message tracking for edits and deletions
message_tracker = {}  # Format: {msg_id: {'chat_id': chat_id, 'text': text, 'sender': sender_name}}

def get_log_file_path(chat_id):
    """Generate log file path for a specific chat"""
    chat_id_str = str(chat_id).replace('/', '_').replace('\\', '_')
    chat_dir = os.path.join(LOGS_DIR, chat_id_str)
    os.makedirs(chat_dir, exist_ok=True)
    return os.path.join(chat_dir, 'log.txt')

def write_to_log(chat_id, content):
    """Write content to the main log file for a chat"""
    try:
        log_file = get_log_file_path(chat_id)
        with open(log_file, 'a', encoding='utf-8', buffering=1) as f:
            f.write(content)
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Force OS to flush file buffers
        
        if DEBUG:
            print(f"Successfully wrote {len(content)} bytes to log file for chat {chat_id}")
        return True
    except Exception as e:
        print(f"Error writing to log file for chat {chat_id}: {e}")
        traceback.print_exc()
        return False

def write_to_numbered_log(chat_id, number, content):
    """Write content to number-specific log file"""
    try:
        chat_id_str = str(chat_id).replace('/', '_').replace('\\', '_')
        chat_dir = os.path.join(LOGS_DIR, chat_id_str)
        os.makedirs(chat_dir, exist_ok=True)
        
        number_file = os.path.join(chat_dir, f"{number}.txt")
        with open(number_file, 'a', encoding='utf-8', buffering=1) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        
        if DEBUG:
            print(f"Successfully wrote to number file {number} for chat {chat_id}")
        return True
    except Exception as e:
        print(f"Error writing to number file {number} for chat {chat_id}: {e}")
        traceback.print_exc()
        return False

def extract_numbers(text):
    """Extract sequences of 7+ digits (typically phone numbers)"""
    return re.findall(r'\b\d{7,}\b', text)

async def list_all_dialogs(client):
    """List all chats and their IDs to help identify the correct chat"""
    print("\n=== LISTING ALL DIALOGS ===")
    print("Use this to find the chat you want to monitor")
    print("=" * 50)
    
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        entity_type = type(entity).__name__
        
        username = f"@{entity.username}" if hasattr(entity, 'username') and entity.username else "No username"
        phone = entity.phone if hasattr(entity, 'phone') and entity.phone else "No phone"
        
        print(f"ID: {dialog.id} | Type: {entity_type} | Name: {dialog.name} | Username: {username} | Phone: {phone}")
    
    print("=" * 50)
    print("To use a specific chat ID, update TARGET_CHAT in the script")

async def find_target_chat(client):
    """Find the target chat ID based on the TARGET_CHAT identifier"""
    global TARGET_CHAT_ID
    
    print(f"\nSearching for target chat: {TARGET_CHAT}")
    
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        matches = False
        
        # Check for matches in ID, username, phone, or name
        if str(dialog.id) == TARGET_CHAT:
            matches = True
        elif hasattr(entity, 'username') and entity.username and TARGET_CHAT in entity.username:
            matches = True
        elif hasattr(entity, 'phone') and entity.phone and TARGET_CHAT in entity.phone:
            matches = True
        elif dialog.name and TARGET_CHAT in dialog.name:
            matches = True
        
        if matches:
            TARGET_CHAT_ID = dialog.id
            print(f"Found target chat! ID: {TARGET_CHAT_ID} | Name: {dialog.name}")
            return True
    
    print(f"Warning: Could not find target chat with identifier {TARGET_CHAT}")
    return False

async def main():
    global TARGET_CHAT_ID
    
    print("Starting Telegram Logger using Telethon 1.40.0...")
    
    # Create client using the context manager pattern
    async with TelegramClient('telegram_session', API_ID, API_HASH) as client:
        # List all available dialogs
        await list_all_dialogs(client)
        
        # Resolve target chat ID
        try:
            if str(TARGET_CHAT).lstrip('-').isdigit():
                TARGET_CHAT_ID = int(TARGET_CHAT)
                entity = await client.get_entity(TARGET_CHAT_ID)
                print(f"Using chat ID: {TARGET_CHAT_ID}")
                print(f"Found chat: {getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))}")
            else:
                entity = await client.get_entity(TARGET_CHAT)
                TARGET_CHAT_ID = entity.id
                print(f"Found chat: {getattr(entity, 'first_name', getattr(entity, 'title', 'Unknown'))}")
                print(f"Chat ID: {TARGET_CHAT_ID}")
        except Exception as e:
            print(f"Warning: Could not find target chat entity: {e}")
            print("Will log messages based on matching criteria")
        
        print(f"Starting to monitor messages in {LOGS_DIR}... (Press Ctrl+C to stop)")
        
        # Test log file access
        if TARGET_CHAT_ID:
            start_message = f"[INFO] Monitoring started at {asyncio.get_event_loop().time()}\n"
            if not write_to_log(TARGET_CHAT_ID, start_message):
                print("CRITICAL: Could not write to log file! Check permissions.")
                return

        # Handle new messages
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                chat = await event.get_chat()
                sender = await event.get_sender()
                chat_id = getattr(chat, 'id', None)
                
                if DEBUG:
                    print(f"New message: {event.message.id} | Chat: {chat_id} | Private: {event.is_private}")
                
                # Determine if we should log this message
                should_log = False
                if TARGET_CHAT_ID is not None and chat_id == TARGET_CHAT_ID:
                    should_log = True
                elif event.is_private:
                    if (hasattr(sender, 'phone') and sender.phone and TARGET_CHAT in sender.phone or
                        hasattr(chat, 'phone') and chat.phone and TARGET_CHAT in chat.phone or
                        event.out and str(chat_id) == TARGET_CHAT):
                        should_log = True
                
                if should_log:
                    # Prepare log data
                    sender_name = "Me" if event.out else getattr(sender, 'first_name', 'Unknown')
                    message_text = event.message.text or "[NON-TEXT CONTENT]"
                    timestamp = event.date.strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"[{timestamp}] {sender_name}: {message_text}\n"
                    
                    # Store message for tracking edits/deletions
                    message_tracker[event.message.id] = {
                        'chat_id': chat_id,
                        'text': message_text,
                        'sender': sender_name,
                        'timestamp': timestamp  # Store the original timestamp
                    }
                    
                    # Log to main file
                    if write_to_log(chat_id, log_entry):
                        print(f"Logged: {log_entry.strip()}")
                    
                    # Check for numbers and log to number-specific files
                    for number in extract_numbers(message_text):
                        write_to_numbered_log(chat_id, number, log_entry)
                
            except Exception as e:
                print(f"Error in message handler: {e}")
                if DEBUG:
                    traceback.print_exc()
        
        # Handle edited messages
        @client.on(events.MessageEdited)
        async def handle_edited_message(event):
            try:
                chat = await event.get_chat()
                sender = await event.get_sender()
                chat_id = getattr(chat, 'id', None)
                
                # Use same criteria as for new messages
                should_log = False
                if TARGET_CHAT_ID is not None and chat_id == TARGET_CHAT_ID:
                    should_log = True
                elif event.is_private:
                    if (hasattr(sender, 'phone') and sender.phone and TARGET_CHAT in sender.phone or
                        hasattr(chat, 'phone') and chat.phone and TARGET_CHAT in chat.phone or
                        event.out and str(chat_id) == TARGET_CHAT):
                        should_log = True
                
                if should_log:
                    sender_name = "Me" if event.out else getattr(sender, 'first_name', 'Unknown')
                    message_text = event.message.text or "[NON-TEXT CONTENT]"
                    event_timestamp = event.date.strftime("%Y-%m-%d %H:%M:%S")  # Original event timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")    # Current time when edit was detected
                    
                    # Get original text if available
                    original_text = "[Unknown original content]"
                    original_timestamp = event_timestamp  # Default to original event time
                    
                    if event.message.id in message_tracker:
                        original_text = message_tracker[event.message.id]['text']
                        if 'timestamp' in message_tracker[event.message.id]:
                            original_timestamp = message_tracker[event.message.id]['timestamp']
                        message_tracker[event.message.id]['text'] = message_text
                    
                    log_entry = f"[{timestamp}] {sender_name} EDITED: {original_text} → [{message_text}] {{EDITED}} at {original_timestamp}\n"
                    
                    # Log to main and number files
                    if write_to_log(chat_id, log_entry):
                        print(f"Logged edit: {log_entry.strip()}")
                    
                    for number in extract_numbers(message_text):
                        write_to_numbered_log(chat_id, number, log_entry)
                    
            except Exception as e:
                print(f"Error in edit handler: {e}")
                if DEBUG:
                    traceback.print_exc()
        
        # Handle deleted messages
        @client.on(events.MessageDeleted)
        async def handle_deleted_message(event):
            try:
                # Telegram doesn't always provide chat info for deletions
                chat_id = event.chat_id if hasattr(event, 'chat_id') else None
                
                for msg_id in event.deleted_ids:
                    message_info = message_tracker.get(msg_id)
                    
                    if message_info:
                        # We have this message in our tracker
                        msg_chat_id = message_info['chat_id']
                        original_text = message_info['text']
                        sender_name = message_info['sender']
                        
                        # Only log if from target chat
                        if TARGET_CHAT_ID is None or msg_chat_id == TARGET_CHAT_ID:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            original_timestamp = timestamp  # Use the current message time as fallback
                            
                            # If we have the original message in our tracker, use its timestamp if available
                            if 'timestamp' in message_info:
                                original_timestamp = message_info['timestamp']
                            
                            log_entry = f"[{timestamp}] {sender_name}: {original_text} {{DELETED}} at {original_timestamp}\n"
                            
                            if write_to_log(msg_chat_id, log_entry):
                                print(f"Logged deletion: {log_entry.strip()}")
                            
                            # Log to number files and remove from tracker
                            for number in extract_numbers(original_text):
                                write_to_numbered_log(msg_chat_id, number, log_entry)
                            
                            del message_tracker[msg_id]
                            
                    elif chat_id is not None and (TARGET_CHAT_ID is None or chat_id == TARGET_CHAT_ID):
                        # Unknown message but we know the chat_id
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_entry = f"[{timestamp}] MESSAGE DELETED: ID {msg_id} {{DELETED}} at {timestamp}\n"
                        write_to_log(chat_id, log_entry)
                
            except Exception as e:
                print(f"Error in deletion handler: {e}")
                if DEBUG:
                    traceback.print_exc()
        
        # Keep the script running until disconnected
        print("Monitoring messages... Press Ctrl+C to stop")
        await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting by user request")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc() 