# Scrapy settings for ghcrawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'ghcrawler'

SPIDER_MODULES = ['ghcrawler.spiders']
NEWSPIDER_MODULE = 'ghcrawler.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'ghcrawler (+http://www.yourdomain.com)'
