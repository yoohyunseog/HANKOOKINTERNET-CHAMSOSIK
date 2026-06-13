#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NB Video Analyzer RSS Feed Generator
Generates RSS feed for dlvr.it integration
"""

import json
import os
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

def load_latest_analysis():
    """Load the latest keyword analysis JSON file"""
    analysis_dir = Path(__file__).parent / "analysis_results"
    latest_file = analysis_dir / "latest_keyword_analysis.json"
    
    if not latest_file.exists():
        print(f"Error: {latest_file} not found")
        return None
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_rss_item(category_data, keyword_data, base_url):
    """Create RSS item for a keyword"""
    item = ET.Element('item')
    
    # Title
    title = ET.SubElement(item, 'title')
    keyword = keyword_data.get('keyword', 'Unknown')
    category = category_data.get('category', 'Unknown')
    title.text = f"[{category}] {keyword}"
    
    # Link
    link = ET.SubElement(item, 'link')
    video_id = keyword_data.get('videos', [{}])[0].get('videoId', '') if keyword_data.get('videos') else ''
    if video_id:
        link.text = f"https://www.youtube.com/watch?v={video_id}"
    else:
        link.text = f"{base_url}/NBVideoAnalyzer/"
    
    # Description
    desc = ET.SubElement(item, 'description')
    view_counts = keyword_data.get('viewAnalysis', {}).get('viewCounts', [])
    view_count = view_counts[0] if view_counts else 0
    videos = keyword_data.get('videos', [])
    channel = videos[0].get('channelTitle', 'Unknown') if videos else 'Unknown'
    desc.text = f"조회수: {view_count:,}회 | 채널: {channel} | 카테고리: {category}"
    
    # PubDate
    pub_date = ET.SubElement(item, 'pubDate')
    analyzed_at = keyword_data.get('dateAnalysis', {}).get('newestUploadDate', '')
    if analyzed_at:
        try:
            dt = datetime.fromisoformat(analyzed_at.replace('+00:00', '+00:00'))
            pub_date.text = dt.strftime('%a, %d %b %Y %H:%M:%S %z')
        except:
            pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900')
    else:
        pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900')
    
    # GUID
    guid = ET.SubElement(item, 'guid')
    guid.set('isPermaLink', 'false')
    guid.text = f"nbva-{category}-{keyword}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return item

def generate_rss_feed(analysis_data, output_path):
    """Generate RSS feed from analysis data"""
    base_url = "https://www.xn--9l4b4xi9r.com"
    
    # Create RSS root element
    rss = ET.Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    
    # Create channel
    channel = ET.SubElement(rss, 'channel')
    
    # Channel metadata
    title = ET.SubElement(channel, 'title')
    title.text = "NB Video Analyzer - 키워드 분석 피드"
    
    link = ET.SubElement(channel, 'link')
    link.text = f"{base_url}/NBVideoAnalyzer/"
    
    description = ET.SubElement(channel, 'description')
    description.text = "참소식.com NB Video Analyzer의 최신 키워드 분석 결과를 실시간으로 제공합니다."
    
    language = ET.SubElement(channel, 'language')
    language.text = "ko-KR"
    
    last_build_date = ET.SubElement(channel, 'lastBuildDate')
    last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900')
    
    generator = ET.SubElement(channel, 'generator')
    generator.text = "NB Video Analyzer RSS Generator v1.0"
    
    # Add atom:link for self-reference
    atom_link = ET.SubElement(channel, 'atom:link')
    atom_link.set('href', f"{base_url}/NBVideoAnalyzer/rss.xml")
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # Process categories and keywords
    categories = analysis_data.get('categories', [])
    total_items = 0
    max_items = 50  # Limit RSS items
    
    for category_data in categories:
        if total_items >= max_items:
            break
        
        category = category_data.get('category', 'Unknown')
        keywords = category_data.get('keywords', [])
        
        # Add top keywords from each category
        for keyword_data in keywords[:5]:  # Top 5 keywords per category
            if total_items >= max_items:
                break
            
            item = create_rss_item(category_data, keyword_data, base_url)
            channel.append(item)
            total_items += 1
    
    # Generate XML string
    xml_str = ET.tostring(rss, encoding='unicode')
    
    # Pretty print
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(pretty_xml)
    
    print(f"RSS feed generated: {output_path}")
    print(f"Total items: {total_items}")
    
    return total_items

def main():
    """Main function"""
    print("=" * 60)
    print("NB Video Analyzer RSS Feed Generator")
    print("=" * 60)
    print()
    
    # Load analysis data
    print("Loading latest analysis data...")
    analysis_data = load_latest_analysis()
    
    if not analysis_data:
        print("Error: Failed to load analysis data")
        return
    
    print(f"Analysis timestamp: {analysis_data.get('analyzedAt', 'Unknown')}")
    print(f"Total keywords: {analysis_data.get('totalKeywordCount', 0)}")
    print(f"Categories: {analysis_data.get('categoryCount', 0)}")
    print()
    
    # Generate RSS feed
    output_path = Path(__file__).parent / "rss.xml"
    print(f"Generating RSS feed to: {output_path}")
    
    total_items = generate_rss_feed(analysis_data, output_path)
    
    print()
    print("=" * 60)
    print("RSS Feed Generation Complete!")
    print("=" * 60)
    print(f"Output: {output_path}")
    print(f"Items: {total_items}")
    print(f"URL: https://www.xn--9l4b4xi9r.com/NBVideoAnalyzer/rss.xml")
    print()

if __name__ == "__main__":
    main()