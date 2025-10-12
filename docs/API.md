# SpectraX API Documentation

This document provides a complete reference for the SpectraX REST API. Use these endpoints to build custom clients, integrate with other systems, or query surveillance data programmatically.

## Base URL

The API runs on the detection server port (default: 8080):

```
http://localhost:8080
```

For remote access, replace `localhost` with your server's IP address.

## Authentication

Currently, the API does not require authentication. For production deployments, consider placing the API behind a reverse proxy with authentication (e.g., nginx with basic auth).

## Response Format

All API responses are in JSON format unless otherwise specified.

**Success Response:**
```json
{
  "status": "success",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description"
}
```

---

## Endpoints

### System Status

#### GET /status

Get current system status and statistics.

**Response:**
```json
{
  "status": "running",
  "cameras": {
    "video/front-door": {
      "fps": 25.3,
      "detections": 42,
      "last_detection": "2025-10-12T19:05:30Z",
      "objects": {
        "person": 15,
        "car": 3
      }
    }
  },
  "uptime_seconds": 3600,
  "model": "yolov8n.pt",
  "tracking_enabled": true
}
```

**Example:**
```bash
curl http://localhost:8080/status
```

---

### Camera Paths

#### GET /paths

List all available camera stream paths.

**Response:**
```json
{
  "paths": [
    "video/front-door",
    "video/backyard",
    "video/garage"
  ]
}
```

**Example:**
```bash
curl http://localhost:8080/paths
```

---

### Video Streaming

#### GET /video/stream

Get MJPEG video stream with AI detection overlays.

**Query Parameters:**
- `path` (optional): Camera path to stream. If omitted, streams the first camera.

**Response:** MJPEG video stream (multipart/x-mixed-replace)

**Example:**
```bash
# Stream first camera
curl http://localhost:8080/video/stream

# Stream specific camera
curl http://localhost:8080/video/stream?path=video/front-door
```

**HTML Integration:**
```html
<img src="http://localhost:8080/video/stream?path=video/front-door" />
```

---

### Recordings

#### GET /api/recordings

List all recordings with metadata.

**Query Parameters:**
- `limit` (optional): Maximum number of recordings to return (default: 100)
- `offset` (optional): Number of recordings to skip (default: 0)
- `object` (optional): Filter by detected object class (e.g., "person", "car")
- `tracker_id` (optional): Filter by tracker ID

**Response:**
```json
{
  "total": 150,
  "limit": 100,
  "offset": 0,
  "recordings": [
    {
      "id": 42,
      "timestamp": "2025-10-12T19:05:30Z",
      "stream_path": "video/front-door",
      "duration_seconds": 15.2,
      "file_path": "recording_20251012_190530_front-door.mp4",
      "file_size_bytes": 2048576,
      "objects_detected": [
        {
          "class": "person",
          "confidence": 0.95,
          "tracker_id": 42,
          "count": 3
        },
        {
          "class": "car",
          "confidence": 0.87,
          "tracker_id": 15,
          "count": 1
        }
      ],
      "tracker_ids": [42, 15],
      "max_confidence": 0.95
    }
  ]
}
```

**Examples:**
```bash
# Get all recordings
curl http://localhost:8080/api/recordings

# Get recordings with pagination
curl "http://localhost:8080/api/recordings?limit=10&offset=20"

# Filter by object class
curl "http://localhost:8080/api/recordings?object=person"

# Filter by tracker ID
curl "http://localhost:8080/api/recordings?tracker_id=42"
```

---

#### GET /api/recordings/{id}

Get details for a specific recording.

**Path Parameters:**
- `id`: Recording ID

**Response:**
```json
{
  "id": 42,
  "timestamp": "2025-10-12T19:05:30Z",
  "stream_path": "video/front-door",
  "duration_seconds": 15.2,
  "file_path": "recording_20251012_190530_front-door.mp4",
  "file_size_bytes": 2048576,
  "objects_detected": [
    {
      "class": "person",
      "confidence": 0.95,
      "tracker_id": 42,
      "bbox": [100, 200, 300, 400],
      "timestamp": "2025-10-12T19:05:32Z"
    }
  ],
  "tracker_ids": [42, 15],
  "max_confidence": 0.95
}
```

**Example:**
```bash
curl http://localhost:8080/api/recordings/42
```

---

#### GET /api/recordings/stats

Get recording statistics and analytics.

**Response:**
```json
{
  "total_recordings": 150,
  "total_duration_seconds": 2280,
  "total_size_bytes": 307200000,
  "total_size_gb": 0.29,
  "oldest_recording": "2025-10-01T10:00:00Z",
  "newest_recording": "2025-10-12T19:05:30Z",
  "objects": {
    "person": 450,
    "car": 120,
    "dog": 15
  },
  "trackers": {
    "total_unique_ids": 87,
    "most_frequent": [
      {"tracker_id": 42, "appearances": 12},
      {"tracker_id": 15, "appearances": 8}
    ]
  },
  "by_camera": {
    "video/front-door": {
      "count": 80,
      "duration_seconds": 1200
    },
    "video/backyard": {
      "count": 70,
      "duration_seconds": 1080
    }
  }
}
```

**Example:**
```bash
curl http://localhost:8080/api/recordings/stats
```

---

#### GET /recordings/{filename}

Download a recording file.

**Path Parameters:**
- `filename`: Recording filename (from `/api/recordings` response)

**Response:** MP4 video file (video/mp4)

**Example:**
```bash
# Download recording
curl -O http://localhost:8080/recordings/recording_20251012_190530_front-door.mp4

# Stream in VLC
vlc http://localhost:8080/recordings/recording_20251012_190530_front-door.mp4
```

---

## Client Examples

### Python Client

```python
import requests
import json

class SpectraXClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    def get_status(self):
        """Get system status"""
        response = requests.get(f"{self.base_url}/status")
        return response.json()
    
    def get_recordings(self, limit=100, offset=0, object_class=None, tracker_id=None):
        """List recordings with optional filters"""
        params = {"limit": limit, "offset": offset}
        if object_class:
            params["object"] = object_class
        if tracker_id:
            params["tracker_id"] = tracker_id
        
        response = requests.get(f"{self.base_url}/api/recordings", params=params)
        return response.json()
    
    def get_recording(self, recording_id):
        """Get specific recording details"""
        response = requests.get(f"{self.base_url}/api/recordings/{recording_id}")
        return response.json()
    
    def download_recording(self, filename, output_path):
        """Download recording file"""
        response = requests.get(f"{self.base_url}/recordings/{filename}", stream=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    def get_stats(self):
        """Get recording statistics"""
        response = requests.get(f"{self.base_url}/api/recordings/stats")
        return response.json()

# Usage
client = SpectraXClient()

# Get system status
status = client.get_status()
print(f"System uptime: {status['uptime_seconds']}s")

# Find recordings with people
recordings = client.get_recordings(object_class="person", limit=10)
print(f"Found {recordings['total']} recordings with people")

# Download a recording
if recordings['recordings']:
    first = recordings['recordings'][0]
    client.download_recording(first['file_path'], "output.mp4")
```

---

### JavaScript Client

```javascript
class SpectraXClient {
  constructor(baseUrl = 'http://localhost:8080') {
    this.baseUrl = baseUrl;
  }

  async getStatus() {
    const response = await fetch(`${this.baseUrl}/status`);
    return response.json();
  }

  async getRecordings(options = {}) {
    const params = new URLSearchParams({
      limit: options.limit || 100,
      offset: options.offset || 0,
      ...(options.object && { object: options.object }),
      ...(options.tracker_id && { tracker_id: options.tracker_id })
    });
    
    const response = await fetch(`${this.baseUrl}/api/recordings?${params}`);
    return response.json();
  }

  async getRecording(id) {
    const response = await fetch(`${this.baseUrl}/api/recordings/${id}`);
    return response.json();
  }

  async getStats() {
    const response = await fetch(`${this.baseUrl}/api/recordings/stats`);
    return response.json();
  }

  getStreamUrl(cameraPath = null) {
    const params = cameraPath ? `?path=${cameraPath}` : '';
    return `${this.baseUrl}/video/stream${params}`;
  }

  getRecordingUrl(filename) {
    return `${this.baseUrl}/recordings/${filename}`;
  }
}

// Usage
const client = new SpectraXClient();

// Get system status
const status = await client.getStatus();
console.log(`System uptime: ${status.uptime_seconds}s`);

// Find recordings with tracker ID 42
const recordings = await client.getRecordings({ tracker_id: 42 });
console.log(`Found ${recordings.total} recordings`);

// Display video stream
const img = document.createElement('img');
img.src = client.getStreamUrl('video/front-door');
document.body.appendChild(img);
```

---

### cURL Examples

```bash
# Get system status
curl http://localhost:8080/status | jq

# List recent recordings
curl http://localhost:8080/api/recordings?limit=10 | jq

# Find recordings with people
curl "http://localhost:8080/api/recordings?object=person" | jq

# Find recordings with tracker ID 42
curl "http://localhost:8080/api/recordings?tracker_id=42" | jq

# Get recording statistics
curl http://localhost:8080/api/recordings/stats | jq

# Download a recording
curl -O http://localhost:8080/recordings/recording_20251012_190530_front-door.mp4

# Stream video to file
curl "http://localhost:8080/video/stream?path=video/front-door" > stream.mjpeg
```

---

## WebSocket Support (Future)

WebSocket support for real-time detection events is planned for a future release. This will enable:

- Real-time detection notifications
- Live tracker updates
- System event streaming

Stay tuned for updates in the [Development Roadmap](roadmap_summary.md).

---

## Rate Limiting

Currently, there are no rate limits on API endpoints. For production deployments, consider implementing rate limiting at the reverse proxy level.

---

## CORS

Cross-Origin Resource Sharing (CORS) is enabled by default for all origins. To restrict access, modify the FastAPI CORS middleware configuration in `videofeed/visualizer.py`.

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---

## Database Schema

For direct database access, recordings are stored in SQLite with the following schema:

```sql
CREATE TABLE recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    stream_path TEXT NOT NULL,
    duration_seconds REAL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    objects_detected TEXT,  -- JSON array
    tracker_ids TEXT,       -- JSON array
    max_confidence REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timestamp ON recordings(timestamp);
CREATE INDEX idx_stream_path ON recordings(stream_path);
CREATE INDEX idx_tracker_ids ON recordings(tracker_ids);
```

**Database Location:** `~/video-feed-recordings/recordings.db`

**Direct Query Example:**
```bash
sqlite3 ~/video-feed-recordings/recordings.db "SELECT * FROM recordings WHERE tracker_ids LIKE '%42%' ORDER BY timestamp DESC LIMIT 10;"
```

---

## Support

For issues or questions:
- Check the [main README](../README.md) for troubleshooting
- Review the [Architecture Guide](ARCHITECTURE.md) for implementation details
- Open an issue on GitHub
