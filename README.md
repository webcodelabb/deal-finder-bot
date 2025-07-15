# DealFinder Bot 🤖

A Telegram bot that helps users track product prices from e-commerce sites like Amazon, AliExpress, Jumia, and Konga. Get notified when prices drop or reach your target price!

## ✨ Features

### 🛒 **Supported Sites**
- **Amazon** (US, UK, DE, FR, IT, ES, CA, AU, IN, BR, MX, JP)
- **AliExpress**
- **Jumia** (Multiple African countries)
- **Konga** (Nigeria)

### 🎯 **Core Features**
- **Price Tracking**: Monitor product prices automatically
- **Price Drop Alerts**: Get notified when prices decrease
- **Target Price Alerts**: Set target prices and get notified when reached
- **Affiliate Links**: Automatic affiliate link generation for all supported sites
- **Product History**: View price history for tracked products

### 🎁 **Referral System**
- **Free Tier**: Track up to 3 products
- **Referral Rewards**: Each referral = +1 product slot
- **Premium Features**: Faster price checks for users with referrals

### 📱 **Commands**
- `/start` - Welcome message and instructions
- `/help` - Show help message
- `/myproducts` - View your tracked products
- `/remove` - Remove a tracked product
- `/referral` - Get your referral link and stats
- `/limits` - Check your tracking limits
- `/history` - View price history for products

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd deal_finder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ```

4. **Configure affiliate IDs** (optional)
   Edit `config.py` and update the affiliate tags for your preferred sites:
   ```python
   'affiliate_tag': '&tag=your_amazon_tag',  # Amazon
   'affiliate_tag': '?aff_id=your_jumia_id',  # Jumia
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

## 🌐 Deployment

### Railway (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Railway**
   - Go to [Railway](https://railway.app/)
   - Connect your GitHub repository
   - Add environment variable: `BOT_TOKEN=your_token`
   - Deploy!

### Other Platforms

#### Render
- Connect your GitHub repo
- Set build command: `pip install -r requirements.txt`
- Set start command: `python bot.py`
- Add environment variable: `BOT_TOKEN`

#### Heroku
- Install Heroku CLI
- Create app: `heroku create your-app-name`
- Set config: `heroku config:set BOT_TOKEN=your_token`
- Deploy: `git push heroku main`

## 📊 Database Schema

The bot uses SQLite3 with the following tables:

### Users Table
- `telegram_id` (Primary Key)
- `username`
- `referral_code` (Unique)
- `referred_by`
- `referral_count`
- `max_products`
- `premium_features`
- `created_at`

### Products Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `url`
- `title`
- `current_price`
- `target_price`
- `currency`
- `image_url`
- `affiliate_url`
- `site_name`
- `created_at`
- `last_checked`

### Price History Table
- `id` (Primary Key)
- `product_id` (Foreign Key)
- `price`
- `currency`
- `recorded_at`

## ⚙️ Configuration

### Check Intervals
- **Standard users**: Every 18 hours
- **Premium users**: Every 8 hours

### Product Limits
- **Default**: 3 products
- **Per referral**: +1 product slot

### Supported Currencies
- USD ($), EUR (€), GBP (£), INR (₹), JPY (¥)
- NGN (₦), KSh, GH₵, USh, and more

## 🔧 Customization

### Adding New Sites
1. Update `SUPPORTED_SITES` in `config.py`
2. Add scraping logic in `scraper.py`
3. Test with sample URLs

### Modifying Check Intervals
Edit `config.py`:
```python
STANDARD_CHECK_INTERVAL = 18  # hours
PREMIUM_CHECK_INTERVAL = 8    # hours
```

### Changing Product Limits
Edit `config.py`:
```python
DEFAULT_MAX_PRODUCTS = 3
REFERRAL_BONUS_PRODUCTS = 1
```

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if BOT_TOKEN is set correctly
   - Verify bot is not blocked by users

2. **Scraping errors**
   - Sites may change their HTML structure
   - Update selectors in `scraper.py`

3. **Database errors**
   - Check file permissions
   - Ensure SQLite is working

### Logs
The bot logs to console. For production, consider using a logging service.

## 📈 Monitoring

### Health Checks
- Bot responds to `/start`
- Scheduled jobs run without errors
- Database operations succeed

### Metrics to Track
- Active users
- Products tracked
- Successful referrals
- Price alerts sent

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:
1. Check the troubleshooting section
2. Review the logs
3. Open an issue on GitHub

---

**Made with ❤️ for deal hunters everywhere!** 