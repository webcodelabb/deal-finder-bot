import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                referral_count INTEGER DEFAULT 0,
                max_products INTEGER DEFAULT 3,
                premium_features BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users(telegram_id)
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT NOT NULL,
                title TEXT,
                current_price REAL,
                target_price REAL,
                currency TEXT,
                image_url TEXT,
                affiliate_url TEXT,
                site_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        ''')
        
        # Price history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL,
                currency TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, telegram_id: int, username: str = None, referred_by: int = None) -> str:
        """Create a new user and return their referral code"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generate unique referral code
        referral_code = str(uuid.uuid4())[:8].upper()
        
        try:
            cursor.execute('''
                INSERT INTO users (telegram_id, username, referral_code, referred_by)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, referral_code, referred_by))
            
            # If user was referred, update referrer's count
            if referred_by:
                cursor.execute('''
                    UPDATE users 
                    SET referral_count = referral_count + 1,
                        max_products = max_products + 1,
                        premium_features = TRUE
                    WHERE telegram_id = ?
                ''', (referred_by,))
            
            conn.commit()
            return referral_code
            
        except sqlite3.IntegrityError:
            # User already exists, return existing referral code
            cursor.execute('SELECT referral_code FROM users WHERE telegram_id = ?', (telegram_id,))
            result = cursor.fetchone()
            return result['referral_code'] if result else None
        finally:
            conn.close()
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict]:
        """Get user by referral code"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users WHERE referral_code = ?
        ''', (referral_code,))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def add_product(self, user_id: int, url: str, title: str, current_price: float, 
                   currency: str, image_url: str = None, target_price: float = None, 
                   site_name: str = None) -> int:
        """Add a new product to track"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if user has reached their product limit
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        current_count = self.get_user_product_count(user_id)
        if current_count >= user['max_products']:
            raise ValueError(f"You can only track {user['max_products']} products. Refer friends to unlock more slots!")
        
        # Add affiliate tag to URL
        affiliate_url = self.add_affiliate_tag(url, site_name)
        
        cursor.execute('''
            INSERT INTO products (user_id, url, title, current_price, target_price, 
                                currency, image_url, affiliate_url, site_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, url, title, current_price, target_price, currency, 
              image_url, affiliate_url, site_name))
        
        product_id = cursor.lastrowid
        
        # Add to price history
        cursor.execute('''
            INSERT INTO price_history (product_id, price, currency)
            VALUES (?, ?, ?)
        ''', (product_id, current_price, currency))
        
        conn.commit()
        conn.close()
        
        return product_id
    
    def get_user_products(self, user_id: int) -> List[Dict]:
        """Get all products tracked by a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_user_product_count(self, user_id: int) -> int:
        """Get count of products tracked by a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM products WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0
    
    def remove_product(self, product_id: int, user_id: int) -> bool:
        """Remove a product (only if owned by the user)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM products WHERE id = ? AND user_id = ?
        ''', (product_id, user_id))
        
        deleted = cursor.rowcount > 0
        
        if deleted:
            # Also remove from price history
            cursor.execute('DELETE FROM price_history WHERE product_id = ?', (product_id,))
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_all_tracked_products(self) -> List[Dict]:
        """Get all products for price checking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.telegram_id, u.premium_features 
            FROM products p 
            JOIN users u ON p.user_id = u.telegram_id
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def update_product_price(self, product_id: int, new_price: float, currency: str):
        """Update product price and add to history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Update current price
        cursor.execute('''
            UPDATE products 
            SET current_price = ?, currency = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_price, currency, product_id))
        
        # Add to price history
        cursor.execute('''
            INSERT INTO price_history (product_id, price, currency)
            VALUES (?, ?, ?)
        ''', (product_id, new_price, currency))
        
        conn.commit()
        conn.close()
    
    def add_affiliate_tag(self, url: str, site_name: str) -> str:
        """Add affiliate tag to URL based on site"""
        from config import SUPPORTED_SITES
        
        if not site_name or site_name not in SUPPORTED_SITES:
            return url
        
        affiliate_tag = SUPPORTED_SITES[site_name]['affiliate_tag']
        
        if '?' in url:
            return url + affiliate_tag
        else:
            return url + affiliate_tag.replace('&', '?')
    
    def get_referral_stats(self, user_id: int) -> Dict:
        """Get user's referral statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute('''
            SELECT referral_count, max_products, premium_features 
            FROM users WHERE telegram_id = ?
        ''', (user_id,))
        
        user_result = cursor.fetchone()
        
        # Get referred users
        cursor.execute('''
            SELECT telegram_id, username, created_at 
            FROM users WHERE referred_by = ?
        ''', (user_id,))
        
        referred_users = cursor.fetchall()
        
        conn.close()
        
        if not user_result:
            return None
        
        return {
            'referral_count': user_result['referral_count'],
            'max_products': user_result['max_products'],
            'premium_features': user_result['premium_features'],
            'referred_users': [dict(user) for user in referred_users]
        }

# Global database instance
db = Database() 
