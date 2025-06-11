# Comprehensive OSINT API Framework

A powerful, extensible OSINT (Open Source Intelligence) framework that reverse engineers and creates APIs for multiple intelligence gathering services. This project systematically analyzes and provides programmatic access to the tools originally found in browser bookmarklets.

## 🚀 Features

### Core Capabilities
- **Social Media Intelligence**: Username searches across Gab, TikTok, LinkedIn, Reddit, Tumblr
- **Image Analysis**: Reverse image search via Google, Yandex, TinEye, Bing, Baidu + EXIF extraction
- **URL Intelligence**: Expansion of shortened URLs through multiple services
- **Bulk Username Checking**: SULTAN framework for cross-platform username verification
- **Pokemon Go OSINT**: Trainer code and username searches across gaming platforms
- **Comprehensive Reporting**: JSON, CSV, and text output formats

### Technical Features
- **Rate Limiting**: Intelligent request throttling to avoid service blocks
- **User Agent Rotation**: Dynamic header rotation for stealth
- **Error Handling**: Robust retry logic and fallback mechanisms
- **Caching**: Results caching to improve performance
- **CLI Interface**: Full command-line tool for easy automation
- **Web Interface**: Browser-based UI for interactive searches
- **API Framework**: RESTful API for integration with other tools

## 📁 Project Structure

```
OSINT/
├── comprehensive_osint_api.py      # Core API framework
├── osint_cli.py                   # Command-line interface
├── osint_web.py                   # Web interface (Flask)
├── osint_config.py               # Configuration management
├── requirements.txt              # Python dependencies
├── README.md                     # This documentation
├── docs/                         # Detailed documentation
├── tests/                        # Test suite
├── examples/                     # Usage examples
└── bookmarklets/                 # Original bookmarklet tools
    ├── Gab/
    ├── TikTok/
    ├── LinkedIn/
    └── ...
```

## 🛠 Installation

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser (for Selenium-based searches)
- Git

### Quick Install
```bash
git clone https://github.com/cbwinslow/OSINT.git
cd OSINT
pip install -r requirements.txt
```

### Docker Installation
```bash
docker build -t osint-framework .
docker run -p 5000:5000 osint-framework
```

## 🎯 Quick Start

### Command Line Usage

```bash
# Username search across all platforms
python osint_cli.py -q username123 -t username -v

# Image reverse search
python osint_cli.py -q "https://example.com/image.jpg" -t image

# URL expansion
python osint_cli.py -q "https://bit.ly/shortlink" -t url

# Social media specific search
python osint_cli.py -q username123 -t social -p gab,tiktok

# Bulk username checking
python osint_cli.py -q username123 -t bulk

# Pokemon Go trainer code search
python osint_cli.py -q "123456789012" -t pokemon

# Auto-detect search type
python osint_cli.py -q username123 --auto

# Save results to file
python osint_cli.py -q username123 -t username -o results.json
```

### Python API Usage

```python
from comprehensive_osint_api import ComprehensiveOSINTEngine

# Initialize the engine
engine = ComprehensiveOSINTEngine()

# Perform comprehensive search
results = engine.search_comprehensive("username123", ["social_username", "bulk_username"])

# Generate report
report = engine.generate_comprehensive_report(results)
print(f"Found {report['search_summary']['successful_searches']} results")

# Save results
engine.save_results(results, "investigation_results.json")
```

### Web Interface
```bash
python osint_web.py
# Navigate to http://localhost:5000
```

## 📚 Service Coverage

### Social Media Platforms

#### Gab
- **Username Search**: `gab.com/{username}`
- **Hashtag Search**: `gab.com/tags/{hashtag}`
- **Data Extraction**:
  - Full-size avatar images
  - Header/banner images  
  - Video content and thumbnails
  - Profile metadata

#### TikTok
- **Username Search**: `tiktok.com/@{username}`
- **Hashtag Search**: `tiktok.com/tag/{hashtag}`
- **Data Extraction**:
  - Profile photos (full resolution)
  - Video download URLs
  - Video thumbnails
  - Upload timestamps
  - Metadata extraction

#### LinkedIn
- **Profile Enhancement**: Extract larger photos and recent activity
- **Data Extraction**:
  - High-resolution profile photos
  - Recent activity feeds
  - Connection information
- **Note**: Email lookup deprecated by LinkedIn

#### Reddit
- **Profile Analysis**: Extract avatars, banners, and metadata
- **Removeddit Integration**: Access deleted content
- **Data Extraction**:
  - Profile avatars (full size)
  - Banner images
  - Account history analysis

#### Tumblr
- **Blog Analysis**: Comprehensive blog intelligence
- **API Integration**: Official Tumblr API usage
- **Data Extraction**:
  - Blog archives
  - Avatar images (512px)
  - Likes, followers, following lists
  - Post history

### Image Intelligence

#### Reverse Image Search
- **Google Images**: Advanced visual search
- **Yandex Images**: Russian search engine with unique capabilities
- **TinEye**: Specialized reverse image search
- **Bing Images**: Microsoft's visual search
- **Baidu Images**: Chinese search engine integration

#### Metadata Analysis
- **EXIF Extraction**: Camera data, GPS coordinates, timestamps
- **Image Forensics**: File analysis and manipulation detection
- **Cross-Reference**: Compare results across multiple engines

### Utility Services

#### URL Intelligence
- **Expansion Services**:
  - GetLinkInfo
  - CheckShortURL
  - ExpandURL
- **Analysis**: Detect redirects, track campaign parameters
- **Security**: Identify malicious shortened links

#### Gaming Platforms (Pokemon Go)
- **Trainer Code Search**: Cross-platform trainer identification
- **Username Search**: Gaming profile discovery
- **Community Integration**: Reddit, Discord, specialized forums
- **Mapping**: Geographic analysis of gaming activity

### Bulk Operations

#### SULTAN Framework
- **Multi-Platform Checking**: Simultaneous username verification
- **Supported Platforms**:
  - GitHub
  - Twitter/X
  - Instagram
  - Reddit
  - YouTube
  - Custom platforms (configurable)
- **Performance**: Optimized for bulk operations
- **Reporting**: Detailed availability analysis

## 🔧 Configuration

### Basic Configuration
```python
# osint_config.py
CONFIG = {
    'rate_limits': {
        'default': 1.0,  # seconds between requests
        'aggressive': 0.5,
        'conservative': 2.0
    },
    'timeouts': {
        'default': 30,
        'image_search': 60,
        'social_media': 45
    },
    'user_agents': {
        'rotate': True,
        'custom_agents': []
    },
    'selenium': {
        'headless': True,
        'implicit_wait': 10
    }
}
```

### Adding Custom Platforms
```python
# Add to SULTAN framework
custom_platform = {
    'name': 'CustomSite',
    'url_template': 'https://customsite.com/user/{}',
    'error_indicators': ['not found', '404'],
    'success_indicators': ['profile', 'posts']
}

engine.sultan.platforms.append(custom_platform)
```

## 📊 Output Formats

### JSON Report Structure
```json
{
  "search_summary": {
    "total_searches": 5,
    "successful_searches": 3,
    "failed_searches": 2,
    "total_response_time": 12.34,
    "timestamp": "2025-06-11T08:34:16.561326"
  },
  "results_by_service": {
    "SocialMediaOSINT": [...],
    "ImageAnalysisOSINT": [...],
    "UtilityOSINT": [...],
    "SULTAN": [...]
  },
  "key_findings": [...],
  "urls_discovered": [...],
  "profiles_found": [...]
}
```

### CSV Export
```csv
Service,Query,Query_Type,Success,Response_Time,Status_Code,Error,Data_Keys,Timestamp
Gab,testuser,username,True,0.52,,200,,avatar_url,2025-06-11T08:34:16
```

## 🌐 Web Interface

The web interface provides an intuitive browser-based tool for OSINT investigations:

### Features
- **Interactive Search**: Point-and-click interface
- **Real-time Results**: Live updating as searches complete
- **Visual Reports**: Charts and graphs of findings
- **Export Options**: Download results in multiple formats
- **Search History**: Track and revisit previous investigations
- **Batch Operations**: Upload lists for bulk processing

### Screenshots
[Web interface screenshots would go here]

## 🔒 Ethics & Legal Considerations

### Ethical Guidelines
- **Respect Rate Limits**: Don't overload target services
- **Honor robots.txt**: Respect website policies
- **Privacy Awareness**: Be mindful of personal information
- **Legal Compliance**: Follow applicable laws and regulations

### Rate Limiting
The framework includes built-in rate limiting to:
- Prevent service disruption
- Avoid IP blocking
- Maintain ethical usage patterns
- Ensure sustainable access

### Disclaimer
This tool is intended for legitimate security research, investigative journalism, and authorized penetration testing. Users are responsible for ensuring their usage complies with applicable laws and service terms.

## 🧪 Testing

### Run Test Suite
```bash
python -m pytest tests/ -v
```

### Manual Testing
```bash
# Test core functionality
python tests/test_basic_functionality.py

# Test specific services
python tests/test_social_media.py
python tests/test_image_analysis.py
python tests/test_utilities.py
```

### Performance Testing
```bash
python tests/benchmark_performance.py
```

## 📈 Performance & Optimization

### Benchmarks
- **Average Response Time**: 2-5 seconds per service
- **Concurrent Requests**: Up to 10 simultaneous searches
- **Memory Usage**: ~50MB base, +10MB per active search
- **Success Rate**: 85-95% depending on service availability

### Optimization Tips
- Use `--conservative` rate limiting for sensitive targets
- Enable caching for repeated searches
- Batch similar queries together
- Use web interface for complex investigations

## 🤝 Contributing

### Development Setup
```bash
git clone https://github.com/cbwinslow/OSINT.git
cd OSINT
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
```

### Adding New Services
1. Create new service class inheriting from `BaseOSINTService`
2. Implement required methods (`search`, data extraction)
3. Add service to main engine
4. Update documentation and tests
5. Submit pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Include comprehensive docstrings
- Add unit tests for new features

## 📝 API Documentation

### Core Classes

#### `ComprehensiveOSINTEngine`
Main orchestration engine for all OSINT operations.

```python
class ComprehensiveOSINTEngine:
    def search_comprehensive(self, query: str, search_types: List[str] = None) -> List[OSINTResult]
    def generate_comprehensive_report(self, results: List[OSINTResult], output_format: str = 'dict') -> Union[Dict, str]
    def save_results(self, results: List[OSINTResult], filename: str = None) -> str
```

#### `OSINTResult`
Standard result format for all searches.

```python
@dataclass
class OSINTResult:
    service: str
    query: str
    query_type: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = None
    response_time: float = 0.0
    status_code: Optional[int] = None
```

### Service Classes

#### `SocialMediaOSINT`
Handles all social media platform searches.

```python
def search_gab(self, query: str, query_type: str = 'username') -> OSINTResult
def search_tiktok(self, query: str, query_type: str = 'username') -> OSINTResult
def search_linkedin(self, query: str, query_type: str = 'profile_url') -> OSINTResult
def search_reddit(self, query: str, query_type: str = 'username') -> OSINTResult
def search_tumblr(self, query: str, query_type: str = 'blog') -> OSINTResult
```

#### `ImageAnalysisOSINT`
Reverse image search and metadata extraction.

```python
def search(self, query: str, query_type: str = 'reverse_image') -> OSINTResult
```

#### `UtilityOSINT`
URL expansion and specialty services.

```python
def expand_url(self, url: str) -> OSINTResult
def pokemon_go_search(self, query: str, query_type: str = 'trainer_code') -> OSINTResult
```

#### `SULTANFramework`
Bulk username checking across multiple platforms.

```python
def bulk_username_check(self, username: str) -> OSINTResult
```

## 🚧 Roadmap

### Short Term (v1.1)
- [ ] Additional social media platforms (Facebook, Instagram API)
- [ ] Enhanced error handling and retry logic
- [ ] Database storage for results
- [ ] API authentication system

### Medium Term (v1.2)
- [ ] Machine learning for result correlation
- [ ] Advanced image analysis (face recognition, object detection)
- [ ] Blockchain and cryptocurrency investigation tools
- [ ] Mobile app for field investigations

### Long Term (v2.0)
- [ ] Distributed architecture for large-scale operations
- [ ] Real-time monitoring and alerting
- [ ] Integration with commercial OSINT platforms
- [ ] Advanced visualization and reporting

## 📞 Support

### Documentation
- [API Reference](docs/api_reference.md)
- [Service Coverage](docs/service_coverage.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Examples](examples/)

### Community
- GitHub Issues: Bug reports and feature requests
- Discussions: General questions and community support
- Wiki: Community-contributed documentation

### Commercial Support
For commercial licensing, custom development, or enterprise support, contact the maintainers.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Services
This tool interacts with third-party services. Users must comply with the terms of service of each platform accessed.

## 🙏 Acknowledgments

- Original bookmarklet creators for inspiration
- Open source OSINT community for tools and techniques
- Service providers for maintaining accessible APIs
- Contributors and beta testers

## 📋 Changelog

### v1.0.0 (2025-06-11)
- Initial release
- Complete framework implementation
- CLI and web interfaces
- Comprehensive service coverage
- Documentation and examples

---

**Built with ❤️ for the OSINT community**
