GitHub Crawler
=========

Scrapy project to crawl [GitHub](https://github.com)

## Required Packages
 *  [scrapy](http://scrapy.org)
 *  [uritemplate](https://pypi.python.org/pypi/uritemplate)

## How to Use

### Crawler Settings
 *  `ITEM_STORAGE_PATH` - path to store crawled items
 *  `FILTER_STORAGE_PATH` - path to store metadata of filter middlewares or pipelines
 *  `PAGINATION_AWARE_SHUTDOWN_ENABLED` - if set to `True`, finish crawling paginated endpoints and shutdown the spider when hitting `Ctrl+C` on the keyboard
 *  `GITHUB_API_TOKEN` - the GitHub personal access token used by the spider

### Spider Settings

#### Common Settings
 *  `policy` - spider policy specifying whether to crawl certain types of entities or relations, which can be
    1.  a dict like `{'user': True, 'repository': True, 'user_starred': True}`
    2.  a string like `'user:0,repository:1,user_starred:0'`

#### Multitask Spider Settings
 *  `start_repos` - initial repositories to crawl, which can be
    1.  a list of dicts with the keys `'owner'` and `'repo'`
    2.  a comma separated string of repository full names
 *  `start_users` - initial users to crawl, which can be
    1.  a list of user names
    2.  a comma separated string of user names
 *  `start_orgs` - initial organizations to crawl, which can be
    1.  a list of organization names
    2.  a comma separated string of organization names

#### Endpoint Spider Settings
 *  `endpoint` - the endpoint to crawl

### Running Spider from Command Line
```
scrapy crawl {multitask-spider | endpoint-spider} [-s KEY=VALUE] [-a KEY=VALUE] -s JOBDIR=<jobdir> -s LOG_LEVEL=INFO -s LOG_FILE=<logfile> --logstderr
```
