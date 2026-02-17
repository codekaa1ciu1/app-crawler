# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-02-17

### Added - MVP Release

#### Core Features
- **AI-Powered Crawler**: Intelligent mobile app crawling using GPT-4 or Claude
  - Automatic DOM analysis and element extraction
  - Smart action decision making
  - Input value suggestions for text fields
  - Human-in-the-loop for uncertain situations

#### Platform Support
- **Android Support**: Full support for Android apps via Appium
- **iOS Support**: Full support for iOS apps via Appium
- **Cross-platform API**: Unified interface for both platforms

#### Path Management
- **Path Recording**: Record all interactions as reusable paths
- **SQLite Database**: Local storage for paths and steps
- **Path Replay**: Replay any recorded path with configurable delays
- **Screenshot Capture**: Automatic screenshots at each step

#### Web Portal
- **Flask-based UI**: Beautiful web interface for path management
- **View Paths**: Display all recorded paths with metadata
- **Path Details**: View individual steps with screenshots and AI reasoning
- **Edit Paths**: Modify path names and descriptions
- **Delete Paths**: Remove unwanted paths
- **Human Interventions**: View all human assistance provided during crawls

#### Command Line Interface
- `crawl`: Start new intelligent crawls
- `replay`: Replay saved paths
- `list`: List all recorded paths
- `info`: Show detailed path information
- `web`: Launch web portal

#### Developer Tools
- **Database API**: Full CRUD operations for paths
- **AI Service API**: Pluggable AI provider system
- **Configuration Management**: Flexible config system
- **Docker Support**: Containerized deployment

#### Documentation
- Comprehensive README with examples
- Quick Start Guide
- API Documentation
- Architecture Overview
- Contributing Guidelines
- Example Scripts

#### Testing
- Database layer unit tests
- All tests passing with pytest
- Coverage reporting support

### Technical Details

#### Dependencies
- Python 3.8+
- Appium Python Client 3.1.0+
- Flask 3.0.0+
- OpenAI API (or Anthropic API)
- SQLite (built-in)

#### Database Schema
- `paths` table: Path metadata
- `path_steps` table: Individual step records
- `human_interventions` table: Human assistance records

#### Supported Actions
- Click/Tap
- Text Input
- Swipe
- Back Navigation

#### AI Capabilities
- DOM tree analysis
- Element extraction and classification
- Priority-based element ranking
- Input value generation
- Decision making with reasoning
- Human help requests

### Known Limitations
- Single device crawling (no parallel support yet)
- Local SQLite only (no distributed DB)
- Limited swipe gestures
- No performance metrics yet
- No CI/CD integration yet

### Future Roadmap
- [ ] Parallel crawling on multiple devices
- [ ] Advanced gesture support
- [ ] PostgreSQL/MongoDB support
- [ ] Cloud screenshot storage
- [ ] Analytics dashboard
- [ ] CI/CD integration
- [ ] Authentication and multi-user support
- [ ] Path comparison and diffing
- [ ] Auto-generated test scripts
- [ ] Performance metrics and reporting

---

## Release Notes

### v0.1.0 - MVP Release

This is the initial MVP (Minimum Viable Product) release of App Crawler, providing all core functionality needed for AI-powered mobile app testing.

**Key Highlights:**
- ✅ All 8 MVP requirements implemented
- ✅ Full Android and iOS support
- ✅ Beautiful web interface
- ✅ Comprehensive documentation
- ✅ Production-ready code quality

**Getting Started:**
```bash
pip install -r requirements.txt
python cli.py crawl --platform android --app-package com.example.app --name "My Test"
python cli.py web
```

**Feedback Welcome:**
This is our first release! Please open issues for bugs, feature requests, or questions.

---

[0.1.0]: https://github.com/codekaa1ciu1/app-crawler/releases/tag/v0.1.0
