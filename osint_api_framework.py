#!/usr/bin/env python3
"""
OSINT API Framework
Comprehensive API wrapper for OSINT services identified in bookmarklet collection
"""

import requests
import time
import json
import re
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OSINTResult:
    """Standard result format for all OSINT queries"""
    service: str
    query: str
    query_type: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: Optional[str] = None

class BaseOSINTService(ABC):
    """Base class for all OSINT services"""
    
    def __init__(self, name: str, base_url: str, rate_limit: float = 1.0):
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.last_request = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()
    
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """Make HTTP request with rate limiting"""
        self._rate_limit()
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            logger.info(f"{self.name}: {method} {url} -> {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"{self.name}: Request failed for {url}: {e}")
            raise
    
    @abstractmethod
    def search(self, query: str, query_type: str = 'default') -> OSINTResult:
        """Abstract method for performing searches"""
        pass

class URLExpanderService(BaseOSINTService):
    """URL expansion services"""
    
    def __init__(self):
        super().__init__("URLExpander", "")
        self.services = {
            'getlinkinfo': 'http://www.getlinkinfo.com/info?link={}',
            'checkshorturl': 'https://checkshorturl.com/expand.php?u={}',
            'expandurl': 'https://www.expandurl.net/expand?url={}'
        }
    
    def search(self, query: str, query_type: str = 'expand') -> OSINTResult:
        """Expand shortened URLs using multiple services"""
        results = {}
        
        for service_name, url_template in self.services.items():
            try:
                url = url_template.format(quote(query))
                response = self._make_request(url)
                
                if response.status_code == 200:
                    # Parse the response based on service
                    expanded_url = self._parse_expansion_response(service_name, response)
                    results[service_name] = {
                        'expanded_url': expanded_url,
                        'status': 'success'
                    }
                else:
                    results[service_name] = {
                        'status': 'failed',
                        'status_code': response.status_code
                    }
            except Exception as e:
                results[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return OSINTResult(
            service=self.name,
            query=query,
            query_type=query_type,
            success=any(r.get('status') == 'success' for r in results.values()),
            data={'results': results}
        )
    
    def _parse_expansion_response(self, service: str, response: requests.Response) -> Optional[str]:
        """Parse expansion response based on service"""
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if service == 'getlinkinfo':
            # Look for expanded URL in the response
            links = soup.find_all('a')
            for link in links:
                href = link.get('href', '')
                if href.startswith('http') and href != response.url:
                    return href
        
        elif service == 'checkshorturl':
            # Look for the expanded URL
            text = soup.get_text()
            url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
            urls = re.findall(url_pattern, text)
            return urls[0] if urls else None
        
        elif service == 'expandurl':
            # Parse ExpandURL response
            result_div = soup.find('div', class_='result')
            if result_div:
                link = result_div.find('a')
                if link:
                    return link.get('href')
        
        return None

class ImageAnalysisService(BaseOSINTService):
    """Reverse image search services"""
    
    def __init__(self):
        super().__init__("ImageAnalysis", "")
        self.services = {
            'google': 'https://www.google.com/searchbyimage?&image_url={}',
            'yandex': 'https://yandex.com/images/search?source=collections&rpt=imageview&url={}',
            'tineye': 'https://www.tineye.com/search/?url={}',
            'bing': 'https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIIRP&sbisrc=UrlPaste&q=imgurl:{}',
            'baidu': 'https://graph.baidu.com/details?isfromtusoupc=1tn=pc&carousel=0&image={}'
        }
    
    def search(self, query: str, query_type: str = 'reverse_image') -> OSINTResult:
        """Perform reverse image search across multiple services"""
        results = {}
        
        for service_name, url_template in self.services.items():
            try:
                url = url_template.format(quote(query))
                response = self._make_request(url)
                
                results[service_name] = {
                    'search_url': url,
                    'status_code': response.status_code,
                    'accessible': response.status_code == 200,
                    'results_found': self._analyze_image_results(service_name, response) if response.status_code == 200 else False
                }
                
            except Exception as e:
                results[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return OSINTResult(
            service=self.name,
            query=query,
            query_type=query_type,
            success=any(r.get('accessible') for r in results.values()),
            data={'services': results}
        )
    
    def _analyze_image_results(self, service: str, response: requests.Response) -> bool:
        """Analyze if image search returned results"""
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Basic heuristics for detecting results
        if service == 'google':
            return len(soup.find_all('div', class_='g')) > 0
        elif service == 'yandex':
            return 'serp-item' in response.text
        elif service == 'tineye':
            return 'match' in response.text.lower()
        elif service == 'bing':
            return 'imgres' in response.text
        elif service == 'baidu':
            return 'graph' in response.text
        
        return False

class SocialMediaService(BaseOSINTService):
    """Social media platform services"""
    
    def __init__(self):
        super().__init__("SocialMedia", "")
    
    def search_gab(self, username: str) -> OSINTResult:
        """Search Gab for username"""
        try:
            url = f"https://gab.com/{username}"
            response = self._make_request(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                profile_data = self._extract_gab_profile(soup)
                
                return OSINTResult(
                    service="Gab",
                    query=username,
                    query_type="username",
                    success=True,
                    data=profile_data
                )
            else:
                return OSINTResult(
                    service="Gab",
                    query=username,
                    query_type="username",
                    success=False,
                    error=f"Profile not found (HTTP {response.status_code})",
                    data={}
                )
                
        except Exception as e:
            return OSINTResult(
                service="Gab",
                query=username,
                query_type="username",
                success=False,
                error=str(e),
                data={}
            )
    
    def search_tiktok(self, username: str) -> OSINTResult:
        """Search TikTok for username"""
        try:
            url = f"https://www.tiktok.com/@{username}"
            response = self._make_request(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                profile_data = self._extract_tiktok_profile(soup)
                
                return OSINTResult(
                    service="TikTok",
                    query=username,
                    query_type="username",
                    success=True,
                    data=profile_data
                )
            else:
                return OSINTResult(
                    service="TikTok",
                    query=username,
                    query_type="username",
                    success=False,
                    error=f"Profile not found (HTTP {response.status_code})",
                    data={}
                )
                
        except Exception as e:
            return OSINTResult(
                service="TikTok",
                query=username,
                query_type="username",
                success=False,
                error=str(e),
                data={}
            )
    
    def _extract_gab_profile(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract profile data from Gab page"""
        data = {}
        
        # Try to extract avatar using the bookmarklet logic
        html_content = str(soup)
        if 'parallax"' in html_content:
            try:
                avatar_section = html_content.split('parallax"')[1]
                avatar_url = avatar_section.split('&quot;')[1]
                data['avatar_url'] = avatar_url
            except IndexError:
                pass
        
        # Extract other profile information
        data['profile_exists'] = True
        data['url'] = soup.find('link', {'rel': 'canonical'})['href'] if soup.find('link', {'rel': 'canonical'}) else None
        
        return data
    
    def _extract_tiktok_profile(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract profile data from TikTok page"""
        data = {}
        
        # Try to extract profile photo using bookmarklet logic
        html_content = str(soup)
        if 'background-image:url(' in html_content:
            try:
                photo_section = html_content.split('background-image:url(')[1]
                photo_url = photo_section.split(')')[0].strip('"\'')
                data['profile_photo'] = photo_url
            except IndexError:
                pass
        
        data['profile_exists'] = True
        return data

    def search(self, query: str, query_type: str = 'username') -> OSINTResult:
        """Generic search method - routes to specific platform methods"""
        if query_type == 'gab_username':
            return self.search_gab(query)
        elif query_type == 'tiktok_username':
            return self.search_tiktok(query)
        else:
            return OSINTResult(
                service=self.name,
                query=query,
                query_type=query_type,
                success=False,
                error="Unsupported query type",
                data={}
            )

class OSINTSearchEngine:
    """Meta search engine that orchestrates all OSINT services"""
    
    def __init__(self):
        self.url_expander = URLExpanderService()
        self.image_analysis = ImageAnalysisService()
        self.social_media = SocialMediaService()
        self.results_cache = {}
    
    def search_all(self, query: str, query_types: List[str] = None) -> List[OSINTResult]:
        """Perform comprehensive search across all available services"""
        if query_types is None:
            query_types = ['url_expand', 'reverse_image', 'username']
        
        results = []
        
        for query_type in query_types:
            if query_type == 'url_expand' and self._looks_like_url(query):
                results.append(self.url_expander.search(query))
            elif query_type == 'reverse_image' and self._looks_like_image_url(query):
                results.append(self.image_analysis.search(query))
            elif query_type == 'username':
                results.append(self.social_media.search_gab(query))
                results.append(self.social_media.search_tiktok(query))
        
        return results
    
    def _looks_like_url(self, query: str) -> bool:
        """Check if query looks like a URL"""
        return query.startswith(('http://', 'https://')) or 'bit.ly' in query or 'tinyurl' in query
    
    def _looks_like_image_url(self, query: str) -> bool:
        """Check if query looks like an image URL"""
        return query.startswith(('http://', 'https://')) and any(query.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
    
    def generate_report(self, results: List[OSINTResult]) -> Dict[str, Any]:
        """Generate comprehensive report from search results"""
        report = {
            'summary': {
                'total_searches': len(results),
                'successful_searches': sum(1 for r in results if r.success),
                'failed_searches': sum(1 for r in results if not r.success)
            },
            'results_by_service': {},
            'findings': []
        }
        
        for result in results:
            if result.service not in report['results_by_service']:
                report['results_by_service'][result.service] = []
            report['results_by_service'][result.service].append(result)
            
            if result.success and result.data:
                report['findings'].append({
                    'service': result.service,
                    'query': result.query,
                    'type': result.query_type,
                    'data': result.data
                })
        
        return report

if __name__ == "__main__":
    # Test the framework
    engine = OSINTSearchEngine()
    
    # Test URL expansion
    print("Testing URL expansion...")
    url_result = engine.url_expander.search("https://bit.ly/example")
    print(f"URL Expansion Result: {url_result.success}")
    
    # Test image analysis
    print("\nTesting image analysis...")
    image_result = engine.image_analysis.search("https://example.com/image.jpg")
    print(f"Image Analysis Result: {image_result.success}")
    
    # Test social media
    print("\nTesting social media...")
    social_result = engine.social_media.search_gab("testuser")
    print(f"Social Media Result: {social_result.success}")
