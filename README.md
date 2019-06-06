# Simple sitemap tree generator


Simple sitemap tree generator that crawls a website and all links found and outputs
a tree with parent and children urls found.

It does not output a sitemap.xml file.


Requirements
- Python 3.6 or higher
- treelib
- beautifulsoup4
- requests


## Installation

$ git clone https://github.com/jambock/crawler  
$ pip3 install -r crawler/requirements.txt  
$ cd crawler



## Usage

```
$ python crawler.py  --help
usage: crawler.py [-h] --url URL [--max-workers MAX_WORKERS] [--print-tree]
                  [--print-links]

Simple sitemap generator.

optional arguments:
  -h, --help            show this help message and exit
  --url URL             Initial domain or url
  --max-workers MAX_WORKERS
                        Max number of threads (default: 1)
  --print-tree          Display a tree of the sitemap (default: True)
  --print-links         Print list of all links found in no particular order
                        (default: False)
```

```
$ python3 crawler.py --url https://fakesite.com --max-workers 12 --print-tree
  Queue size: 0, Parent urls: 419, Links found: 1139, Crawled Pages: 1113


https://fakesite.com
└── https://fakesite.com/
    ├── https://fakesite.com/about/
    ├── https://fakesite.com/blog/
    │   ├── https://fakesite.com/blog/2019/01/24/fakesite-golden-tickets/
    │   │   ├── https://fakesite.com/blog/2018/05/24/no-more-fakesite-waiting-list/
    │   │   │   └── https://fakesite.com/blog/authors/jordan-turtle/
    │   │   │       └── https://fakesite.com/blog/2018/07/13/joints-vouchers-in-labs/
    │   │   └── https://fakesite.com/blog/2018/06/05/fakesite-exchange-rate/
    │   │       ├── https://fakesite.com/blog/2018/04/26/more-than-one-store-voucher/
    │   │       └── https://fakesite.com/university/card-invoices
    │   │           └── https://fakesite.com/blog/2018/06/13/how-card-invoices-work/
    │   ├── https://fakesite.com/blog/2019/02/01/bill-splitting/
    │   │   └── https://fakesite.com/blog/2018/04/18/invoice-reactions/
    │   │       ├── https://fakesite.com/blog/2017/10/30/fakesite-to-fakesite-invoices/
    │   │       │   └── https://fakesite.com/blog/2017/10/24/android-pay/
    │   │       ├── https://fakesite.com/blog/2018/04/05/april-update/
    │   │       │   ├── https://fakesite.com/blog/2018/02/28/march-update/
    │   │       │   │   ├── https://fakesite.com/blog/2018/02/06/february-update/
    │   │       │   │   │   └── https://fakesite.com/blog/2018/01/25/store-statements/
    ...
    ...
    
    
    https://fakesite.com crawl completed in 49 seconds
    Crawled pages: 1114

```


## TODO
- Respect robots.txt option
- Follow subdomains option
- Extract links from existing sitemap.xml option
- ...




