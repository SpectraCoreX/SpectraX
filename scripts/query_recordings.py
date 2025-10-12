#!/usr/bin/env python3
"""Query recordings database with tracking information."""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse


def get_db_path():
    """Get the default database path."""
    return Path.home() / "video-feed-recordings" / "recordings.db"


def connect_db(db_path=None):
    """Connect to the recordings database."""
    if db_path is None:
        db_path = get_db_path()
    
    if not Path(db_path).exists():
        print(f"❌ Database not found at: {db_path}")
        sys.exit(1)
    
    return sqlite3.connect(db_path)


def list_all_recordings(conn, limit=10):
    """List recent recordings with tracker information."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, stream_name, duration, confidence, 
               tracker_ids, objects_detected
        FROM recordings
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    print(f"\n📹 Recent Recordings (last {limit}):")
    print("=" * 100)
    
    for row in cursor.fetchall():
        rec_id, timestamp, stream, duration, conf, tracker_ids, objects = row
        
        # Parse tracker IDs
        tracker_list = json.loads(tracker_ids) if tracker_ids else []
        
        # Parse objects
        obj_list = json.loads(objects) if objects else []
        obj_classes = [obj['class'] for obj in obj_list]
        
        print(f"\n🎬 Recording #{rec_id}")
        print(f"   Time: {timestamp}")
        print(f"   Stream: {stream}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Confidence: {conf:.2f}")
        print(f"   Objects: {', '.join(set(obj_classes))}")
        print(f"   Tracker IDs: {tracker_list}")


def find_by_tracker_id(conn, tracker_id):
    """Find all recordings containing a specific tracker ID."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, stream_name, duration, tracker_ids, objects_detected
        FROM recordings
        WHERE tracker_ids LIKE ?
        ORDER BY timestamp DESC
    ''', (f'%{tracker_id}%',))
    
    results = cursor.fetchall()
    
    if not results:
        print(f"\n❌ No recordings found with tracker ID #{tracker_id}")
        return
    
    print(f"\n🔍 Found {len(results)} recording(s) with tracker ID #{tracker_id}:")
    print("=" * 100)
    
    for row in results:
        rec_id, timestamp, stream, duration, tracker_ids, objects = row
        
        # Parse tracker IDs
        tracker_list = json.loads(tracker_ids) if tracker_ids else []
        
        # Parse objects to find this specific tracker
        obj_list = json.loads(objects) if objects else []
        matching_objects = [
            obj for obj in obj_list 
            if obj.get('tracker_id') == tracker_id
        ]
        
        print(f"\n🎬 Recording #{rec_id}")
        print(f"   Time: {timestamp}")
        print(f"   Stream: {stream}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   All Tracker IDs: {tracker_list}")
        
        if matching_objects:
            obj = matching_objects[0]
            print(f"   Tracker #{tracker_id}: {obj['class']} (confidence: {obj['confidence']:.2f})")


def find_by_object_class(conn, object_class):
    """Find all recordings containing a specific object class."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, stream_name, duration, tracker_ids, objects_detected
        FROM recordings
        WHERE objects_detected LIKE ?
        ORDER BY timestamp DESC
    ''', (f'%"{object_class}"%',))
    
    results = cursor.fetchall()
    
    if not results:
        print(f"\n❌ No recordings found with object class '{object_class}'")
        return
    
    print(f"\n🔍 Found {len(results)} recording(s) with '{object_class}':")
    print("=" * 100)
    
    for row in results:
        rec_id, timestamp, stream, duration, tracker_ids, objects = row
        
        # Parse tracker IDs
        tracker_list = json.loads(tracker_ids) if tracker_ids else []
        
        # Parse objects
        obj_list = json.loads(objects) if objects else []
        matching_objects = [
            obj for obj in obj_list 
            if obj['class'] == object_class
        ]
        
        print(f"\n🎬 Recording #{rec_id}")
        print(f"   Time: {timestamp}")
        print(f"   Stream: {stream}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Tracker IDs: {tracker_list}")
        print(f"   {object_class.capitalize()} instances: {len(matching_objects)}")
        
        for obj in matching_objects:
            tid = obj.get('tracker_id', 'N/A')
            print(f"      - Tracker #{tid}: confidence {obj['confidence']:.2f}")


def get_tracker_statistics(conn):
    """Get statistics about tracker IDs across all recordings."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tracker_ids, objects_detected
        FROM recordings
        WHERE tracker_ids IS NOT NULL AND tracker_ids != '[]'
    ''')
    
    tracker_counts = {}
    tracker_objects = {}
    
    for row in cursor.fetchall():
        tracker_ids, objects = row
        
        # Parse tracker IDs
        tracker_list = json.loads(tracker_ids) if tracker_ids else []
        
        # Parse objects
        obj_list = json.loads(objects) if objects else []
        
        for tracker_id in tracker_list:
            tracker_counts[tracker_id] = tracker_counts.get(tracker_id, 0) + 1
            
            # Find object class for this tracker
            for obj in obj_list:
                if obj.get('tracker_id') == tracker_id:
                    if tracker_id not in tracker_objects:
                        tracker_objects[tracker_id] = []
                    tracker_objects[tracker_id].append(obj['class'])
    
    if not tracker_counts:
        print("\n❌ No tracking data found in recordings")
        return
    
    print("\n📊 Tracker Statistics:")
    print("=" * 100)
    print(f"\nTotal unique trackers: {len(tracker_counts)}")
    print("\nMost frequently recorded trackers:")
    
    # Sort by count
    sorted_trackers = sorted(tracker_counts.items(), key=lambda x: x[1], reverse=True)
    
    for tracker_id, count in sorted_trackers[:10]:
        objects = tracker_objects.get(tracker_id, [])
        most_common = max(set(objects), key=objects.count) if objects else "unknown"
        print(f"   Tracker #{tracker_id}: {count} recording(s) - mostly '{most_common}'")


def main():
    parser = argparse.ArgumentParser(
        description="Query SpectraX recordings database with tracking information"
    )
    parser.add_argument(
        '--db', 
        help='Path to database file (default: ~/video-feed-recordings/recordings.db)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recent recordings')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of recordings to show')
    
    # Find by tracker ID
    tracker_parser = subparsers.add_parser('tracker', help='Find recordings by tracker ID')
    tracker_parser.add_argument('id', type=int, help='Tracker ID to search for')
    
    # Find by object class
    object_parser = subparsers.add_parser('object', help='Find recordings by object class')
    object_parser.add_argument('class_name', help='Object class to search for (e.g., person, car)')
    
    # Statistics
    subparsers.add_parser('stats', help='Show tracker statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Connect to database
    conn = connect_db(args.db)
    
    try:
        if args.command == 'list':
            list_all_recordings(conn, args.limit)
        elif args.command == 'tracker':
            find_by_tracker_id(conn, args.id)
        elif args.command == 'object':
            find_by_object_class(conn, args.class_name)
        elif args.command == 'stats':
            get_tracker_statistics(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
