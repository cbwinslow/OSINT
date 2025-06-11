#!/usr/bin/env python3
"""
Comprehensive OSINT API Framework
Enhanced version covering all services identified in the bookmarklet collection
"""

import requests
import time
import json
import re
from urllib.parse import quote, urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any, Union
import logging
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import base64
from fake_useragent import UserAgent
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class OSINTResult:
    """Enhanced result format for all OSINT queries"""
    service: str
    query: str
    query_type: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = None
    response_time: float = 0.0
    status_code: Optional[int] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class EnhancedSession:
    """Enhanced session with rotation capabilities"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.proxy_list = []  # Can be populated with proxy servers
        self.current_proxy = None
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with random user agent"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """Make request with error handling and retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Rotate user agent on retries
                if attempt > 0:
                    self._update_headers()
                
                response = self.session.request(method, url, timeout=30, **kwargs)
                return response
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(random.uniform(1, 3))
        
        raise Exception("Max retries exceeded")

class BaseOSINTService(ABC):
    """Enhanced base class for all OSINT services"""
    
    def __init__(self, name: str, base_url: str = "", rate_limit: float = 1.0):
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.last_request = 0
        self.session = EnhancedSession()
        self.driver = None  # Selenium driver for JS-heavy sites
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()
    
    def _get_selenium_driver(self):
        """Initialize Selenium driver if needed"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            try:
                self.driver = webdriver.Chrome(
                    ChromeDriverManager().install(),
                    options=chrome_options
                )
            except Exception as e:
                logger.warning(f"Could not initialize Selenium driver: {e}")
                self.driver = None
        
        return self.driver
    
    def _make_request(self, url: str, method: str = 'GET', use_selenium: bool = False, **kwargs) -> Union[requests.Response, Any]:
        """Make HTTP request with rate limiting and optional Selenium"""
        self._rate_limit()
        start_time = time.time()
        
        try:
            if use_selenium and self._get_selenium_driver():
                self.driver.get(url)
                # Return a mock response-like object
                class SeleniumResponse:
                    def __init__(self, driver):
                        self.text = driver.page_source
                        self.status_code = 200
                        self.url = driver.current_url
                
                response = SeleniumResponse(self.driver)
            else:
                response = self.session.make_request(url, method, **kwargs)
            
            response_time = time.time() - start_time
            logger.info(f"{self.name}: {method} {url} -> {getattr(response, 'status_code', 'N/A')} ({response_time:.2f}s)")
            return response
            
        except Exception as e:
            logger.error(f"{self.name}: Request failed for {url}: {e}")
            raise
    
    @abstractmethod
    def search(self, query: str, query_type: str = 'default') -> OSINTResult:
        """Abstract method for performing searches"""
        pass

class SocialMediaOSINT(BaseOSINTService):
    """Comprehensive social media OSINT service"""
    
    def __init__(self):
        super().__init__("SocialMediaOSINT")
    
    def search_gab(self, query: str, query_type: str = 'username') -> OSINTResult:
        """Enhanced Gab search with multiple data extraction methods"""
        start_time = time.time()
        
        try:
            if query_type == 'username':
                url = f"https://gab.com/{query}"
            elif query_type == 'hashtag':
                url = f"https://gab.com/tags/{query}"
            else:
                return OSINTResult(
                    service="Gab",
                    query=query,
                    query_type=query_type,
                    success=False,
                    error="Unsupported query type",
                    data={}
                )
            
            response = self._make_request(url)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                profile_data = self._extract_gab_data(soup, response.text, query_type)
                
                return OSINTResult(
                    service="Gab",
                    query=query,
                    query_type=query_type,
                    success=True,
                    data=profile_data,
                    response_time=response_time,
                    status_code=response.status_code
                )
            else:
                return OSINTResult(
                    service="Gab",
                    query=query,
                    query_type=query_type,
                    success=False,
                    error=f"Profile not found (HTTP {response.status_code})",
                    data={},
                    response_time=response_time,
                    status_code=response.status_code
                )
                
        except Exception as e:
            return OSINTResult(
                service="Gab",
                query=query,
                query_type=query_type,
                success=False,
                error=str(e),
                data={},
                response_time=time.time() - start_time
            )
    
    def _extract_gab_data(self, soup: BeautifulSoup, html_content: str, query_type: str) -> Dict[str, Any]:
        """Extract comprehensive data from Gab pages using bookmarklet methods"""
        data = {'profile_exists': True}
        
        # Extract avatar using bookmarklet logic
        if 'parallax"' in html_content:
            try:
                avatar_section = html_content.split('parallax"')[1]
                avatar_url = avatar_section.split('&quot;')[1]
                data['avatar_url'] = avatar_url
                data['avatar_full_size'] = avatar_url  # Already full size from this method
            except (IndexError, ValueError):
                pass
        
        # Extract header image using bookmarklet logic  
        if 'account__header__info' in html_content:
            try:
                header_section = html_content.split('account__header__info')[1]
                header_url = header_section.split('="')[1].split('"')[0]
                data['header_image_url'] = header_url
            except (IndexError, ValueError):
                pass
        
        # Extract video content using bookmarklet logic
        if 'playsinline=' in html_content:
            try:
                video_section = html_content.split('playsinline=')[1]
                video_url = video_section.split('src="')[1].split('"')[0]
                poster_url = video_section.split('poster="')[1].split('"')[0]
                data['video_url'] = video_url
                data['video_thumbnail'] = poster_url
            except (IndexError, ValueError):
                pass
        
        # Extract standard profile information
        canonical_link = soup.find('link', {'rel': 'canonical'})
        if canonical_link:
            data['canonical_url'] = canonical_link.get('href')
        
        # Extract profile name and bio
        title = soup.find('title')
        if title:
            data['page_title'] = title.text
        
        return data
    
    def search_tiktok(self, query: str, query_type: str = 'username') -> OSINTResult:
        """Enhanced TikTok search with comprehensive data extraction"""
        start_time = time.time()
        
        try:
            if query_type == 'username':
                url = f"https://www.tiktok.com/@{query}"
            elif query_type == 'hashtag':
                url = f"https://www.tiktok.com/tag/{query}"
            else:
                return OSINTResult(
                    service="TikTok",
                    query=query,
                    query_type=query_type,
                    success=False,
                    error="Unsupported query type",
                    data={}
                )
            
            # TikTok heavily uses JavaScript, so we'll try both methods
            response = self._make_request(url, use_selenium=True)
            response_time = time.time() - start_time
            
            if hasattr(response, 'status_code') and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')  
                profile_data = self._extract_tiktok_data(soup, response.text, query_type)
                
                return OSINTResult(
                    service="TikTok",
                    query=query,
                    query_type=query_type,
                    success=True,
                    data=profile_data,
                    response_time=response_time,
                    status_code=getattr(response, 'status_code', 200)
                )
            else:
                return OSINTResult(
                    service="TikTok",
                    query=query,
                    query_type=query_type,
                    success=False,
                    error="Could not access TikTok profile",
                    data={},
                    response_time=response_time
                )
                
        except Exception as e:
            return OSINTResult(
                service="TikTok",
                query=query,
                query_type=query_type,
                success=False,
                error=str(e),
                data={},
                response_time=time.time() - start_time
            )
    
    def _extract_tiktok_data(self, soup: BeautifulSoup, html_content: str, query_type: str) -> Dict[str, Any]:
        """Extract TikTok data using bookmarklet methods"""
        data = {'profile_exists': True}
        
        # Extract profile photo using bookmarklet logic
        if 'background-image:url(' in html_content:
            try:
                photo_section = html_content.split('background-image:url(')[1]
                photo_url = photo_section.split(')')[0].strip('"\'')
                data['profile_photo'] = photo_url
            except (IndexError, ValueError):
                pass
        
        # Extract video data (when viewing a specific video)
        if 'uploadDate":"' in html_content:
            try:
                # Extract upload date
                date_section = html_content.split('uploadDate":"')[1]
                upload_date = date_section.split('"')[0]
                data['video_upload_date'] = upload_date
            except (IndexError, ValueError):
                pass
        
        # Extract video thumbnail  
        if 'poster="' in html_content:
            try:
                thumb_section = html_content.split('poster="')[1]
                thumbnail_url = thumb_section.split('"')[0]
                data['video_thumbnail'] = thumbnail_url
            except (IndexError, ValueError):
                pass
        
        # Extract video download URL
        if 'poster="' in html_content and 'src="' in html_content:
            try:
                video_section = html_content.split('poster="')[1]
                video_url = video_section.split('src="')[1].split('"')[0]
                video_url = video_url.replace("amp;", "")
                data['video_download_url'] = video_url
            except (IndexError, ValueError):
                pass
        
        # Extract full-size user photo (removing size restrictions)
        if 'background-image: url(&quot;' in html_content:
            try:
                photo_section = html_content.split('background-image: url(&quot;')[1]
                photo_url = photo_section.split('&quot')[0]
                photo_url = photo_url.replace("_100x100", "")  # Remove size restriction
                data['full_size_photo'] = photo_url
            except (IndexError, ValueError):
                pass
        
        return data
    
    def search_linkedin(self, query: str, query_type: str = 'profile_url') -> OSINTResult:
        """LinkedIn profile enhancement"""
        start_time = time.time()
        
        try:
            data = {}
            
            if query_type == 'profile_photo' and query.startswith('https://'):
                # Extract larger profile photo
                photo_url = query + "detail/photo/"
                data['enhanced_photo_url'] = photo_url
                
            elif query_type == 'recent_activity' and query.startswith('https://'):
                # Get recent activity URL
                activity_url = query + "detail/recent-activity/"
                data['recent_activity_url'] = activity_url
                
            elif query_type == 'email_lookup':
                # Note: This functionality was removed by LinkedIn
                data['email_lookup_status'] = 'deprecated'
                data['note'] = 'LinkedIn removed email lookup functionality'
            
            return OSINTResult(
                service="LinkedIn",
                query=query,
                query_type=query_type,
                success=True,
                data=data,
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            return OSINTResult(
                service="LinkedIn",
                query=query,
                query_type=query_type,
                success=False,
                error=str(e),
                data={},
                response_time=time.time() - start_time
            )
    
    def search_reddit(self, query: str, query_type: str = 'username') -> OSINTResult:
        """Reddit profile analysis"""
        start_time = time.time()
        
        try:
            data = {}
            
            if query_type == 'removeddit':
                # Convert Reddit URL to Removeddit
                if 'reddit.com' in query:
                    removeddit_url = query.replace("www.reddit.com/", "www.removeddit.com/")
                    data['removeddit_url'] = removeddit_url
            
            elif query_type == 'profile_analysis' and query.startswith('https://'):
                response = self._make_request(query)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract banner using bookmarklet logic
                    html_content = response.text
                    if '<div style="background-image:url(' in html_content:
                        try:
                            banner_section = html_content.split('<div style="background-image:url(')[1]
                            banner_url = banner_section.split('?width')[0]
                            data['banner_url'] = banner_url
                        except (IndexError, ValueError):
                            pass
                    
                    # Extract profile photo using bookmarklet logic
                    if '"Profile icon" src="' in html_content:
                        try:
                            avatar_section = html_content.split('"Profile icon" src="')[1]
                            avatar_url = avatar_section.split('" class=')[0]
                            
                            # Clean up the URL
                            if '.png' in avatar_url:
                                avatar_url = avatar_url.split('.png')[0] + '.png'
                            elif '.jpg' in avatar_url:
                                avatar_url = avatar_url.split('.jpg')[0] + '.jpg'
                            
                            data['avatar_url'] = avatar_url
                        except (IndexError, ValueError):
                            pass
            
            return OSINTResult(
                service="Reddit",
                query=query,
                query_type=query_type,
                success=True,
                data=data,
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            return OSINTResult(
                service="Reddit",
                query=query,
                query_type=query_type,
                success=False,
                error=str(e),
                data={},
                response_time=time.time() - start_time
            )
    
    def search_tumblr(self, query: str, query_type: str = 'blog') -> OSINTResult:
        """Tumblr blog analysis"""
        start_time = time.time()
        
        try:
            data = {}
            blog_name = query.replace('.tumblr.com', '') if '.tumblr.com' in query else query
            
            # Generate Tumblr URLs using bookmarklet logic
            data['archive_url'] = f"http://{blog_name}.tumblr.com/archive"
            data['likes_url'] = f"http://{blog_name}.tumblr.com/likes"
            data['following_url'] = f"http://{blog_name}.tumblr.com/following"
            data['followers_url'] = f"http://{blog_name}.tumblr.com/followers"
            
            # Use Tumblr API for avatar
            avatar_api_url = f"https://api.tumblr.com/v2/blog/{blog_name}.tumblr.com/avatar/512"
            data['avatar_api_url'] = avatar_api_url
            
            # Try to fetch avatar
            try:
                avatar_response = self._make_request(avatar_api_url)
                if avatar_response.status_code == 200:
                    data['avatar_accessible'] = True
                    data['avatar_direct_url'] = avatar_response.url
                else:
                    data['avatar_accessible'] = False
            except:
                data['avatar_accessible'] = False
            
            return OSINTResult(
                service="Tumblr",
                query=query,
                query_type=query_type,
                success=True,
                data=data,
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            return OSINTResult(
                service="Tumblr",
                query=query,
                query_type=query_type,
                success=False,
                error=str(e),
                data={},
                response_time=time.time() - start_time
            )
    
    def search(self, query: str, query_type: str = 'username') -> List[OSINTResult]:
        """Generic search method that runs across all platforms"""
        results = []
        
        # Handle platform-specific queries like 'social_gab_username'
        if query_type.startswith('social_'):
            # Remove 'social_' prefix and parse platform
            remainder = query_type[7:]  # Remove 'social_'
            parts = remainder.split('_')
            if len(parts) >= 2:
                platform = parts[0]
                actual_query_type = '_'.join(parts[1:])
            else:
                platform = remainder
                actual_query_type = 'username'
        else:
            platform_queries = query_type.split('_')
            if len(platform_queries) > 1:
                platform, actual_query_type = platform_queries[0], '_'.join(platform_queries[1:])
            else:
                platform = 'all'
                actual_query_type = query_type
        
        if platform == 'all' or platform == 'gab':
            results.append(self.search_gab(query, actual_query_type))
        if platform == 'all' or platform == 'tiktok':
            results.append(self.search_tiktok(query, actual_query_type))
        if platform == 'all' or platform == 'linkedin':
            results.append(self.search_linkedin(query, actual_query_type))
        if platform == 'all' or platform == 'reddit':
            results.append(self.search_reddit(query, actual_query_type))
        if platform == 'all' or platform == 'tumblr':
            results.append(self.search_tumblr(query, actual_query_type))
        
        return results

class ImageAnalysisOSINT(BaseOSINTService):
    """Enhanced image analysis and reverse search service"""
    
    def __init__(self):
        super().__init__("ImageAnalysisOSINT")
        self.services = {
            'google': {
                'url': 'https://www.google.com/searchbyimage?&image_url={}',
                'name': 'Google Images'
            },
            'yandex': {
                'url': 'https://yandex.com/images/search?source=collections&rpt=imageview&url={}',
                'name': 'Yandex Images'
            },
            'tineye': {
                'url': 'https://www.tineye.com/search/?url={}',
                'name': 'TinEye'
            },
            'bing': {
                'url': 'https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIIRP&sbisrc=UrlPaste&q=imgurl:{}',
                'name': 'Bing Images'
            },
            'baidu': {
                'url': 'https://graph.baidu.com/details?isfromtusoupc=1tn=pc&carousel=0&image={}',
                'name': 'Baidu Images'
            }
        }
        self.exif_service = 'http://exif.regex.info/exif.cgi?&url={}'
    
    def search(self, query: str, query_type: str = 'reverse_image') -> OSINTResult:
        """Comprehensive image analysis"""
        start_time = time.time()
        results = {}
        
        # Reverse image search across all services
        for service_id, service_info in self.services.items():
            try:
                search_url = service_info['url'].format(quote(query))
                response = self._make_request(search_url)
                
                results[service_id] = {
                    'service_name': service_info['name'],
                    'search_url': search_url,
                    'status_code': response.status_code,
                    'accessible': response.status_code == 200,
                    'response_size': len(response.text) if hasattr(response, 'text') else 0
                }
                
                # Try to extract some basic results info
                if response.status_code == 200:
                    results[service_id]['has_results'] = self._analyze_search_results(service_id, response)
                
            except Exception as e:
                results[service_id] = {
                    'service_name': service_info['name'],
                    'status': 'error',
                    'error': str(e)
                }
        
        # EXIF data extraction
        exif_data = self._extract_exif_data(query)
        if exif_data:
            results['exif'] = exif_data
        
        return OSINTResult(
            service=self.name,
            query=query,
            query_type=query_type,
            success=any(r.get('accessible', False) for r in results.values()),
            data={
                'reverse_search_results': results,
                'total_accessible_services': sum(1 for r in results.values() if r.get('accessible', False))
            },
            response_time=time.time() - start_time
        )
    
    def _analyze_search_results(self, service: str, response) -> bool:
        """Analyze if reverse image search found results"""
        if not hasattr(response, 'text'):
            return False
        
        text_lower = response.text.lower()
        
        # Service-specific result detection
        if service == 'google':
            return 'no results found' not in text_lower and len(response.text) > 10000
        elif service == 'yandex':
            return 'serp-item' in response.text or 'similar' in text_lower
        elif service == 'tineye':
            return 'match' in text_lower and 'no matches' not in text_lower
        elif service == 'bing':
            return 'imgres' in response.text and len(response.text) > 5000
        elif service == 'baidu':
            return 'similar' in text_lower or len(response.text) > 10000
        
        return False
    
    def _extract_exif_data(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Extract EXIF data from image"""
        try:
            exif_url = self.exif_service.format(quote(image_url))
            response = self._make_request(exif_url)
            
            if response.status_code == 200:
                return {
                    'exif_url': exif_url,
                    'accessible': True,
                    'data_size': len(response.text)
                }
        except Exception as e:
            return {
                'exif_url': self.exif_service.format(quote(image_url)),
                'accessible': False,
                'error': str(e)
            }
        
        return None

class UtilityOSINT(BaseOSINTService):
    """Utility services for URL expansion, Pokemon Go, etc."""
    
    def __init__(self):
        super().__init__("UtilityOSINT")
        
        self.url_expanders = {
            'getlinkinfo': 'http://www.getlinkinfo.com/info?link={}',
            'checkshorturl': 'https://checkshorturl.com/expand.php?u={}',
            'expandurl': 'https://www.expandurl.net/expand?url={}'
        }
        
        self.pokemon_go_services = {
            'pogotrainer': 'https://pogotrainer.club/',
            'gamepress': 'https://gamepress.gg/pokemongo/trainer-codes-list',
            'pokelytics': 'https://pokelytics.com/',
            'openstreetmap': 'https://www.openstreetmap.org/'
        }
    
    def expand_url(self, url: str) -> OSINTResult:
        """Expand shortened URLs using multiple services"""
        start_time = time.time()
        results = {}
        
        for service_name, url_template in self.url_expanders.items():
            try:
                expand_url = url_template.format(quote(url))
                response = self._make_request(expand_url)
                
                if response.status_code == 200:
                    expanded = self._parse_expansion_response(service_name, response, url)
                    results[service_name] = {
                        'status': 'success',
                        'expanded_url': expanded,
                        'service_url': expand_url
                    }
                else:
                    results[service_name] = {
                        'status': 'failed',
                        'status_code': response.status_code,
                        'service_url': expand_url
                    }
                    
            except Exception as e:
                results[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return OSINTResult(
            service=self.name,
            query=url,
            query_type='url_expansion',
            success=any(r.get('status') == 'success' for r in results.values()),
            data={'expansion_results': results},
            response_time=time.time() - start_time
        )
    
    def pokemon_go_search(self, query: str, query_type: str = 'trainer_code') -> OSINTResult:
        """Pokemon Go trainer/username search"""
        start_time = time.time()
        
        search_urls = {}
        
        if query_type == 'trainer_code':
            search_urls.update({
                'google': f'https://www.google.com/search?q="{query}"',
                'reddit': f'https://www.reddit.com/r/PokemonGoFriends/search/?q={query}&restrict_sr=1',
                'twitter': f'https://twitter.com/search?q={query}'
            })
        
        elif query_type == 'username':
            search_urls.update({
                'friendhuntr': f'https://api.friendhuntr.com/distribute/payload-search?username={query}',
                'silph': f'https://sil.ph/{query}',
                'pokebattler': f'https://www.pokebattler.com/profiles?search={query}&page=0#searchResult',
                'trainerdex': f'https://www.trainerdex.co.uk/u/{query}'
            })
        
        return OSINTResult(
            service=self.name,
            query=query,
            query_type=f'pokemon_go_{query_type}',
            success=True,
            data={
                'search_urls': search_urls,
                'pokemon_go_resources': self.pokemon_go_services
            },
            response_time=time.time() - start_time
        )
    
    def _parse_expansion_response(self, service: str, response, original_url: str) -> Optional[str]:
        """Parse URL expansion response"""
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if service == 'getlinkinfo':
            # Look for expanded URL
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href.startswith('http') and href != original_url and href != response.url:
                    return href
        
        elif service == 'checkshorturl':
            text = soup.get_text()
            # Look for URLs in the text
            url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
            urls = re.findall(url_pattern, text)
            for url in urls:
                if url != original_url:
                    return url
        
        elif service == 'expandurl':
            # Look for result section
            for div in soup.find_all('div'):
                if 'result' in div.get('class', []):
                    link = div.find('a')
                    if link:
                        return link.get('href')
        
        return None
    
    def search(self, query: str, query_type: str = 'url_expansion') -> OSINTResult:
        """Route to appropriate utility service"""
        if query_type == 'url_expansion':
            return self.expand_url(query)
        elif query_type.startswith('pokemon_go'):
            pogo_type = query_type.replace('pokemon_go_', '')
            return self.pokemon_go_search(query, pogo_type)
        else:
            return OSINTResult(
                service=self.name,
                query=query,
                query_type=query_type,
                success=False,
                error="Unsupported query type",
                data={}
            )

class SULTANFramework(BaseOSINTService):
    """Enhanced SULTAN framework for bulk username checking"""
    
    def __init__(self):
        super().__init__("SULTAN", rate_limit=0.5)
        self.platforms = self._load_default_platforms()
    
    def _load_default_platforms(self) -> List[Dict[str, str]]:
        """Load default platform configurations"""
        return [
            {
                'name': 'GitHub',
                'url_template': 'https://github.com/{}',
                'error_indicators': ['Not Found', '404'],
                'success_indicators': ['contributions']
            },
            {
                'name': 'Twitter',
                'url_template': 'https://twitter.com/{}',
                'error_indicators': ['does not exist', 'suspended'],
                'success_indicators': ['tweets', 'followers']
            },
            {
                'name': 'Instagram',
                'url_template': 'https://instagram.com/{}',
                'error_indicators': ['not found', 'error'],
                'success_indicators': ['posts', 'followers']
            },
            {
                'name': 'Reddit',
                'url_template': 'https://reddit.com/user/{}',
                'error_indicators': ['not found', 'suspended'],
                'success_indicators': ['karma', 'trophy']
            },
            {
                'name': 'YouTube',
                'url_template': 'https://youtube.com/@{}',
                'error_indicators': ['not found', '404'],
                'success_indicators': ['subscribers', 'videos']
            }
        ]
    
    def bulk_username_check(self, username: str) -> OSINTResult:
        """Check username across multiple platforms"""
        start_time = time.time()
        results = {}
        found_count = 0
        
        for platform in self.platforms:
            try:
                url = platform['url_template'].format(username)
                response = self._make_request(url)
                
                # Analyze response
                exists = self._analyze_platform_response(response, platform)
                
                results[platform['name']] = {
                    'url': url,
                    'status_code': response.status_code,
                    'exists': exists,
                    'accessible': response.status_code == 200
                }
                
                if exists:
                    found_count += 1
                    
            except Exception as e:
                results[platform['name']] = {
                    'url': platform['url_template'].format(username),
                    'error': str(e),
                    'exists': False,
                    'accessible': False
                }
        
        return OSINTResult(
            service=self.name,
            query=username,
            query_type='bulk_username_check',
            success=found_count > 0,
            data={
                'platforms_checked': len(self.platforms),
                'profiles_found': found_count,
                'results': results,
                'summary': f"Found {found_count} profiles for username '{username}'"
            },
            response_time=time.time() - start_time
        )
    
    def _analyze_platform_response(self, response, platform: Dict[str, str]) -> bool:
        """Analyze if username exists on platform"""
        if response.status_code == 404:
            return False
        elif response.status_code == 403:
            # Access denied could mean profile exists but is private
            return True
        elif response.status_code != 200:
            return False
        
        text_lower = response.text.lower()
        
        # Check for error indicators first
        for error_indicator in platform['error_indicators']:
            if error_indicator.lower() in text_lower:
                return False
        
        # For platforms like Twitter/Instagram, a 200 response usually means profile exists
        # unless we find specific error indicators
        if platform['name'] in ['Twitter', 'Instagram', 'YouTube']:
            # These platforms return 200 even for non-existent users sometimes
            # but redirect or show error messages
            if any(error in text_lower for error in ['not found', 'does not exist', 'suspended', 'account suspended']):
                return False
            return True
        
        # Check for success indicators
        for success_indicator in platform['success_indicators']:
            if success_indicator.lower() in text_lower:
                return True
        
        # If no clear indicators but got 200, likely exists
        return True
    
    def search(self, query: str, query_type: str = 'bulk_username_check') -> OSINTResult:
        """SULTAN search interface"""
        if query_type == 'bulk_username_check':
            return self.bulk_username_check(query)
        else:
            return OSINTResult(
                service=self.name,
                query=query,
                query_type=query_type,
                success=False,
                error="Unsupported query type for SULTAN",
                data={}
            )

class ComprehensiveOSINTEngine:
    """Meta search engine orchestrating all OSINT services"""
    
    def __init__(self):
        self.social_media = SocialMediaOSINT()
        self.image_analysis = ImageAnalysisOSINT()
        self.utilities = UtilityOSINT()
        self.sultan = SULTANFramework()
        self.results_cache = {}
        
    def search_comprehensive(self, query: str, search_types: List[str] = None) -> List[OSINTResult]:
        """Perform comprehensive OSINT search"""
        if search_types is None:
            search_types = self._determine_search_types(query)
        
        results = []
        
        for search_type in search_types:
            try:
                if search_type.startswith('social_'):
                    platform_results = self.social_media.search(query, search_type)
                    if isinstance(platform_results, list):
                        results.extend(platform_results)
                    else:
                        results.append(platform_results)
                
                elif search_type == 'image_analysis':
                    results.append(self.image_analysis.search(query))
                
                elif search_type.startswith('utility_'):
                    util_type = search_type.replace('utility_', '')
                    results.append(self.utilities.search(query, util_type))
                
                elif search_type == 'bulk_username':
                    results.append(self.sultan.search(query))
                    
            except Exception as e:
                logger.error(f"Error in search type {search_type}: {e}")
                
        return results
    
    def _determine_search_types(self, query: str) -> List[str]:
        """Intelligently determine what types of searches to perform"""
        search_types = []
        
        # URL detection
        if self._is_url(query):
            if self._is_shortened_url(query):
                search_types.append('utility_url_expansion')
            if self._is_image_url(query):
                search_types.append('image_analysis')
        
        # Username/handle detection
        elif self._looks_like_username(query):
            search_types.extend([
                'social_username',
                'bulk_username'
            ])
        
        # Email detection
        elif '@' in query and '.' in query:
            search_types.append('social_linkedin_email_lookup')
        
        # Trainer code detection (Pokemon Go)
        elif re.match(r'^\d{12}$', query):
            search_types.append('utility_pokemon_go_trainer_code')
        
        # Default to comprehensive search
        if not search_types:
            search_types = ['social_username', 'bulk_username']
        
        return search_types
    
    def _is_url(self, query: str) -> bool:
        """Check if query is a URL"""
        return query.startswith(('http://', 'https://')) or any(domain in query for domain in ['.com', '.org', '.net'])
    
    def _is_shortened_url(self, query: str) -> bool:
        """Check if query is a shortened URL"""
        short_domains = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly']
        return any(domain in query for domain in short_domains)
    
    def _is_image_url(self, query: str) -> bool:
        """Check if query is an image URL"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        return any(query.lower().endswith(ext) for ext in image_extensions)
    
    def _looks_like_username(self, query: str) -> bool:
        """Check if query looks like a username"""
        return (
            len(query) >= 2 and 
            len(query) <= 30 and 
            re.match(r'^[a-zA-Z0-9_.-]+$', query) and
            not self._is_url(query)
        )
    
    def generate_comprehensive_report(self, results: List[OSINTResult], output_format: str = 'dict') -> Union[Dict, str]:
        """Generate comprehensive report from all results"""
        report = {
            'search_summary': {
                'total_searches': len(results),
                'successful_searches': sum(1 for r in results if r.success),
                'failed_searches': sum(1 for r in results if not r.success),
                'total_response_time': sum(r.response_time for r in results),
                'timestamp': datetime.now().isoformat()
            },
            'results_by_service': {},
            'key_findings': [],
            'urls_discovered': [],
            'profiles_found': []
        }
        
        # Organize results by service
        for result in results:
            service = result.service
            if service not in report['results_by_service']:
                report['results_by_service'][service] = []
            
            report['results_by_service'][service].append({
                'query': result.query,
                'query_type': result.query_type,
                'success': result.success,
                'data': result.data,
                'error': result.error,
                'response_time': result.response_time
            })
            
            # Extract key findings
            if result.success and result.data:
                self._extract_key_findings(result, report)
        
        if output_format == 'json':
            return json.dumps(report, indent=2, default=str)
        elif output_format == 'csv':
            return self._generate_csv_report(results)
        else:
            return report
    
    def _extract_key_findings(self, result: OSINTResult, report: Dict):
        """Extract key findings from successful results"""
        data = result.data
        
        # Extract URLs
        for key, value in data.items():
            if isinstance(value, str) and self._is_url(value):
                report['urls_discovered'].append({
                    'url': value,
                    'source': result.service,
                    'context': key
                })
        
        # Extract profile information
        if result.service in ['SocialMediaOSINT', 'SULTAN'] and result.success:
            if 'profile_exists' in str(data) or 'profiles_found' in str(data):
                report['profiles_found'].append({
                    'service': result.service,
                    'query': result.query,
                    'data': data
                })
        
        # Add to key findings
        if result.success:
            report['key_findings'].append({
                'service': result.service,
                'query': result.query,
                'type': result.query_type,
                'finding': f"Successfully found data on {result.service}",
                'details': data
            })
    
    def _generate_csv_report(self, results: List[OSINTResult]) -> str:
        """Generate CSV format report"""
        data_rows = []
        
        for result in results:
            data_rows.append({
                'Service': result.service,
                'Query': result.query,
                'Query_Type': result.query_type,
                'Success': result.success,
                'Response_Time': result.response_time,
                'Status_Code': result.status_code,
                'Error': result.error or '',
                'Data_Keys': ', '.join(result.data.keys()) if result.data else '',
                'Timestamp': result.timestamp
            })
        
        if data_rows:
            df = pd.DataFrame(data_rows)
            return df.to_csv(index=False)
        else:
            return "No results to export"
    
    def save_results(self, results: List[OSINTResult], filename: str = None):
        """Save results to file"""
        if filename is None:
            filename = f"osint_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.generate_comprehensive_report(results, 'dict')
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filename}")
        return filename

def main():
    """Main function for testing the comprehensive OSINT framework"""
    print("=== Comprehensive OSINT Framework Test ===\n")
    
    engine = ComprehensiveOSINTEngine()
    
    # Test cases
    test_queries = [
        ("testuser", ["social_username"]),
        ("https://bit.ly/example", ["utility_url_expansion"]),
        ("https://example.com/image.jpg", ["image_analysis"]),
        ("123456789012", ["utility_pokemon_go_trainer_code"])
    ]
    
    all_results = []
    
    for query, search_types in test_queries:
        print(f"Testing query: '{query}' with types: {search_types}")
        
        results = engine.search_comprehensive(query, search_types)
        all_results.extend(results)
        
        for result in results:
            print(f"  {result.service}: {'✓' if result.success else '✗'} ({result.response_time:.2f}s)")
        print()
    
    # Generate comprehensive report
    print("=== Comprehensive Report ===")
    report = engine.generate_comprehensive_report(all_results)
    
    print(f"Total searches: {report['search_summary']['total_searches']}")
    print(f"Successful: {report['search_summary']['successful_searches']}")
    print(f"Failed: {report['search_summary']['failed_searches']}")
    print(f"Total time: {report['search_summary']['total_response_time']:.2f}s")
    
    # Save results
    filename = engine.save_results(all_results)
    print(f"\nDetailed results saved to: {filename}")

if __name__ == "__main__":
    main()
