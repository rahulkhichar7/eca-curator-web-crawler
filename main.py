import signal
import logging
from multiprocessing import Process, Manager, Queue
from config import SEED_FILE, LOG_FILE, JOIN_TIMEOUT
from utils import setup_logging, ManagerSet, save_domain_queues
from writers import warc_writer_process, visited_writer, timeouts_writer
from crawler import DomainCrawler
import warnings
warnings.filterwarnings('ignore')


def main():
    setup_logging(LOG_FILE)
    # Read domains from seed file
    with open(SEED_FILE, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    manager = Manager()
    visited = ManagerSet(manager)
    timeouts = ManagerSet(manager)
    shutdown_event = manager.Event()
    domain_queues = manager.dict()

    warc_queue = Queue()
    visited_queue = Queue()
    timeouts_queue = Queue()

    writer_proc = Process(target=warc_writer_process, args=(warc_queue,))
    visited_proc = Process(target=visited_writer, args=(visited_queue,))
    timeouts_proc = Process(target=timeouts_writer, args=(timeouts_queue,))
    writer_proc.start()
    visited_proc.start()
    timeouts_proc.start()

    workers = []
    for domain in domains:
        crawler = DomainCrawler(
            domain, visited, timeouts, warc_queue, visited_queue, timeouts_queue,
            shutdown_event, domain_queues
        )
        p = Process(target=crawler.crawl)
        p.start()
        workers.append(p)

    def handle_interrupt(signum, frame):
        logging.info("Keyboard interrupt received. Initiating shutdown...")
        shutdown_event.set()
        for p in workers:
            p.join(timeout=2)
        save_domain_queues(domain_queues)
        warc_queue.put(None)
        visited_queue.put(None)
        timeouts_queue.put(None)
        writer_proc.join(timeout=JOIN_TIMEOUT)
        visited_proc.join(timeout=JOIN_TIMEOUT)
        timeouts_proc.join(timeout=JOIN_TIMEOUT)
        logging.info("Shutdown complete.")
        exit(0)

    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        for p in workers:
            p.join()
    finally:
        if not shutdown_event.is_set():
            warc_queue.put(None)
            visited_queue.put(None)
            timeouts_queue.put(None)
            writer_proc.join()
            visited_proc.join()
            timeouts_proc.join()
            logging.info("Crawling completed successfully.")

if __name__ == "__main__":
    main()
