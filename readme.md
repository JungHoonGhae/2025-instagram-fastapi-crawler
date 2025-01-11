# 2025-instagram-fastapi-crawler

A powerful and efficient Instagram hashtag crawler built with FastAPI and Instagrapi. This API service allows you to fetch recent posts and information for multiple hashtags simultaneously.

## Features

- 🚀 Fast and concurrent hashtag searching
- 📊 Multiple hashtag processing in parallel
- 💾 Database caching for improved performance
- 🔒 Session management for reliable Instagram access

## Tech Stack

- FastAPI (0.115.0)
- Instagrapi (2.1.2)
- SQLAlchemy with SQLite
- Python 3.8+

## Local Development Setup

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- SQLite3

### 2. Installation
```bash
# Clone repository
git clone https://github.com/JungHoonGhae/2025-instagram-fastapi-crawler.git
cd 2025-instagram-fastapi-crawler

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py
```

### 3. Running the Application Locally
```bash
# Start FastAPI server
uvicorn main:app --reload --port 8000
```

Access the API documentation at: http://localhost:8000/docs

### 4. Local Database Management

#### Using SQLite CLI
```bash
# Install SQLite CLI if not installed
brew install sqlite  # macOS
sudo apt-get install sqlite3  # Ubuntu/Debian

# Connect to database
sqlite3 insta_scraper.db

# Useful commands
.tables  # Show all tables
.schema instagram_sessions
.schema insta_posts
.mode column
.headers on
```

#### Common Development Queries
```sql
-- Check Instagram sessions
SELECT id, username, is_block, is_challenge, number_of_use 
FROM instagram_sessions;

-- View recent posts
SELECT id, profile, loading_time, json_posts->>'$.hashtag' as hashtag,
       json_posts->>'$.count' as post_count
FROM insta_posts
ORDER BY create_at DESC
LIMIT 5;
```

#### GUI Database Tool
- Download [DB Browser for SQLite](https://sqlitebrowser.org/)
- Open `insta_scraper.db` with DB Browser

## Production Deployment (AWS)

### 1. Prerequisites
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Domain name (optional, for SSL)

### 2. EC2 Instance Setup
1. Launch EC2:
   - Ubuntu Server 22.04 LTS
   - t2.micro (development) or t2.small/medium (production)
   - Configure security group:
     ```
     - SSH (22)
     - HTTP (80)
     - HTTPS (443)
     ```

2. Configure Instance:
   ```bash
   # Connect to instance
   ssh -i your-key.pem ubuntu@your-ec2-ip

   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install dependencies
   sudo apt install python3-pip python3-venv nginx -y
   ```

### 3. Application Deployment
1. Setup Project:
   ```bash
   git clone https://github.com/yourusername/instagram_crawler_FastAPI.git
   cd instagram_crawler_FastAPI
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure Gunicorn:
   ```bash
   pip install gunicorn
   sudo nano /etc/systemd/system/instagram-crawler.service
   ```
   Add configuration:
   ```ini
   [Unit]
   Description=Instagram Crawler FastAPI
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/instagram_crawler_FastAPI
   Environment="PATH=/home/ubuntu/instagram_crawler_FastAPI/venv/bin"
   ExecStart=/home/ubuntu/instagram_crawler_FastAPI/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

   [Install]
   WantedBy=multi-user.target
   ```

3. Configure Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/instagram-crawler
   ```
   Add configuration:
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

4. Start Services:
   ```bash
   # Start Gunicorn
   sudo systemctl start instagram-crawler
   sudo systemctl enable instagram-crawler

   # Configure Nginx
   sudo ln -s /etc/nginx/sites-available/instagram-crawler /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### 4. Production Database Management
1. Access Database:
   ```bash
   # Connect to production database
   sqlite3 /home/ubuntu/instagram_crawler_FastAPI/insta_scraper.db
   ```

2. Monitoring Queries:
   ```sql
   -- Check system status
   SELECT COUNT(*) as total_sessions,
          SUM(CASE WHEN is_block = 1 OR is_challenge = 1 THEN 1 ELSE 0 END) as blocked_sessions
   FROM instagram_sessions;

   -- Monitor recent activity
   SELECT DATE(create_at) as date,
          COUNT(*) as searches,
          COUNT(DISTINCT profile) as unique_hashtags
   FROM insta_posts
   GROUP BY DATE(create_at)
   ORDER BY date DESC
   LIMIT 7;
   ```

### 5. Monitoring & Maintenance
- Set up CloudWatch for logs and metrics
- Configure AWS SNS for alerts
- Regular database backups:
  ```bash
  # Backup database
  sqlite3 insta_scraper.db ".backup '/backup/insta_scraper_$(date +%Y%m%d).db'"
  ```

## API Endpoints

### Search Multiple Hashtags
```http
POST /api/hashtags/search
```
Request body:
```json
{
    "hashtags": ["programming", "python", "javascript"],
    "amount_per_tag": 20
}
```

## Error Handling

The API includes comprehensive error handling for:
- Instagram API limitations
- Challenge requirements
- Login issues
- Rate limiting
- Network errors

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.