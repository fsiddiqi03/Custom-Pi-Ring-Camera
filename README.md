# 🎥 Custom Pi Ring Camera

A full-featured smart security camera system built with Raspberry Pi 5, featuring AI-powered person detection, cloud storage, and real-time monitoring with email notifications.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Raspberry Pi 5                              │
│  ┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐    │
│  │  Pi Camera 3 │───▶│  Flask Server   │───▶│  Detection Loop │    │
│  │  (640x480)   │    │  (Port 8080)    │    │  (15s interval)  │    │
│  └──────────────┘    └─────────────────┘    └──────────────────┘    │
│                              │                         │            │
└──────────────────────────────┼─────────────────────────┼────────────┘
                               │                         │
                        ┌──────▼─────────────────────────▼──────┐
                        │         AWS Cloud Services            │
                        │                                       │
                        │  ┌──────────────────────────────────┐ │
                        │  │  Lambda (Person Detection)       │ │
                        │  │  • YOLO Model (Docker/ECR)       │ │
                        │  │  • HTTP Endpoint                 │ │
                        │  │  • Returns: person_detected bool │ │
                        │  └──────────────────────────────────┘ │
                        │                │                      │
                        │                ▼                      │
                        │  ┌──────────────────────────────────┐ │
                        │  │  S3 Bucket (Video Storage)       │ │
                        │  │  • MP4 files (H.264)             │ │
                        │  │  • Presigned URLs                │ │
                        │  │  • Filename: YYYYMMDD_HHMMSS.mp4 │ │
                        │  └──────────────────────────────────┘ │
                        │                │                      │
                        │                ▼                      │
                        │  ┌──────────────────────────────────┐ │
                        │  │  Lambda (Email Notifications)    │ │
                        │  │  • Triggered by S3 upload        │ │
                        │  │  • AWS SES integration           │ │
                        │  └──────────────────────────────────┘ │
                        └───────────────────────────────────────┘
                                         │
                                         ▼
                        ┌────────────────────────────────┐
                        │  User Browser (Web Interface)  │
                        │  • Live camera feed            │
                        │  • Alert history with filters  │
                        │  • Video playback modal        │
                        └────────────────────────────────┘
```

## ✨ Features

### 🎯 Core Functionality
- **Real-time Video Streaming**: Live camera feed accessible via web browser
- **AI Person Detection**: Automatic person detection using YOLO model every 15 seconds
- **Smart Recording**: Automatically records 5-second clips when a person is detected
- **Cloud Storage**: All recordings stored in AWS S3 with organized naming convention
- **Email Alerts**:  Email notifications via AWS SES when motion is detected
- **Video Playback**: Browse and watch past alerts through the web interface
- **Filtering**: Filter alerts by date and time range

### 🛡️ Features
- **Cooldown System**: 2-minute cooldown between recordings to prevent spam
- **Optimized Detection**: Reduced check intervals (15s) to minimize CPU usage
- **Browser-Compatible Videos**: H.264/MP4 format for universal playback
- **Presigned URLs**: Secure, temporary access to video files (1-hour expiration)

### 🎨 Web Interface
- **Two-Page Layout**:
  - **Live Feed**: Real-time camera stream with monitoring status
  - **Alerts**: Grid view of all recorded events with thumbnails

## 🔧 Prerequisites

### Hardware
- **Raspberry Pi 5** (4GB+ RAM recommended)
- **Pi Camera Module 3** (or compatible camera)

### Software & Cloud Services
- **Raspberry Pi OS** (64-bit, Bookworm or later)
- **Python 3.11+**
- **AWS**:
  - Lambda
  - S3 bucket
  - ECR repository ( YOLO Docker image)
  - SES configured for email notifications
  - IAM user with appropriate permissions


