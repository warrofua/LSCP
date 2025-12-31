#!/bin/bash
while true; do
    clear
    echo "=== LSCP Batch Scan Monitor ==="
    echo "Time: $(date '+%H:%M:%S')"
    echo ""
    sqlite3 /Users/joshuafarrow/Projects/LSCP/data/lscp.db "SELECT COUNT(*) as 'Scans Completed:' FROM scans"
    sqlite3 /Users/joshuafarrow/Projects/LSCP/data/lscp.db "SELECT COUNT(*) as 'Relationships Found:' FROM relationships"
    echo ""
    echo "Latest scanned concepts:"
    sqlite3 /Users/joshuafarrow/Projects/LSCP/data/lscp.db "SELECT c.name, datetime(s.scan_timestamp, 'localtime') FROM scans s JOIN concepts c ON s.anchor_concept_id = c.id ORDER BY s.scan_timestamp DESC LIMIT 3"
    echo ""
    echo "Log file size: $(wc -l < /Users/joshuafarrow/Projects/LSCP/batch_scan.log) lines"
    echo ""
    echo "Press Ctrl+C to stop monitoring"
    sleep 30
done
