import time
import logging
from urllib.parse import urlparse, urljoin
from lxml import html
import requests
from config import MAX_DEPTH, USER_AGENT, TIMEOUT, CRAWL_DELAY
from utils import normalize_url, fetch_robots_txt

class DomainCrawler:
    def __init__(self, domain, visited, timeouts, warc_queue, visited_queue, timeouts_queue,
                 shutdown_event, domain_queues):
        self.domain = domain
        self.visited = visited
        self.timeouts = timeouts
        self.warc_queue = warc_queue
        self.visited_queue = visited_queue
        self.timeouts_queue = timeouts_queue
        self.shutdown_event = shutdown_event
        self.domain_queues = domain_queues

    def crawl(self):
        try:
            rp = fetch_robots_txt(self.domain)
            logging.info(f"Started crawler for {self.domain}")
            domain_url = normalize_url(self.domain)
            domain_netloc = urlparse(domain_url).netloc
            queue = [(domain_url, 0)]
            local_visited = 0
            local_timeouts = 0
            while queue and not self.shutdown_event.is_set():
                url, depth = queue.pop(0)
                if depth > MAX_DEPTH or url in self.visited:
                    continue
                if not rp.can_fetch(url, USER_AGENT):
                    logging.info(f"Disallowed by robots.txt: {url}")
                    continue
                try:
                    time.sleep(CRAWL_DELAY)
                    response = requests.get(
                        url,
                        headers={'User-Agent': USER_AGENT},
                        timeout=TIMEOUT,
                        allow_redirects=True,
                        verify=False
                    )
                    if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                        self.visited.add(url)
                        self.visited_queue.put(url)
                        local_visited += 1
                        self.warc_queue.put((url, response.content, response.headers, response.status_code))
                        tree = html.fromstring(response.content)
                        links = tree.xpath('//a/@href')
                        for link in links:
                            abs_url = urljoin(url, link)
                            parsed = urlparse(abs_url)
                            if parsed.netloc != domain_netloc:
                                continue
                            clean_url = parsed._replace(fragment='', query='').geturl()
                            if clean_url not in self.visited:
                                queue.append((clean_url, depth + 1))
                except Exception as e:
                    logging.warning(f"Timeout/Error fetching {url}: {e}")
                    self.timeouts_queue.put(url)
                    self.timeouts.add(url)
                    local_timeouts += 1
            # Save remaining queue state if interrupted
            if self.shutdown_event.is_set():
                self.domain_queues[self.domain] = list(queue)
            logging.info(f"Finished {self.domain}: Visited {local_visited} | Timeouts: {local_timeouts}")
        except Exception as e:
            logging.error(f"Domain crawl failed: {e}")
