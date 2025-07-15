import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import db
from scraper import scraper
from config import STANDARD_CHECK_INTERVAL, PREMIUM_CHECK_INTERVAL
from aiogram import Bot

async def check_prices_and_notify(bot: Bot, premium_only: bool = False):
    products = db.get_all_tracked_products()
    for product in products:
        user_id = product['telegram_id']
        url = product['url']
        old_price = product['current_price']
        target_price = product['target_price']
        premium = product['premium_features']
        site_name = product['site_name']
        # Only process users in the correct group
        if premium_only and not premium:
            continue
        if not premium_only and premium:
            continue
        try:
            info = scraper.extract_product_info(url)
            new_price = info['price']
            currency = info['currency']
            title = info['title']
            affiliate_url = db.add_affiliate_tag(url, site_name)
            # If price dropped
            if new_price < old_price:
                text = (
                    f"🔥 <b>Price Drop Alert!</b>\n"
                    f"<b>{title}</b> is now <b>{currency}{new_price:,.2f}</b> (was {currency}{old_price:,.2f})\n"
                    f"<a href='{affiliate_url}'>View Product</a>"
                )
                await bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=False)
            # If target price is set and reached
            if target_price and new_price <= target_price:
                text = (
                    f"🎯 <b>Target Price Reached!</b>\n"
                    f"<b>{title}</b> is now <b>{currency}{new_price:,.2f}</b> (target: {currency}{target_price:,.2f})\n"
                    f"<a href='{affiliate_url}'>View Product</a>"
                )
                await bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=False)
            # Update price in DB
            db.update_product_price(product['id'], new_price, currency)
        except Exception as e:
            # Optionally log or notify admin
            continue

def start_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    # Standard users: every STANDARD_CHECK_INTERVAL hours
    scheduler.add_job(
        check_prices_and_notify,
        'interval',
        hours=STANDARD_CHECK_INTERVAL,
        args=[bot, False],
        id='price_check_standard',
        replace_existing=True
    )
    # Premium users: every PREMIUM_CHECK_INTERVAL hours
    scheduler.add_job(
        check_prices_and_notify,
        'interval',
        hours=PREMIUM_CHECK_INTERVAL,
        args=[bot, True],
        id='price_check_premium',
        replace_existing=True
    )
    scheduler.start() 
    