import argparse
import logging
import re
import sys
import threading
import time
from queue import Queue, Empty
from urllib.parse import urlparse, urljoin, urldefrag

import requests
from bs4 import BeautifulSoup
from treelib import Tree

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(threadName)s - %(funcName)s - %(levelname)s - %(message)s')
logger.setLevel(logging.INFO)


local_thread = threading.local()


def get_session():
    """
    Make sure the running threads have their own requests session

    :return: requests Session
    :rtype: requests.Session
    """
    if not hasattr(local_thread, "session"):
        local_thread.session = requests.Session()
        local_thread.session.headers.update({'User-Agent': 'Mozilla/5.0 Crawly'})
    return local_thread.session


def crawl(queue):
    """

    Reads queue for links to crawl
    Extracts new links from crawled pages
    Adds new links to queue
    Builds the sitemap with parent/children urls

    :param queue: queue used to read/add links to
    :type queue: queue.Queue
    """
    # Hardcoded minimal list of extensions to ignore
    ignored_extensions = re.compile(
        '.(pdf|png|jpeg|jpg|doc|docx|xls|xlsx|zip|tar|gz|gif|exe|mov|avi|tiff|bmp|mpg|mp4|swf|wmv)$')
    try:
        while True:
            session = get_session()
            link = queue.get(timeout=5)
            (parent, child), = link.items()
            sys.stdout.write(f"\r Queue size: {queue.qsize()},"
                             f" Parent urls: {len(sitemap)},"
                             f" Links found: {len(links_found)},"
                             f" Crawled Pages: {len(crawled_pages)}")
            sys.stdout.flush()
            # Don't request ignored extensions
            if not ignored_extensions.search(child):
                try:
                    logger.debug(f'Requesting {link}')
                    response = session.get(child)
                except requests.exceptions.RequestException as e:
                    logger.error(f'Failed to request {child}: {e}')
                else:
                    if response.status_code == 200:
                        # Ideally, the sitemap should not have links that returns a redirect
                        # Instead of preventing redirects and adding a new link to the queue,
                        # we follow the redirect and add the final url to the list of links
                        if response.history:
                            # If the redirected url is in the same domain,
                            if urlparse(response.url).netloc == domain.netloc:
                                link[parent] = response.url
                        logger.debug(f'Adding {child} to crawled_pages')
                        # If successful, we keep a record of it
                        crawled_pages.add(child)
                        # Grab all the links found in the page
                        links = {response.url: get_links(response.text)}
                        # Add the parent and children to the sitemap
                        add_to_sitemap(link)
                        add_to_queue(links, queue)
                        queue.task_done()
                    else:
                        logger.debug(f'Skipping {child} because of status={response.status_code}')
            else:
                # If it matches ignored extension, add it to sitemap without crawling
                add_to_sitemap(link)

    except Empty:
        pass


def get_links(page):
    """
    Extracts links from page and does some processing before returning

    :param page: requests.text
    :type page: str
    :return: links found in page
    :rtype: set
    """
    links = set()
    soup = BeautifulSoup(page, features='html.parser')
    # Find all links in page
    for a in soup.find_all('a', href=True):
        link = a.get('href')
        # prepend scheme and domain if link is relative
        if link.startswith('/'):
            link = urljoin(domain.geturl(), link)
        # Skip external links
        if not urlparse(link).netloc == domain.netloc:
            continue
        # Remove anchor/fragment from link
        link = urldefrag(link).url
        # Remove query
        # if urlparse(link).query:
        #     link = urlparse(link).scheme + '://' + urlparse(link).netloc + urlparse(link).path
        links.add(link)
    return links


def add_to_queue(links, queue):
    """
    Adds new links to queue if not seen before

    :param links: Dictionary with parent and children urls
    :type links: dict
    :param queue: queue used to read/add links to
    :type queue: queue.Queue
    """

    for parent in links.keys():
        if len(links[parent]) > 0:
            for child in links[parent]:
                # Add link to queue if not seen before
                if child not in links_found:
                    link = {parent: child}
                    logger.debug(f'Queuing {link}')
                    links_found.add(child)
                    queue.put(link)


def add_to_sitemap(link):
    """
    For each crawled URL, we create a key in the sitemap
    If any links were found on that page, they are added as children
    Because each link is only visited once, the sitemap will only contain
    a reference to the first time the link was seen

    :param link: Dictionary with parent and child url
    :type link: dict
    """
    (parent, link), = link.items()
    if not sitemap.get(parent):
        sitemap[parent] = list()
    sitemap[parent].append(link)


def create_tree(sitemap_dict):
    """
    Reads sitemap dict and generate a tree of all links

    :param sitemap_dict: Sitemap generated during run
    :type sitemap_dict: dict
    """
    tree = Tree()
    root = list(sitemap_dict.keys())[0]
    tree.create_node(root, root)
    for k, v in sitemap_dict.items():
        if not tree.contains(k):
            logger.debug(f'Creating key: {k}')
            tree.create_node(k, k, parent=root)
        for i in v:
            if not tree.contains(i):
                logger.debug(f'Creating node {i}, parent: {k}')
                tree.create_node(i, i, parent=k)
    return tree


def parse_args():
    parser = argparse.ArgumentParser(description='Simple sitemap generator.')
    parser.add_argument('--url', default=None, dest='url', required=True, help='Initial domain or url')
    parser.add_argument('--max-workers', default=1, type=int, dest='max_workers', required=False,
                        help='Max number of threads (default: 1)')
    parser.add_argument('--print-tree', dest='print_tree', default=True, action='store_true',
                        help='Display a tree of the sitemap (default: True)')
    parser.add_argument('--print-links', dest='print_links', default=False, action='store_true',
                        help='Print list of all links found in no particular order (default: False)')
    return parser.parse_args()


def main(url, max_workers, print_tree, print_links):
    global domain, crawled_pages, links_found, sitemap
    if not url.startswith('http'):
        url = 'http://' + url
    start = time.perf_counter()
    crawled_pages = set()
    links_found = set()
    sitemap = dict()
    links_queue = Queue()
    domain = urlparse(url)
    initial_url = {url: [url, ]}
    add_to_queue(initial_url, links_queue)
    workers = []
    for i in range(max_workers):
        worker = threading.Thread(target=crawl, args=(links_queue,))
        worker.daemon = True
        worker.start()
        workers.append(worker)
    for worker in workers:
        worker.join()

    tree = create_tree(sitemap)
    print('\n\n')
    if print_tree:
        tree.show()

    if print_links:
        for link in crawled_pages:
            print(link)


    print(f'''
\n{url} crawl completed in {round(time.perf_counter() - start)} seconds
Crawled pages: {len(crawled_pages)}
        ''')


if __name__ == '__main__':
    args = parse_args()
    main(args.url, args.max_workers, args.print_tree, args.print_links)
