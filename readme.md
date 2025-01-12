<div align="center">

# 🚀 Instagram FastAPI Crawler

A powerful and efficient Instagram hashtag crawler built with FastAPI and Instagrapi.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com)
[![Instagrapi](https://img.shields.io/badge/Instagrapi-2.1.2-orange.svg)](https://github.com/adw0rd/instagrapi)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## ✨ Features

- 🔄 **Concurrent Processing**: Fast parallel hashtag searching
- 📊 **Efficient Data Handling**: Multiple hashtags processed simultaneously
- 💾 **Smart Caching**: Database-backed for improved performance
- 🔒 **Reliable Access**: Robust session management system
- 🛡️ **Error Handling**: Comprehensive protection against API limitations

## 🛠️ Tech Stack

- **FastAPI** (0.115.0) - Modern, fast web framework
- **Instagrapi** (2.1.2) - Powerful Instagram private API
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Lightweight database
- **Python** 3.8+

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite3

### Installation

```bash
# Clone repository
git clone https://github.com/JungHoonGhae/instagram-fastapi-crawler.git
cd instagram-fastapi-crawler

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py
```

### Running Locally

```bash
uvicorn main:app --reload --port 8000
```

📝 API documentation available at: http://localhost:8000/docs

## 💾 Database Management

### CLI Access

```bash
# macOS
brew install sqlite

# Ubuntu/Debian
sudo apt-get install sqlite3

# Connect to database
sqlite3 insta_scraper.db
```

### Useful Commands

```sql
-- View sessions
SELECT id, username, is_block, is_challenge, number_of_use 
FROM instagram_sessions;

-- Check recent posts
SELECT id, profile, loading_time, 
       json_posts->>'$.hashtag' as hashtag,
       json_posts->>'$.count' as post_count
FROM insta_posts
ORDER BY create_at DESC
LIMIT 5;
```

## 🌐 API Usage

### Search Hashtags
```http
POST /api/hashtags/search
Content-Type: application/json

{
    "hashtags": ["programming", "python", "javascript"],
    "amount_per_tag": 20
}
```

## 🚀 Production Deployment

### AWS Setup

1. **Launch EC2**
   - Ubuntu Server 22.04 LTS
   - t2.micro (dev) / t2.small (prod)
   - Security: SSH(22), HTTP(80), HTTPS(443)

2. **Configure Server**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3-pip python3-venv nginx -y
   ```

3. **Deploy Application**
   ```bash
   # Setup
   git clone https://github.com/yourusername/instagram_crawler_FastAPI.git
   cd instagram_crawler_FastAPI
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt gunicorn

   # Configure services
   sudo systemctl start instagram-crawler
   sudo systemctl enable instagram-crawler
   sudo systemctl restart nginx
   ```

## 🔍 Monitoring

- CloudWatch integration for logs
- AWS SNS alerts
- Regular backups:
  ```bash
  sqlite3 insta_scraper.db ".backup '/backup/insta_scraper_$(date +%Y%m%d).db'"
  ```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
