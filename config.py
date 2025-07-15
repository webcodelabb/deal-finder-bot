import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Database Configuration
DATABASE_PATH = "deal_finder.db"

# Supported E-commerce Sites
SUPPORTED_SITES = {
    'amazon': {
        'domains': ['amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr', 'amazon.it', 'amazon.es', 'amazon.ca', 'amazon.com.au', 'amazon.in', 'amazon.com.br', 'amazon.com.mx', 'amazon.co.jp'],
        'affiliate_tag': '&tag=webcodelab-20',  # Replace with your Amazon Associates tag
        'currency_symbols': ['$', '€', '£', '₹', '¥', 'R$', 'MX$', 'A$']
    },
    'aliexpress': {
        'domains': ['aliexpress.com', 'aliexpress.ru'],
        'affiliate_tag': '&aff_platform=link-c-tool&src=go',  # Replace with your AliExpress affiliate link
        'currency_symbols': ['$', '€', '¥']
    },
    'jumia': {
        'domains': ['jumia.com.ng', 'jumia.co.ke', 'jumia.com.gh', 'jumia.co.ug', 'jumia.com.tn', 'jumia.dz', 'jumia.ma', 'jumia.com.eg', 'jumia.com.ci', 'jumia.sn', 'jumia.cm', 'jumia.bf', 'jumia.ne', 'jumia.ml', 'jumia.mr', 'jumia.td', 'jumia.cf', 'jumia.cg', 'jumia.cd', 'jumia.ga', 'jumia.gq', 'jumia.st', 'jumia.gm', 'jumia.gw', 'jumia.gn', 'jumia.sl', 'jumia.lr', 'jumia.tg', 'jumia.bj', 'jumia.tg'],
        'affiliate_tag': '?aff_id=webcodelab-20',  # Your Jumia affiliate ID
        'currency_symbols': ['₦', 'KSh', 'GH₵', 'USh', 'TND', 'DZD', 'MAD', 'EGP', 'XOF', 'XAF', 'CDF', 'XAF', 'XOF', 'XOF', 'XOF', 'XAF', 'XAF', 'XAF', 'CDF', 'XAF', 'XAF', 'XAF', 'XAF', 'XAF', 'XAF', 'XAF', 'XAF', 'XAF', 'XAF']
    },
    'konga': {
        'domains': ['konga.com'],
        'affiliate_tag': '?utm_source=YOUR_KONGA_TAG',  # Replace with your Konga affiliate tag
        'currency_symbols': ['₦']
    }
}

# Product Limits
DEFAULT_MAX_PRODUCTS = 3
REFERRAL_BONUS_PRODUCTS = 1

# Check Intervals (in hours)
STANDARD_CHECK_INTERVAL = 18  # 18 hours for free users
PREMIUM_CHECK_INTERVAL = 8    # 8 hours for users with referrals

# User Agent for web scraping
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Bot Messages
WELCOME_MESSAGE = """
🤖 Welcome to DealFinder Bot!

I'm your personal price tracker for e-commerce sites. I'll monitor product prices and notify you when they drop!

🛒 **Supported Sites:**
• Amazon (US, UK, DE, FR, IT, ES, CA, AU, IN, BR, MX, JP)
• AliExpress
• Jumia (Nigeria, Kenya, Ghana, Uganda, Tunisia, Algeria, Morocco, Egypt, Ivory Coast, Senegal, Cameroon, Burkina Faso, Niger, Mali, Mauritania, Chad, Central African Republic, Congo, Democratic Republic of Congo, Gabon, Equatorial Guinea, Sao Tome and Principe, Gambia, Guinea-Bissau, Guinea, Sierra Leone, Liberia, Togo, Benin, Togo)
• Konga (Nigeria)

📊 **Free Features:**
• Track up to 3 products
• Price drop alerts
• Target price notifications

🎁 **Refer Friends & Unlock More:**
• Each referral = +1 product slot
• Faster price checks
• Priority notifications

📝 **How to use:**
1. Send me a product link from any supported site
2. Set a target price (optional)
3. I'll start tracking and notify you of price changes!

Ready to start? Send me a product link! 🚀
"""

HELP_MESSAGE = """
📚 **DealFinder Bot Commands:**

/start - Welcome message and instructions
/help - Show this help message
/myproducts - View your tracked products
/remove - Remove a tracked product
/referral - Get your referral link and stats
/limits - Check your tracking limits

🔗 **Adding Products:**
Simply send me a product link from:
• Amazon
• AliExpress  
• Jumia
• Konga

💰 **Target Prices:**
When you add a product, you can set a target price. I'll notify you when the price drops to or below your target!

🎁 **Referral System:**
• Share your referral link with friends
• Each friend who joins = +1 product slot for you
• Unlock premium features with referrals

Need help? Contact @your_support_username
""" 
