import os

# Directories
SEED_FILE = 'seed.txt'
WARC_DIR = 'warc_files'
FILES_DIR = 'files'

os.makedirs(WARC_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

# Crawler settings
MAX_DEPTH = 10
USER_AGENT = 'EkaCurator/1.0'
TIMEOUT = 10
WARC_SIZE_LIMIT = 5000 * 1024 * 1024  # 5 TB (uncompressed)
CRAWL_DELAY = 0.1  # seconds
JOIN_TIMEOUT = 3   # seconds

# Logging
LOG_FILE = 'crawler.log'
