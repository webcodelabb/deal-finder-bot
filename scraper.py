import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, Optional, Tuple
from config import SUPPORTED_SITES, USER_AGENT

class ProductScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def is_supported_site(self, url: str) -> Tuple[bool, str]:
        """Check if URL is from a supported site and return site name"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        for site_name, site_info in SUPPORTED_SITES.items():
            if any(supported_domain in domain for supported_domain in site_info['domains']):
                return True, site_name
        
        return False, None
    
    def extract_product_info(self, url: str) -> Dict:
        """Extract product information from URL"""
        is_supported, site_name = self.is_supported_site(url)
        if not is_supported:
            raise ValueError("Unsupported website. Please use Amazon, AliExpress, Jumia, or Konga.")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if site_name == 'amazon':
                return self._scrape_amazon(soup, url)
            elif site_name == 'aliexpress':
                return self._scrape_aliexpress(soup, url)
            elif site_name == 'jumia':
                return self._scrape_jumia(soup, url)
            elif site_name == 'konga':
                return self._scrape_konga(soup, url)
            else:
                raise ValueError(f"Scraper not implemented for {site_name}")
                
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch product page: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse product information: {str(e)}")
    
    def _scrape_amazon(self, soup: BeautifulSoup, url: str) -> Dict:
        """Scrape Amazon product page"""
        # Product title
        title_selectors = [
            '#productTitle',
            'h1.a-size-large',
            'h1.a-size-base-plus',
            '.a-size-large.product-title-word-break'
        ]
        
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # Price
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price-range .a-offscreen'
        ]
        
        price = None
        currency = '$'
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract price and currency
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group().replace(',', ''))
                    # Detect currency
                    if '€' in price_text:
                        currency = '€'
                    elif '£' in price_text:
                        currency = '£'
                    elif '₹' in price_text:
                        currency = '₹'
                    elif '¥' in price_text:
                        currency = '¥'
                    elif 'R$' in price_text:
                        currency = 'R$'
                    elif 'MX$' in price_text:
                        currency = 'MX$'
                    elif 'A$' in price_text:
                        currency = 'A$'
                    break
        
        # Image
        image_selectors = [
            '#landingImage',
            '#imgBlkFront',
            '.a-dynamic-image',
            'img[data-old-hires]'
        ]
        
        image_url = None
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url:
                    break
        
        if not title:
            raise ValueError("Could not extract product title")
        if not price:
            raise ValueError("Could not extract product price")
        
        return {
            'title': title,
            'price': price,
            'currency': currency,
            'image_url': image_url,
            'site_name': 'amazon'
        }
    
    def _scrape_aliexpress(self, soup: BeautifulSoup, url: str) -> Dict:
        """Scrape AliExpress product page"""
        # Product title
        title_selectors = [
            '.product-title',
            'h1.product-title-text',
            '.product-title-text'
        ]
        
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # Price
        price_selectors = [
            '.product-price-current',
            '.product-price-value',
            '.price-current'
        ]
        
        price = None
        currency = '$'
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group().replace(',', ''))
                    if '€' in price_text:
                        currency = '€'
                    elif '¥' in price_text:
                        currency = '¥'
                    break
        
        # Image
        image_selectors = [
            '.images-view-item img',
            '.product-image img',
            '.magnifier-image'
        ]
        
        image_url = None
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url:
                    break
        
        if not title:
            raise ValueError("Could not extract product title")
        if not price:
            raise ValueError("Could not extract product price")
        
        return {
            'title': title,
            'price': price,
            'currency': currency,
            'image_url': image_url,
            'site_name': 'aliexpress'
        }
    
    def _scrape_jumia(self, soup: BeautifulSoup, url: str) -> Dict:
        """Scrape Jumia product page"""
        # Product title
        title_selectors = [
            'h1[data-name="product-title"]',
            '.product-title',
            'h1.title'
        ]
        
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # Price
        price_selectors = [
            '.price',
            '.product-price',
            '.price-current',
            '[data-price]'
        ]
        
        price = None
        currency = '₦'
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group().replace(',', ''))
                    # Detect currency based on domain
                    if 'jumia.co.ke' in url:
                        currency = 'KSh'
                    elif 'jumia.com.gh' in url:
                        currency = 'GH₵'
                    elif 'jumia.co.ug' in url:
                        currency = 'USh'
                    elif 'jumia.com.tn' in url:
                        currency = 'TND'
                    elif 'jumia.dz' in url:
                        currency = 'DZD'
                    elif 'jumia.ma' in url:
                        currency = 'MAD'
                    elif 'jumia.com.eg' in url:
                        currency = 'EGP'
                    break
        
        # Image
        image_selectors = [
            '.image-gallery-slide img',
            '.product-image img',
            '.gallery-image'
        ]
        
        image_url = None
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url:
                    break
        
        if not title:
            raise ValueError("Could not extract product title")
        if not price:
            raise ValueError("Could not extract product price")
        
        return {
            'title': title,
            'price': price,
            'currency': currency,
            'image_url': image_url,
            'site_name': 'jumia'
        }
    
    def _scrape_konga(self, soup: BeautifulSoup, url: str) -> Dict:
        """Scrape Konga product page"""
        # Product title
        title_selectors = [
            '.product-name',
            'h1.product-title',
            '.product-details h1'
        ]
        
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # Price
        price_selectors = [
            '.price',
            '.product-price',
            '.current-price',
            '[data-price]'
        ]
        
        price = None
        currency = '₦'
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group().replace(',', ''))
                    break
        
        # Image
        image_selectors = [
            '.product-image img',
            '.gallery-image img',
            '.main-image'
        ]
        
        image_url = None
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url:
                    break
        
        if not title:
            raise ValueError("Could not extract product title")
        if not price:
            raise ValueError("Could not extract product price")
        
        return {
            'title': title,
            'price': price,
            'currency': currency,
            'image_url': image_url,
            'site_name': 'konga'
        }

def clean_product_url(url: str, site_name: str) -> str:
    from urllib.parse import urlparse, parse_qs, urlunparse, unquote
    if site_name == 'amazon':
        # Try to extract /dp/ASIN from any Amazon URL
        import re
        match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if match:
            asin = match.group(1)
            return f"https://www.amazon.com/dp/{asin}"
        # Sometimes ASIN is in /gp/product/ASIN
        match = re.search(r"/gp/product/([A-Z0-9]{10})", url)
        if match:
            asin = match.group(1)
            return f"https://www.amazon.com/dp/{asin}"
        # If url is a redirect (e.g., /sspa/click?...&url=%2Fdp%2FB09VVDYM7N%2F...)
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if 'url' in qs:
            decoded = unquote(qs['url'][0])
            return clean_product_url(decoded, 'amazon')
        return url.split('?')[0]
    elif site_name == 'aliexpress':
        # Remove query params, keep only main product URL
        parsed = urlparse(url)
        clean_url = urlunparse(parsed._replace(query="", fragment=""))
        return clean_url
    elif site_name == 'jumia':
        # Remove query params, keep only main product URL
        parsed = urlparse(url)
        clean_url = urlunparse(parsed._replace(query="", fragment=""))
        return clean_url
    elif site_name == 'konga':
        # Remove query params, keep only main product URL
        parsed = urlparse(url)
        clean_url = urlunparse(parsed._replace(query="", fragment=""))
        return clean_url
    else:
        return url

# Global scraper instance
scraper = ProductScraper() 
