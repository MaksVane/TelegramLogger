# Telegram Message Logger

A powerful Python-based Telegram message logger that monitors specific chats or contacts and creates organized logs of all messages, with special tracking for phone numbers and other numeric identifiers.

## Features

- **Chat Monitoring**: Monitor specific Telegram chats by username, phone number, or chat ID
- **Organized Logging**: Automatically saves messages in chat-specific directories
- **Number Extraction**: Detects phone numbers and other numeric sequences in messages
- **Separate Number Logs**: Creates separate log files for each detected number
- **Message Tracking**: Records original message content, edits, and deletions
- **Comprehensive Metadata**: Logs timestamps, sender names, and message content
- **Modern Async Design**: Uses the latest Telethon 1.40.0 with modern async patterns

## Requirements

- Python 3.7+
- Telethon 1.40.0+
- A Telegram API ID and Hash (from [my.telegram.org](https://my.telegram.org/))

### Optional Dependencies
- `cryptg`: For speed improvements in downloading media
- `pillow`: For handling images

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/telegram_logger.git
cd telegram-logger
```

2. Create a `requirements.txt` file with the following content:
```
telethon==1.40.0
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your Telegram API credentials:
   - Get your API ID and Hash from [my.telegram.org](https://my.telegram.org/)
   - Update the `API_ID` and `API_HASH` variables in `telegram_logger.py`

## Usage

1. Set the target chat in `telegram_logger.py`:
```python
TARGET_CHAT = '+1234567890'  # Your target's phone number, username, or chat ID
```

2. Run the script:
```bash
python telegram_logger.py
```

3. On first run, you'll need to log in to your Telegram account. The script will:
   - List all your dialogs (chats) to help you identify the correct chat ID
   - Start monitoring the specified chat
   - Create a directory structure in `chat_logs/` for organizing messages

## Log File Structure

The logger creates an organized directory structure:
```
chat_logs/
├── 123456789/             # Chat ID folder
│   ├── log.txt            # Main log with all messages
│   ├── 7777777.txt        # Separate log for messages containing this number
│   └── 9999999.txt        # Separate log for messages containing this number
└── another_chat_id/
    └── ...
```

## Log Format

Messages are logged with timestamps and sender information:
```
[2023-05-20 14:32:45] John: Hello, please call me at 7777777
[2023-05-20 14:33:12] Me: I'll call you later
[2023-05-20 14:35:27] John EDITED: Hello, please call me at 7777777 → [Hello, please call me at 7777777 tonight] {EDITED} at 2023-05-20 14:32:45
[2023-05-20 14:36:01] Me: Thanks! {DELETED} at 2023-05-20 14:33:12
```

Each log entry contains:
- **Left timestamp** `[2023-05-20 14:35:27]`: When the action (sending/editing/deletion) was detected
- **Sender**: Who performed the action
- **Message content**: Original and new content for edits
- **Right timestamp** `at 2023-05-20 14:32:45`: For edited/deleted messages, when the original message was sent

This dual-timestamp system provides a complete history of message lifecycle, showing both when messages were originally sent and when they were modified.

## Advanced Features

### Modern Async Implementation
The logger uses Python's modern async syntax with Telethon 1.40.0:
- Context manager (`async with`) for proper client lifecycle management
- Named event handlers for better code organization
- Proper asyncio.run() implementation for clean runtime

### Message Tracking
The logger keeps track of messages to properly log edits and deletions:
- Edited messages show both the original and new content, along with the original message timestamp
- Deleted messages are marked with {DELETED} and include both the original content and the original message timestamp

### Number Detection
Numbers are automatically detected in messages using a regular expression pattern. By default, it extracts sequences of 7 or more digits, which typically captures phone numbers and other significant numeric identifiers.

## Security & Privacy

- This tool is for personal use only
- Never share your `telegram_session` file or API credentials
- Be aware of privacy implications when logging communications
- Use responsibly and ethically, and in compliance with local laws

## Customization

You can customize the logger behavior by modifying these variables:
- `DEBUG`: Set to `True` or `False` to control verbose output
- `logging.basicConfig`: Configure the logging level for more or less detailed output
- Change the regex pattern in `extract_numbers()` to alter number detection

## License

This project is released under the MIT License. See the LICENSE file for details.

## Contributions

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is provided for educational and personal use only. The developers are not responsible for any misuse or for any damages resulting from its use. Always respect privacy and adhere to the Telegram Terms of Service.
