#!/usr/bin/env python
"""
Command-line interface for App Crawler.
Provides easy access to crawl, replay, and manage paths.
"""

import argparse
import sys
import os
from dotenv import load_dotenv

from app_crawler import AppCrawler, CrawlerDatabase


def human_intervention_callback(question: str, current_state: dict) -> str:
    """Default callback for human intervention."""
    print("\n" + "="*60)
    print("🤖 AI NEEDS HELP!")
    print("="*60)
    print(f"\nQuestion: {question}")
    print(f"\nCurrent Screen: {current_state.get('activity', 'Unknown')}")
    print(f"Available Elements: {len(current_state.get('elements', []))}")
    
    # Show top elements
    for i, elem in enumerate(current_state.get('elements', [])[:5], 1):
        print(f"  {i}. {elem.get('type')}: {elem.get('text')}")
    
    print("\n" + "="*60)
    response = input("\nYour response (or 'stop' to end crawl): ")
    return response


def crawl_command(args):
    """Execute crawl command."""
    print(f"Starting crawl for {args.app_package}...")
    
    crawler = AppCrawler(
        platform=args.platform,
        app_package=args.app_package,
        app_activity=args.app_activity,
        bundle_id=args.bundle_id,
        device_name=args.device,
        appium_server=args.appium_server,
        ai_provider=args.ai_provider,
        db_path=args.db_path
    )
    
    try:
        crawler.start_crawl(
            name=args.name,
            description=args.description or "",
            max_steps=args.max_steps,
            human_callback=human_intervention_callback if not args.no_human else None
        )
        
        print(f"\n✅ Crawl completed successfully!")
        print(f"Path ID: {crawler.current_path_id}")
        print(f"Steps: {crawler.step_count}")
        print(f"\nView results at: http://localhost:5000")
        
    except KeyboardInterrupt:
        print("\n⚠️  Crawl interrupted by user")
        crawler.disconnect()
    except Exception as e:
        print(f"\n❌ Error during crawl: {e}")
        crawler.disconnect()
        sys.exit(1)


def replay_command(args):
    """Execute replay command."""
    print(f"Replaying path: {args.path_id}...")
    
    crawler = AppCrawler(
        platform=args.platform,
        app_package=args.app_package,
        app_activity=args.app_activity,
        bundle_id=args.bundle_id,
        device_name=args.device,
        appium_server=args.appium_server,
        db_path=args.db_path
    )
    
    try:
        crawler.replay_path(args.path_id, delay=args.delay)
        print(f"\n✅ Replay completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during replay: {e}")
        crawler.disconnect()
        sys.exit(1)


def list_command(args):
    """List all paths."""
    db = CrawlerDatabase(args.db_path)
    paths = db.get_all_paths()
    
    if not paths:
        print("No paths found. Run a crawl first!")
        return
    
    print(f"\n📱 Found {len(paths)} path(s):\n")
    print(f"{'Path ID':<20} {'Name':<30} {'Platform':<10} {'Steps':<8} {'Created'}")
    print("-" * 90)
    
    for path in paths:
        created = path['created_at'][:10] if path['created_at'] else 'N/A'
        print(f"{path['path_id']:<20} {path['name']:<30} {path['platform']:<10} "
              f"{path['step_count']:<8} {created}")


def info_command(args):
    """Show details about a specific path."""
    db = CrawlerDatabase(args.db_path)
    path = db.get_path_by_id(args.path_id)
    
    if not path:
        print(f"❌ Path not found: {args.path_id}")
        sys.exit(1)
    
    steps = db.get_path_steps(args.path_id)
    interventions = db.get_human_interventions(args.path_id)
    
    print(f"\n📱 Path Information")
    print("=" * 60)
    print(f"Path ID: {path['path_id']}")
    print(f"Name: {path['name']}")
    print(f"Platform: {path['platform']}")
    print(f"App Package: {path['app_package']}")
    print(f"Description: {path['description'] or 'N/A'}")
    print(f"Created: {path['created_at']}")
    print(f"Updated: {path['updated_at']}")
    print(f"Steps: {len(steps)}")
    print(f"Human Interventions: {len(interventions)}")
    
    if args.show_steps and steps:
        print(f"\n📋 Steps:")
        for step in steps[:10]:  # Show first 10
            print(f"  {step['step_number']}. {step['action_type']} - {step['element_selector'][:50]}")
        if len(steps) > 10:
            print(f"  ... and {len(steps) - 10} more steps")


def web_command(args):
    """Start the web portal."""
    print("Starting web portal...")
    print("Open your browser to: http://localhost:5000")
    
    # Import and run Flask app
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from web_portal.app import app
    app.run(debug=args.debug, host='0.0.0.0', port=args.port)


def main():
    """Main CLI entry point."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="App Crawler - AI-powered mobile app testing",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global arguments
    parser.add_argument('--db-path', default='crawler_paths.db',
                       help='Path to SQLite database')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Start a new crawl')
    crawl_parser.add_argument('--platform', required=True, choices=['android', 'ios'],
                             help='Platform to crawl')
    crawl_parser.add_argument('--app-package', required=True,
                             help='App package name or bundle ID')
    crawl_parser.add_argument('--app-activity',
                             help='Main activity (Android only)')
    crawl_parser.add_argument('--bundle-id',
                             help='Bundle ID (iOS only)')
    crawl_parser.add_argument('--device', default='emulator-5554',
                             help='Device name')
    crawl_parser.add_argument('--appium-server', default='http://localhost:4723',
                             help='Appium server URL')
    crawl_parser.add_argument('--ai-provider', default='openai',
                             choices=['openai', 'anthropic', 'qwen'],
                             help='AI provider')
    crawl_parser.add_argument('--name', required=True,
                             help='Name for this crawl')
    crawl_parser.add_argument('--description',
                             help='Description of crawl goal')
    crawl_parser.add_argument('--max-steps', type=int, default=50,
                             help='Maximum number of steps')
    crawl_parser.add_argument('--no-human', action='store_true',
                             help='Disable human intervention')
    
    # Replay command
    replay_parser = subparsers.add_parser('replay', help='Replay a saved path')
    replay_parser.add_argument('path_id', help='Path ID to replay')
    replay_parser.add_argument('--platform', required=True, choices=['android', 'ios'])
    replay_parser.add_argument('--app-package', required=True)
    replay_parser.add_argument('--app-activity')
    replay_parser.add_argument('--bundle-id')
    replay_parser.add_argument('--device', default='emulator-5554')
    replay_parser.add_argument('--appium-server', default='http://localhost:4723')
    replay_parser.add_argument('--delay', type=float, default=2.0,
                              help='Delay between steps (seconds)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all paths')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show path details')
    info_parser.add_argument('path_id', help='Path ID')
    info_parser.add_argument('--show-steps', action='store_true',
                            help='Show step details')
    
    # Web command
    web_parser = subparsers.add_parser('web', help='Start web portal')
    web_parser.add_argument('--port', type=int, default=5000,
                           help='Port to run on')
    web_parser.add_argument('--debug', action='store_true',
                           help='Run in debug mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command
    if args.command == 'crawl':
        crawl_command(args)
    elif args.command == 'replay':
        replay_command(args)
    elif args.command == 'list':
        list_command(args)
    elif args.command == 'info':
        info_command(args)
    elif args.command == 'web':
        web_command(args)


if __name__ == '__main__':
    main()
