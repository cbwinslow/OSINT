#!/usr/bin/env python3
"""
OSINT CLI Tool
Command-line interface for the comprehensive OSINT framework
"""

import argparse
import json
import sys
from typing import List, Dict, Any
from comprehensive_osint_api import ComprehensiveOSINTEngine
import os

def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive OSINT Search Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Username search across all platforms
  python osint_cli.py -q testuser -t username

  # Image reverse search
  python osint_cli.py -q "https://example.com/image.jpg" -t image

  # URL expansion
  python osint_cli.py -q "https://bit.ly/example" -t url

  # Pokemon Go trainer code search
  python osint_cli.py -q "123456789012" -t pokemon

  # Social media specific search
  python osint_cli.py -q testuser -t social -p gab,tiktok

  # Save results to file
  python osint_cli.py -q testuser -t username -o results.json

  # Bulk username search
  python osint_cli.py -q testuser -t bulk

  # Auto-detect search type
  python osint_cli.py -q testuser --auto
        """
    )
    
    parser.add_argument('-q', '--query', required=True,
                       help='Search query (username, URL, image URL, etc.)')
    
    parser.add_argument('-t', '--type',
                       choices=['username', 'image', 'url', 'pokemon', 'social', 'bulk', 'auto'],
                       default='auto',
                       help='Type of search to perform')
    
    parser.add_argument('-p', '--platforms',
                       help='Comma-separated list of platforms for social search (gab,tiktok,linkedin,reddit,tumblr)')
    
    parser.add_argument('-o', '--output',
                       help='Output file for results (JSON format)')
    
    parser.add_argument('--format',
                       choices=['json', 'csv', 'text'],
                       default='text',
                       help='Output format')
    
    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Verbose output')
    
    parser.add_argument('--config',
                       help='Configuration file path')
    
    parser.add_argument('--timeout',
                       type=int,
                       default=30,
                       help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Initialize engine
    engine = ComprehensiveOSINTEngine()
    
    # Determine search types
    if args.type == 'auto':
        search_types = engine._determine_search_types(args.query)
        if args.verbose:
            print(f"Auto-detected search types: {search_types}")
    else:
        search_types = get_search_types(args.type, args.platforms)
    
    if args.verbose:
        print(f"Performing search for: '{args.query}'")
        print(f"Search types: {search_types}")
        print("-" * 50)
    
    # Perform search
    try:
        results = engine.search_comprehensive(args.query, search_types)
        
        # Display results
        if args.format == 'text':
            display_text_results(results, args.verbose)
        elif args.format == 'json':
            report = engine.generate_comprehensive_report(results, 'json')
            print(report)
        elif args.format == 'csv':
            report = engine.generate_comprehensive_report(results, 'csv')
            print(report)
        
        # Save to file if requested
        if args.output:
            filename = engine.save_results(results, args.output)
            print(f"\nResults saved to: {filename}")
        
        # Summary
        successful = sum(1 for r in results if r.success)
        total = len(results)
        print(f"\nSummary: {successful}/{total} searches successful")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def get_search_types(search_type: str, platforms: str = None) -> List[str]:
    """Convert CLI search type to internal search types"""
    if search_type == 'username':
        return ['social_username', 'bulk_username']
    elif search_type == 'image':
        return ['image_analysis']
    elif search_type == 'url':
        return ['utility_url_expansion']
    elif search_type == 'pokemon':
        return ['utility_pokemon_go_trainer_code']
    elif search_type == 'social':
        if platforms:
            return [f'social_{platform}_username' for platform in platforms.split(',')]
        else:
            return ['social_username']
    elif search_type == 'bulk':
        return ['bulk_username']
    else:
        return ['social_username']

def display_text_results(results: List, verbose: bool = False):
    """Display results in human-readable text format"""
    print("\n=== OSINT Search Results ===\n")
    
    for result in results:
        status = "✓" if result.success else "✗"
        print(f"{status} {result.service} - {result.query_type}")
        
        if result.success and result.data:
            if verbose:
                print(f"   Response time: {result.response_time:.2f}s")
                
            # Display key findings
            data = result.data
            
            if result.service == 'SocialMediaOSINT':
                display_social_media_findings(data)
            elif result.service == 'ImageAnalysisOSINT':
                display_image_analysis_findings(data)
            elif result.service == 'UtilityOSINT':
                display_utility_findings(data, result.query_type)
            elif result.service == 'SULTAN':
                display_sultan_findings(data)
            
        elif not result.success:
            print(f"   Error: {result.error}")
        
        print()

def display_social_media_findings(data: Dict[str, Any]):
    """Display social media search findings"""
    if 'profile_exists' in data and data['profile_exists']:
        print("   Profile found!")
        
        if 'avatar_url' in data:
            print(f"   Avatar: {data['avatar_url']}")
        if 'header_image_url' in data:
            print(f"   Header: {data['header_image_url']}")
        if 'canonical_url' in data:
            print(f"   URL: {data['canonical_url']}")
        if 'video_url' in data:
            print(f"   Video: {data['video_url']}")

def display_image_analysis_findings(data: Dict[str, Any]):
    """Display image analysis findings"""
    if 'reverse_search_results' in data:
        results = data['reverse_search_results']
        accessible_count = data.get('total_accessible_services', 0)
        
        print(f"   Accessible services: {accessible_count}/5")
        
        for service, info in results.items():
            if isinstance(info, dict) and info.get('accessible'):
                has_results = info.get('has_results', False)
                result_indicator = "📊" if has_results else "📭"
                print(f"   {result_indicator} {info.get('service_name', service)}: {info['search_url']}")

def display_utility_findings(data: Dict[str, Any], query_type: str):
    """Display utility service findings"""
    if query_type == 'url_expansion' and 'expansion_results' in data:
        results = data['expansion_results']
        successful = [name for name, info in results.items() if info.get('status') == 'success']
        
        if successful:
            print(f"   Successfully expanded via: {', '.join(successful)}")
            for service in successful:
                expanded_url = results[service].get('expanded_url')
                if expanded_url:
                    print(f"   {service}: {expanded_url}")
        else:
            print("   No successful expansions")
    
    elif 'pokemon_go' in query_type and 'search_urls' in data:
        print("   Pokemon Go search URLs generated:")
        for platform, url in data['search_urls'].items():
            print(f"   {platform}: {url}")

def display_sultan_findings(data: Dict[str, Any]):
    """Display SULTAN bulk search findings"""
    if 'profiles_found' in data:
        found_count = data['profiles_found']
        total_checked = data.get('platforms_checked', 0)
        
        print(f"   Found profiles: {found_count}/{total_checked} platforms")
        
        if 'results' in data:
            for platform, info in data['results'].items():
                if info.get('exists'):
                    print(f"   ✓ {platform}: {info['url']}")

if __name__ == "__main__":
    main()
