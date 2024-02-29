from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
import httpx
from bs4 import BeautifulSoup
import os

bot_token = '6595127975:AAEGxHMDOe4uYxwHkYhrgDFHDcm-24MA_sY'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    with open('subscribers.txt', 'a+') as file:
        if str(chat_id) + '\n' not in file.readlines():
            file.write(str(chat_id) + '\n')
            await context.bot.send_message(chat_id=chat_id, text="You've been subscribed to updates.")
        else:
            await context.bot.send_message(chat_id=chat_id, text="You're already subscribed.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def fetch_latest_news_id(url, selector):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    latest_news = soup.select_one(selector)
    return latest_news['href'] if latest_news else None

async def check_for_changes(bot: Bot, url, selector, interval, message):
    print(f"Starting check for changes on {url}")
    last_state = None
    while True:
        try:
            latest_news_id = await fetch_latest_news_id(url, selector)
            print(f"Latest news ID for {url}: {latest_news_id}")
            
            if latest_news_id != last_state:
                if last_state is not None:
                    if os.path.exists('subscribers.txt'):
                        with open('subscribers.txt', 'r') as subs:
                            subscribers = [line.strip() for line in subs if line.strip()]
                            for chat_id in subscribers:
                                await bot.send_message(chat_id=chat_id, text=message)
                            print(f"Notified {len(subscribers)} subscribers for {url}.")
                last_state = latest_news_id
                with open(f'last_state_{url.replace("https://", "").replace("/", "_")}.txt', 'w') as file:
                    file.write(latest_news_id)
            else:
                print(f"No changes detected for {url}.")
        except Exception as e:
            print(f"Error checking for changes on {url}: {e}")
        await asyncio.sleep(interval)

def setup():
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler('start', start))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    bot = Bot(token=bot_token)
    
    asyncio.create_task(check_for_changes(bot, 'https://report.az/son-xeberler/', '.news-item.flex.infinity-item', 3600, "Test: Change Detected"))

    selector = '.news__item a'
    asyncio.create_task(check_for_changes(bot, 'https://jlc.gov.az/az/media/xeberler?page=1', selector, 60, "Changes detected on JLC"))

    application.run_polling()

if __name__ == '__main__':
    asyncio.run(setup())
