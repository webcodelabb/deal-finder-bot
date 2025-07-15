import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE
from db import db
from scraper import scraper
from scheduler import start_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required. Please set it in Railway variables.")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM States
class ProductStates(StatesGroup):
    waiting_for_target_price = State()

# Inline keyboard helpers
def get_product_keyboard(product_id: int, affiliate_url: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for product actions"""
    keyboard = [
        [
            InlineKeyboardButton(text="🔍 View Product", url=affiliate_url),
            InlineKeyboardButton(text="🗑 Stop Tracking", callback_data=f"remove_{product_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_remove_keyboard(products: list) -> InlineKeyboardMarkup:
    """Create inline keyboard for removing products"""
    keyboard = []
    for product in products:
        # Truncate title if too long
        title = product['title'][:30] + "..." if len(product['title']) > 30 else product['title']
        keyboard.append([
            InlineKeyboardButton(
                text=f"🗑 {title}",
                callback_data=f"remove_{product['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_remove")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Command handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Check if user was referred
    referred_by = None
    if message.text.startswith('/start '):
        referral_code = message.text.split()[1]
        referrer = db.get_user_by_referral_code(referral_code)
        if referrer and referrer['telegram_id'] != user_id:
            referred_by = referrer['telegram_id']
    
    # Create or get user
    # Only pass referred_by if not None
    if referred_by is not None:
        referral_code = db.create_user(user_id, username, referred_by)
    else:
        referral_code = db.create_user(user_id, username)
    
    # Send welcome message
    await message.answer(WELCOME_MESSAGE)
    
    # If user was referred, send thank you message
    if referred_by:
        await message.answer(
            f"🎉 You were invited by a friend! You now have access to premium features.\n"
            f"Your referral code: `{referral_code}`\n"
            f"Share it with friends to unlock more product slots!",
            parse_mode="Markdown"
        )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    await message.answer(HELP_MESSAGE)

@dp.message(Command("myproducts"))
async def cmd_myproducts(message: types.Message):
    """Handle /myproducts command"""
    user_id = message.from_user.id
    products = db.get_user_products(user_id)
    
    if not products:
        await message.answer("📦 You're not tracking any products yet.\nSend me a product link to get started!")
        return
    
    user = db.get_user(user_id)
    if not user:
        await message.answer("❌ User not found. Please use /start first.")
        return
    await message.answer(
        f"📦 **Your Tracked Products** ({len(products)}/{user['max_products']})\n\n"
        f"🎁 Refer friends to unlock more slots!"
    )
    
    for product in products:
        price_text = f"{product['currency']}{product['current_price']:,.2f}"
        target_text = f"\n🎯 Target: {product['currency']}{product['target_price']:,.2f}" if product['target_price'] else ""
        
        text = (
            f"📦 **{product['title']}**\n"
            f"💰 Current Price: {price_text}{target_text}\n"
            f"🕒 Added: {product['created_at'][:10]}"
        )
        
        keyboard = get_product_keyboard(product['id'], product['affiliate_url'])
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("remove"))
async def cmd_remove(message: types.Message):
    """Handle /remove command"""
    user_id = message.from_user.id
    products = db.get_user_products(user_id)
    
    if not products:
        await message.answer("📦 You're not tracking any products to remove.")
        return
    
    keyboard = get_remove_keyboard(products)
    await message.answer(
        "🗑 **Select a product to remove:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(Command("referral"))
async def cmd_referral(message: types.Message):
    """Handle /referral command"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ User not found. Please use /start first.")
        return
    
    stats = db.get_referral_stats(user_id)
    if not stats:
        await message.answer("❌ Could not load referral stats.")
        return
    
    bot_username = (await bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    
    text = (
        f"🎁 **Your Referral Stats**\n\n"
        f"📊 Referrals: {stats['referral_count']}\n"
        f"📦 Product Slots: {stats['max_products']}\n"
        f"⭐ Premium Features: {'Yes' if stats['premium_features'] else 'No'}\n\n"
        f"🔗 **Your Referral Link:**\n"
        f"`{referral_link}`\n\n"
        f"💡 Share this link with friends to unlock more product slots!"
    )
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("limits"))
async def cmd_limits(message: types.Message):
    """Handle /limits command"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ User not found. Please use /start first.")
        return
    
    current_count = db.get_user_product_count(user_id)
    
    text = (
        f"📊 **Your Tracking Limits**\n\n"
        f"📦 Current Products: {current_count}\n"
        f"🔢 Maximum Products: {user['max_products']}\n"
        f"⭐ Premium Features: {'Yes' if user['premium_features'] else 'No'}\n\n"
        f"🎁 **How to unlock more:**\n"
        f"• Each referral = +1 product slot\n"
        f"• Premium users get faster price checks\n\n"
        f"Use /referral to get your referral link!"
    )
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    """Handle /history command"""
    user_id = message.from_user.id
    products = db.get_user_products(user_id)
    if not products:
        await message.answer("📦 You're not tracking any products yet.")
        return
    # Show product list as inline buttons
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=product['title'][:30] + ("..." if len(product['title']) > 30 else ""), callback_data=f"history_{product['id']}")]
            for product in products
        ]
    )
    await message.answer("📈 <b>Select a product to view its price history:</b>", reply_markup=keyboard, parse_mode="HTML")

# URL handling
@dp.message(F.text.contains("http"))
async def handle_url(message: types.Message, state: FSMContext):
    """Handle product URLs"""
    user_id = message.from_user.id
    
    # Check if user exists
    user = db.get_user(user_id)
    if not user:
        await message.answer("❌ Please use /start first to initialize your account.")
        return
    
    # Extract URL from message
    text = message.text
    urls = []
    
    # Simple URL extraction (can be improved with regex)
    words = text.split()
    for word in words:
        if word.startswith(('http://', 'https://')):
            urls.append(word)
    
    if not urls:
        return  # Not a URL message
    
    url = urls[0]
    
    try:
        # Check if URL is supported
        is_supported, site_name = scraper.is_supported_site(url)
        if not is_supported:
            await message.answer(
                "❌ Unsupported website. Please use:\n"
                "• Amazon\n"
                "• AliExpress\n"
                "• Jumia\n"
                "• Konga"
            )
            return
        
        # Extract product information
        await message.answer("🔍 Extracting product information...")
        product_info = scraper.extract_product_info(url)
        
        # Store product info in state for target price input
        await state.update_data(
            url=url,
            title=product_info['title'],
            price=product_info['price'],
            currency=product_info['currency'],
            image_url=product_info['image_url'],
            site_name=product_info['site_name']
        )
        
        # Ask for target price
        price_text = f"{product_info['currency']}{product_info['price']:,.2f}"
        await message.answer(
            f"📦 **{product_info['title']}**\n"
            f"💰 Current Price: {price_text}\n\n"
            f"🎯 **Set a target price?** (optional)\n"
            f"Reply with a price (e.g., {product_info['currency']}1000) or send 'skip' to continue without a target.",
            parse_mode="Markdown"
        )
        
        await state.set_state(ProductStates.waiting_for_target_price)
        
    except ValueError as e:
        await message.answer(f"❌ Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        await message.answer("❌ Sorry, I couldn't process this product. Please try again later.")

@dp.message(ProductStates.waiting_for_target_price)
async def handle_target_price(message: types.Message, state: FSMContext):
    """Handle target price input"""
    user_id = message.from_user.id
    text = message.text.strip().lower()
    
    # Get stored product data
    data = await state.get_data()
    
    target_price = None
    if text != 'skip':
        try:
            # Extract price from text
            import re
            price_match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
            if price_match:
                target_price = float(price_match.group().replace(',', ''))
            else:
                await message.answer("❌ Invalid price format. Please enter a number or 'skip'.")
                return
        except ValueError:
            await message.answer("❌ Invalid price format. Please enter a number or 'skip'.")
            return
    
    try:
        # Add product to database
        if target_price is not None:
            product_id = db.add_product(
                user_id=user_id,
                url=data['url'],
                title=data['title'],
                current_price=data['price'],
                currency=data['currency'],
                image_url=data['image_url'],
                target_price=target_price,
                site_name=data['site_name']
            )
        else:
            product_id = db.add_product(
                user_id=user_id,
                url=data['url'],
                title=data['title'],
                current_price=data['price'],
                currency=data['currency'],
                image_url=data['image_url'],
                target_price=0.0,
                site_name=data['site_name']
            )
        
        # Format response
        price_text = f"{data['currency']}{data['price']:,.2f}"
        target_text = f"\n🎯 Target Price: {data['currency']}{target_price:,.2f}" if target_price else ""
        
        response_text = (
            f"✅ **Tracking Started!**\n\n"
            f"📦 **{data['title']}**\n"
            f"💰 Current Price: {price_text}{target_text}\n\n"
            f"🔔 You'll be notified when the price drops!"
        )
        
        # Get product for keyboard
        products = db.get_user_products(user_id)
        product = next((p for p in products if p['id'] == product_id), None)
        
        if product:
            keyboard = get_product_keyboard(product['id'], product['affiliate_url'])
            await message.answer(response_text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(response_text, parse_mode="Markdown")
        
        # Clear state
        await state.clear()
        
    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
        await state.clear()
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        await message.answer("❌ Sorry, I couldn't add this product. Please try again later.")
        await state.clear()

# Callback query handlers
@dp.callback_query(lambda c: c.data.startswith('remove_'))
async def handle_remove_callback(callback: types.CallbackQuery):
    """Handle remove product callback"""
    user_id = callback.from_user.id
    
    if callback.data == "cancel_remove":
        await callback.message.delete()
        await callback.answer("❌ Cancelled")
        return
    
    try:
        product_id = int(callback.data.split('_')[1])
        
        # Remove product
        success = db.remove_product(product_id, user_id)
        
        if success:
            await callback.message.edit_text("✅ Product removed from tracking!")
        else:
            await callback.answer("❌ Product not found or you don't have permission.")
    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}")

@dp.callback_query(lambda c: c.data.startswith('history_'))
async def handle_history_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    product_id = int(callback.data.split('_')[1])
    # Get product and check ownership
    products = db.get_user_products(user_id)
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        await callback.answer("❌ Product not found or you don't have permission.")
        return
    # Get price history
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT price, currency, recorded_at FROM price_history WHERE product_id = ? ORDER BY recorded_at DESC', (product_id,))
    history = cursor.fetchall()
    conn.close()
    if not history:
        await callback.message.edit_text("No price history found for this product.")
        return
    text = f"📈 <b>Price History for:</b>\n<b>{product['title']}</b>\n\n"
    for row in history:
        date = row['recorded_at'][:10]
        price = f"{row['currency']}{row['price']:,.2f}"
        text += f"{date}: {price}\n"
    await callback.message.edit_text(text, parse_mode="HTML")

async def main():
    # Start the scheduler
    start_scheduler(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())