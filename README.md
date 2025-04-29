# bazi-AI
# Bazi AI - README

Bazi AI is a Telegram bot designed to provide a variety of AI-powered functionalities within group chats.  This project is currently under development, and features will continue to be added and improved.

Functionality:

This bot offers a range of commands, including text and voice generation, image creation, polls, timers, and chat management tools.  Some features are still under development.

Commands:

* /start: Starts the bot and registers the chat in the database.  This is required for the bot to function correctly in a group.
* /gent: Generates a text message.
* /genv: Generates a voice message (TTS).
* /genm: Generates images.
* /gent2: Improved version of /gent (Under Development).
* /gent2t:  /gent2 using a template (Under Development).
* Memes: Meme generation (Under Development).
* /top: Shows the top chats based on message count.
* Baziki (Базики): In-bot currency (Under Development).
* /cm true: Clears the chat (Admin only).
* /info: Displays information about the bot.
* /poll: Generates a poll or quiz.
* /activity {number}: Changes the bot's activity level (1-10) (Admin only).  Higher numbers mean more frequent responses.
* /voice {voice_name}: Changes the voice used for TTS (Admin only).  Specific voice names will be documented separately.
* /timer {time}\n{command}: Sets a timer to execute a command after a specified time.  Example: /timer 1h\n/gent Hello! (will execute /gent Hello! after 1 hour).
* /timers: Lists active timers.
* /stoptimer: Stops a timer (Admin only).
* /natural {on/off or 1/0}: Enables/disables natural language processing (Admin only).
* /lang {language_code}: Sets the bot's language (Admin only).  Supported language codes will be documented separately.
* /tl: Translates a message.
* /autotl {on/off or 1/0}: Enables/disables automatic translation (Admin only).


Admin-Only Commands:

The following commands are restricted to administrators of the chat:

* /cm true
* /activity
* /voice
* /stoptimer
* /natural
* /lang
* /autotl


Technical Details:

* Programming Language:  [Specify programming language, e.g., Python]
* Libraries: [List libraries used, e.g., telebot, transformers]
* Database: [Specify database used, e.g., PostgreSQL, MongoDB]

Contribution:

Contributions are welcome! Please see the contributing guidelines [link to contributing guidelines if available].

License:

[Specify license, e.g., MIT License]


Contact:

[Contact information]


This README will be updated as the project progresses.
