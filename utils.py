import logging
import json
from urllib.parse import urlparse, urlunparse
import requests
from protego import Protego

def setup_logging(log_file: str):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def normalize_url(url: str) -> str:
    """Remove fragments and normalize the URL."""
    parsed = urlparse(url)
    return urlunparse((
        parsed.scheme or "https",
        parsed.netloc,
        parsed.path.strip('/'),
        parsed.params,
        parsed.query,
        ""
    ))

def fetch_robots_txt(url: str) -> Protego:
    """Fetch and parse robots.txt for a domain."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = requests.get(robots_url, verify=False, timeout=5)
        rp = Protego.parse(response.text if response.status_code == 200 else "")
    except Exception as e:
        logging.error(f"Error fetching robots.txt for {robots_url}: {e}")
        rp = Protego.parse("")
    return rp

def save_domain_queues(domain_queues):
    """Save the current queues for each domain as JSON."""
    try:
        serializable = {domain: list(queue) for domain, queue in domain_queues.items()}
        with open('domain_queues.json', 'w') as f:
            json.dump(serializable, f, indent=2)
        logging.info("Saved domain queues to domain_queues.json")
    except Exception as e:
        logging.error(f"Error saving domain queues: {e}")

class ManagerSet:
    """A process-safe set using a managed dict."""
    def __init__(self, manager):
        self._dict = manager.dict()
    def add(self, item):
        self._dict[item] = True
    def __contains__(self, item):
        return item in self._dict
    def items(self):
        return self._dict.keys()
