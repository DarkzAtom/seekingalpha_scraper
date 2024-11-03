import asyncio
import random
import time
from asyncio import timeout

from undetected_playwright.async_api import async_playwright, expect, Playwright
from playwright_stealth import stealth_async, StealthConfig
import json
import logging
from datetime import date, timedelta
from collections import Counter
import re
import pyautogui
import random
import datetime
import fetch_anticaptchacom_solved_obj
import csv


# logger
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),  # Write logs to a file
        logging.StreamHandler()  # Print logs to the console
    ]
)
logger = logging.getLogger(__name__)


# globals
initial_link = 'https://seekingalpha.com/latest-articles'
# initial_link = 'https://2ip.io'
seek_alpha_login = 'wise.investor.7783@gmail.com'
seek_alpha_pswd = '7878wiin'
user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.2045.43 Safari/537.36 Edg/117.0.2045.43',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.1938.69 Safari/537.36 Edg/116.0.1938.69',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.1901.203 Safari/537.36 Edg/115.0.1901.203',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.1823.67 Safari/537.36 Edg/114.0.1823.67',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.62 Safari/537.36 OPR/101.0.4843.33',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Safari/537.36 OPR/100.0.4815.30',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.110 Safari/537.36 OPR/99.0.4788.87',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36 OPR/98.0.4759.39',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.93 Safari/537.36 OPR/97.0.4719.63',
    ]

user_agent = random.choice(user_agents)

retry_init_failure_count = 0

proxy_dict = {
    'proxyaddr': '168.158.229.230',
    'proxyport': '50100',
    'proxylogin': 'raycchen',
    'proxypswd': 'm95TTKR2Nc',
}

async def setup_browser_context(playwright: Playwright, state=None):

    print(f'USER-AGENT selected: {user_agent}')

    browser = await playwright.chromium.launch(
        headless=False,
        channel='chrome',
        slow_mo=750,
        proxy={
            "server": f"http://{proxy_dict['proxyaddr']}:{proxy_dict['proxyport']}",
            "username": proxy_dict['proxylogin'],
            "password": proxy_dict['proxypswd']
        },
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            # '--disable-blink-features=AutomationControlled',
            '--start-maximized',
            '--disable-extensions',
            '--disable-infobars',
            # '--lang=en-US,en;q=0.9',
            '--disable-backgrounding-occluded-windows',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--ignore-certificate-errors',
            '--disable-popup-blocking',
            '--disable-notifications',
            '--disable-browser-side-navigation',
            # '--disable-features=IsolateOrigins,site-per-process',
        ]
    )

    context = await browser.new_context(
        storage_state='playwright/.auth/last_seekingalpha_state.json' if state else None,
        locale='en-US',
        user_agent=None,
        no_viewport=True,  # Set to your desired window size
        ignore_https_errors=True,  # Ignore certificate errors
    )

    # Adding experimental features similar to Selenium's options
    await context.add_init_script("""
        delete window.__proto__.webdriver;
    """)

    # Disable `navigator.webdriver` (mimic undetectable-chromedriver behavior)
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    return browser, context


def count_repetitions(input_list):
    # Use Counter to count occurrences of each element
    count_dict = Counter(input_list)

    # Filter out elements that appear only once
    repetitions = {item: count for item, count in count_dict.items() if count > 1}

    return repetitions


def extract_author_name(url):
    pattern = r'/author/([^#]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def get_date_string(offset=0):
    """
    Generate a formatted date string like "Saturday, November 2nd," based on today's date and an offset

    Args:
        offset (int): Number of days to offset from today (negative for past dates, 0 for today, positive for future dates)

    Returns:
        str: Formatted date string (e.g., "Saturday, November 2nd,")
    """
    target_date = date.today() + timedelta(days=offset)

    # Get day suffix (st, nd, rd, th)
    day = target_date.day
    if day in (1, 21, 31):
        suffix = "st"
    elif day in (2, 22):
        suffix = "nd"
    elif day in (3, 23):
        suffix = "rd"
    else:
        suffix = "th"

    # Format the date string
    date_string = target_date.strftime(f"%A, %B {day}{suffix},")

    return date_string


def filter_aliases(link_list, aliases):
    seen = set()
    result = []

    for link in link_list:
        # Check if any alias is in the link
        matching_alias = next((alias for alias in aliases if alias in link), None)

        if matching_alias:
            if matching_alias not in seen:
                seen.add(matching_alias)
                result.append(link)
        else:
            result.append(link)

    return result

articles_parsed_list = []
authors_parsed_list = []


async def check_for_captcha(page):
    try:
        # Check for common CAPTCHA indicators
        captcha_selectors = [
            # your selectors here
        ]

        try:
            for selector in captcha_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    logger.info("CAPTCHA detected via selector!")
                    return True
        except Exception as e:
            logger.error(f"Error checking selectors: {e}")

        try:
            # Make sure to await the content
            page_text = (await page.inner_text('body')).lower()
            captcha_indicators = [
                'press & hold'
            ]

            if any(indicator in page_text for indicator in captcha_indicators):
                logger.info("CAPTCHA text detected!")
                return True

        except Exception as e:
            logger.error(f"Error checking page content: {e}")

        return False

    except Exception as e:
        logger.error(f"Error in main captcha check: {e}")
        return False


class CaptchaException(Exception):
    pass

class EmptyTaskException(Exception):
    pass


async def run_task_article(link: str, task_index, semaphore):
    async with semaphore:
        try:
            logger.info(f'Starting task for link: {link}')
            async with async_playwright() as playwright:
                logger.info('Playwright initiated')
                browser, context = await setup_browser_context(playwright, state=True)
                # browser, context = setup_browser_context(playwright)
                logger.info('Browser context created')
                page = await context.new_page()
                logger.info('New page created')

                response_data = []

                async def handle_response(response):
                    if "real_time_quotes?sa_ids=" in response.url and "%2C" not in response.url:
                        try:
                            data = await response.json()
                            response_data.append(data)
                            logger.info("Found the response:", data)
                        except Exception as e:
                            logger.error(f"Error processing response: {e}")

                page.on("response", handle_response)
                logger.info('Response handler attached')


                logger.info('Attempting to navigate to the page...')
                await page.goto(link)
                logger.info('Page loaded')

                logger.info('Waiting for network idle...')
                try:
                    await page.wait_for_load_state('networkidle', timeout=20000)
                except Exception as e:
                    logger.error(f"{e}, ale lets go")
                logger.info('Network idle')
                logger.info('Starting captcha check')
                if await check_for_captcha(page):
                    logger.error('Captcha detected!')
                    raise CaptchaException("Captcha detected!")
                logger.info('Checking for premium')
                # if await page.get_by_text('Unlock this article with Premium').is_visible(timeout=3000):
                #     logger.error('Detected Premium!!!! skipping')
                #     art_dict_to_append = {
                #         'articleUrl': link,
                #         'articleId': re.search(r'/article/(\d+)-', link).group(1),
                #         'title': "PremiumRequired",
                #         'fullArticle': "PremiumRequired",
                #         'articleDate': "PremiumRequired",
                #         'stockTicker': "PremiumRequired",
                #         'author': "PremiumRequired",
                #         'authorTitle': "PremiumRequired",
                #         'authorUrl': "PremiumRequired",
                #         # 'rating': rating,
                #         'priceAtPublication': "PremiumRequired",
                #         'scrapedDate': datetime.datetime.today().strftime('%Y-%m-%d'),
                #     }
                #     articles_parsed_list.append(art_dict_to_append)
                #     return
                article_url = link       # good
                article_id = re.search(r'/article/(\d+)-', link).group(1)      #  good

                logger.info('looking for title')
                try:
                    title = await page.inner_text("h1[data-test-id='post-title']", timeout=2500)    #   good
                except Exception as e:
                    logger.error(f"Error processing title: {e}")
                    title = ''

                logger.info('looking for summary of the article to add to the \'full article\'')
                try:
                    summary_article_label_unrfnd = await page.locator('h2[data-test-id=\'article-summary-title\']').inner_text(timeout=2500)
                    summary_article_bulletpoints_unrfnd = await page.locator('h2[data-test-id=\'article-summary-title\'] + ul').locator('li').all()
                    bpoints = []
                    for bulletpoint in summary_article_bulletpoints_unrfnd:
                        bpoint_toappend = await bulletpoint.inner_text(timeout=2500)
                        bpoints.append(bpoint_toappend)
                    summary_article = summary_article_label_unrfnd + '\n\n' + '\n'.join(' ' + '-' + '  ' + bpoint for bpoint in bpoints) + '\n\n'
                except Exception as e:
                    logger.error(f"Error processing summary: {e}")
                    summary_article = ''


                logger.info('looking for article unrefined')
                try:
                    full_article_unrefined_unsorted = await page.locator("div[data-test-id='content-container'] > *").all()
                    full_article_unrfnd_sorted: list  = []
                    for index, el in enumerate(full_article_unrefined_unsorted):
                        element_type_name = await el.evaluate("element => element.tagName.toLowerCase()")
                        if element_type_name == 'p' or element_type_name == 'h2' or element_type_name == 'h3':
                            extr_text = await el.inner_text(timeout=2500)
                            if element_type_name == 'h2' or element_type_name == 'h3':
                                extr_text = '\n' + extr_text + '\n\n'
                            elif element_type_name == 'p':
                                extr_text = extr_text + '\n'
                            full_article_unrfnd_sorted.append(extr_text)
                        else:
                            pass
                    full_article_unrefined = full_article_unrfnd_sorted
                except Exception as e:
                    logger.error(f"Error processing article unrefined: {e}")
                    full_article_unrefined = ''

                logger.info('joining the refined parts')
                try:
                    full_article = ''.join(full_article_unrefined)
                    if '»' in full_article:
                        full_article = full_article.split('»', 1)[1]
                        full_article = full_article.lstrip('\n')
                    if summary_article != '':
                        full_article = summary_article + '\n' + full_article
                except Exception as e:
                    logger.error(f"Error processing joining the article: {e}")
                    full_article = ''

                logger.info('looking for article date')
                try:
                    article_date = await page.inner_text("span[data-test-id='post-date']", timeout=2500)       #   good
                except Exception as e:
                    logger.error(f"Error processing article date: {e}")
                    article_date = ''

                logger.info('looking for author')
                try:
                    author = await page.inner_text("a[data-test-id='author-name']", timeout=2500)        #   good
                except Exception as e:
                    logger.error(f"Error processing author: {e}")
                    author = ''

                logger.info('looking for author title')
                try:
                    author_title = await page.inner_text("a[data-test-id='author-badge']", timeout=2500)        #   good
                except Exception as e:
                    logger.error(f"Error processing author title: {e}")
                    author_title = ''

                logger.info('looking for url')
                try:
                    author_url = await page.locator("a[data-test-id='author-name']").nth(0).get_attribute('href', timeout=2500)        #   good
                except Exception as e:
                    logger.error(f"Error processing author url: {e}")
                    author_url = ''
                scraped_date = datetime.datetime.today().strftime('%Y-%m-%d')          #  good

                logger.info('waiting on the page 3 sec')
                await page.wait_for_timeout(1500)
                await page.wait_for_timeout(1500)


                logger.info('Processing the response data')
                price_data = None
                start_time = time.time()
                while time.time() - start_time < 15:
                    if response_data:
                        price_data = response_data[0]
                        logger.info(f'Captured data: {price_data}')
                        break
                    time.sleep(0.5)

                if not response_data:
                    logger.error("No response captured after 10 seconds")

                try:
                    stock_ticker = price_data['real_time_quotes'][0]['symbol']
                    price_at_pub = price_data['real_time_quotes'][0]['last']
                except (TypeError, KeyError, IndexError):
                    stock_ticker = ''
                    price_at_pub = ''

                try:
                    rating = await page.locator('span[data-test-id="quant-badge"]').nth(0).text_content(timeout=1500)
                except Exception as e:
                    try:
                        rating = await page.locator('section[data-test-id="news-symbol-ratings"]').locator('div').locator('div[class*="col"]').locator('span[data-test-id="text-rating-badge"]').nth(0).text_content(timeout=1500)
                    except Exception as e:
                        rating = ""
                        logger.error(f"Error processing rating: {e}")

                if title == '':
                    raise EmptyTaskException("There's nothing in the article: do not append")

                art_dict_to_append = {
                    'article_url': article_url,
                    'article_id': article_id,
                    'title': title,
                    'full_article': full_article,
                    'article_date': article_date,
                    'stock_ticker': stock_ticker,
                    'author': author,
                    'author_title': author_title,
                    'author_url': 'https://seekingalpha.com' + author_url,
                    'rating': rating,
                    'price_at_publication': price_at_pub,
                    'scraped_date': scraped_date,
                    'vendor_name': 'matvey_fedosenko'
                }
                logger.info(art_dict_to_append)

                # temp solution
                # for key, value in art_dict_to_append.items():
                #     logger.info(f'{key}: {value}')

                articles_parsed_list.append(art_dict_to_append)

                # csv_file_temp_test = "articles_polygon.csv"
                #
                # with open(csv_file_temp_test, mode='w', newline='', encoding='utf-8') as file:
                #     writer = csv.DictWriter(file, fieldnames=articles_parsed_list[0].keys())
                #     writer.writeheader()
                #     for data in articles_parsed_list:
                #         writer.writerow(data)


                await browser.close()
        except CaptchaException as e:
            logger.error(f'Captcha, except block: {e}')
            logger.info('Initiating the anti-captcha bypass process')
            fetch_anticaptchacom_solved_obj.solve_obj(link, seek_alpha_login, seek_alpha_pswd)
            semaphore.release()
            return await run_task_article(link, task_index, semaphore)

        except EmptyTaskException as e:
            logger.error(f"{article_url} is not appended, since all the values are empty")


        except Exception as e:
            logger.error(f'Caught exception running single task: {e}')


def get_linkedin_id(url):
    if not url:
        return None

    # Handle old format with view?id=
    if 'view?id=' in url:
        return url.split('id=')[1].split('&')[0]

    # Handle new format
    try:
        # For /in/ profiles
        if '/in/' in url:
            return url.split('/in/')[-1].split('?')[0].rstrip('/')
        # For company profiles
        elif '/company/' in url:
            return url.split('/company/')[-1].split('?')[0].rstrip('/')
        else:
            return None
    except:
        return None


async def run_task_author(link, task_index, semaphore):
    async with semaphore:
        try:
            logger.info(f'Starting task for link: {link}')
            async with async_playwright() as playwright:
                logger.info('Playwright initiated')
                browser, context = await setup_browser_context(playwright, state=True)
                # browser, context = setup_browser_context(playwright)
                logger.info('Browser context created')
                page = await context.new_page()
                logger.info('New page created')

                logger.info('Attempting to navigate to the page...')
                await page.goto(link)
                logger.info('Page loaded')

                logger.info('Waiting for network idle...')
                try:
                    await page.wait_for_load_state('networkidle', timeout=20000)
                except Exception as e:
                    logger.error(f"{e}, ale let's go")
                logger.info('Network idle')
                logger.info('Starting captcha check')
                if await check_for_captcha(page):
                    logger.error('Captcha detected!')
                    raise CaptchaException("Captcha detected!")

                # elements section

                author_url = link  #done

                logger.info("looking for author's photo url")
                try:
                    # Just find any img with src in the correct wrapper
                    photo_url = await page.evaluate('''
                        () => {
                            const outerwrapper = document.querySelector('[data-test-id="author-header"]');
                            const wrapper = outerwrapper.querySelector('[data-test-id="user-pic-wrapper"]');
                            const img = wrapper ? wrapper.querySelector('img') : null;
                            return img ? img.src : null;
                        }
                    ''')
                    if not photo_url:
                        photo_url = ''
                except Exception as e:
                    logger.error(f"Error processing author's photo url: {e}")
                    photo_url = ''

                logger.info('looking for author\'s name')   #done
                try:
                    name = await page.locator('h1[data-test-id="article-author"]').text_content(timeout=500)
                except Exception as e:
                    logger.error(f"Error processing author\'s name: {e}")
                    name = ''

                logger.info('looking for the author\'s title')
                try:
                    author_title = await page.locator('[data-test-id="author-badge"]').text_content(timeout=500)
                except Exception as e:
                    logger.error(f"Error processing author\'s title: {e}")
                    author_title = ''

                logger.info('looking for author\'s since')
                try:
                    since = await page.locator('div[data-test-id="author-detail"]').get_by_text(re.compile('since', re.IGNORECASE)).text_content(timeout=500)
                except Exception as e:
                    logger.error(f"Error processing author\'s since: {e}")
                    since = ''

                logger.info('looking for company')     #done
                try:
                    company = await page.locator('section[data-test-id="about-card"]').get_by_text('Company').locator('+ span').text_content(timeout=500)
                except Exception as e:
                    logger.error(f"Error processing company: {e}")
                    company = ''

                # logger.info('looking for author\'s bio short')
                # try:
                #     bio_short = await page.locator
                # except Exception as e:
                #     logger.error(f"Error processing author bio short: {e}")
                #     bio_short = 'None'

                logger.info('looking for author bio full')
                try:
                    bio_full = await page.locator("div[data-test-id='content-container']").nth(1).text_content(timeout=500)
                except Exception as e:
                    logger.error(f"Error processing author bio full: {e}")
                    bio_full = ''

                logger.info('looking for x_url')
                try:
                    x_url = await page.locator('a[data-test-id="twitter-icon"]').nth(0).get_attribute('href', timeout=500)
                except Exception as e:
                    logger.error(f"Error processing x_url: {e}")
                    x_url = ''

                logger.info('looking for x_handle')
                try:
                    x_handle_unstrip = x_url.rstrip('/')
                    x_handle = x_handle_unstrip.split('/')[-1]
                except Exception as e:
                    logger.error(f"Error processing x_handle: {e}")
                    x_handle = ''

                logger.info('looking for linkedin_url')
                try:
                    linkedin_url = await page.locator('a[data-test-id="linkedIn-icon"]').nth(0).get_attribute('href', timeout=500)
                except Exception as e:
                    logger.error(f"Error processing linkedin_url: {e}")
                    linkedin_url = ''

                logger.info('looking for linkedin_id')
                try:
                    linkedin_id = get_linkedin_id(linkedin_url)
                except Exception as e:
                    logger.error(f"Error processing linkedin_id: {e}")
                    linkedin_id = ''

                logger.info('looking for theme_title')      #done
                try:
                    theme_title = await page.locator('h3[data-test-id="banner-title"]').text_content(timeout=500)
                except Exception as e:
                    logger.error(f"Error processing theme_title: {e}")
                    theme_title = ''

                logger.info('looking for theme_desc')
                try:
                    theme_desc = await page.locator('div.hidden.text-medium-2-r:has(+ a[data-test-id="learn-more-button"])').text_content(timeout=500)
                except Exception as e:
                    logger.error(f"Error processing theme_desc: {e}")
                    theme_desc = ''

                logger.info('looking for theme_reviews')      #done
                try:
                    get_number = lambda text: re.search(r'[\d.]+[KMB]?', text).group()
                    theme_reviews_unrfnd = await page.locator('a[data-test-id="rating-link"]').text_content(timeout=500)
                    theme_reviews = get_number(theme_reviews_unrfnd)
                except Exception as e:
                    logger.error(f"Error processing theme_reviews: {e}")
                    theme_reviews = ''

                logger.info('looking for num_analysis')    #to be refined: 'Analysis (2.8K)'
                try:
                    num_analysis_unrfnd = await page.locator('li[data-test-id*="Analysis"]').text_content(timeout=500)
                    num_analysis = re.search(r'\((.*?)\)', num_analysis_unrfnd).group(1)
                except Exception as e:
                    logger.error(f"Error processing num_analysis: {e}")
                    num_analysis = ''

                logger.info('looking for num_inv_group_research')    #to be refined 'Investing Group Research (1.16K)'
                try:
                    num_inv_group_research_unrfnd = await page.locator('li[data-test-id*="Investing Group Research"]').text_content(timeout=500)
                    num_inv_group_research = re.search(r'\((.*?)\)', num_inv_group_research_unrfnd).group(1)
                except Exception as e:
                    logger.error(f"Error processing num_inv_group_research: {e}")
                    num_inv_group_research = ''

                logger.info('looking for num_blog_posts')
                try:
                    num_blog_posts_unrfnd = await page.locator('li[data-test-id*="Blog Posts"]').text_content(timeout=500)
                    num_blog_posts = re.search(r'\((.*?)\)', num_blog_posts_unrfnd).group(1)
                except Exception as e:
                    logger.error(f"Error processing num_blog_posts: {e}")
                    num_blog_posts = ''

                logger.info('looking for num_comments')
                try:
                    num_comments_unrfnd = await page.locator('li[data-test-id*="Comments"]').text_content(timeout=500)
                    num_comments = re.search(r'\((.*?)\)', num_comments_unrfnd).group(1)
                except Exception as e:
                    logger.error(f"Error processing num_comments: {e}")
                    num_comments = ''

                logger.info('looking for num_likes')
                try:
                    num_likes_unrfnd = await page.locator('li[data-test-id*="Likes"]').text_content(timeout=500)
                    num_likes = re.search(r'\((.*?)\)', num_likes_unrfnd).group(1)
                except Exception as e:
                    logger.error(f"Error processing num_likes: {e}")
                    num_likes = ''

                logger.info('looking for num_followers')
                try:
                    num_followers_unrfnd = await page.locator('li[data-test-id*="Followers"]').text_content(timeout=500)
                    num_followers = re.search(r'\((.*?)\)', num_followers_unrfnd).group(1)
                except Exception as e:
                    logger.error(f"Error processing num_followers: {e}")
                    num_followers = ''

                logger.info('looking for num_following')
                try:
                    num_following_unrfnd = await page.locator('li[data-test-id*="Following"]').text_content(timeout=500)
                    num_following = re.search(r'\((.*?)\)', num_following_unrfnd).group(1)
                except Exception as e:
                    logger.error(f"Error processing num_following: {e}")
                    num_following = ''

                scraped_date = datetime.datetime.today().strftime('%Y-%m-%d')

                author_dict_to_append = {
                    'author_url': author_url,
                    'name': name,
                    'photo_url': photo_url,
                    'author_title': author_title,
                    'since': since,
                    'company': company,
                    # 'bioShort': bio_short,
                    'bio_full': bio_full,
                    'x_url': x_url,
                    # 'x_handle': x_handle,
                    'linked_in_url': linkedin_url,
                    # 'linked_in_ID': linkedin_id,
                    'theme_title': theme_title,
                    'theme_description': theme_desc,
                    'theme_reviews': theme_reviews,
                    'num_analysis': num_analysis,
                    'num_inv_group_research': num_inv_group_research,
                    'num_blog_posts': num_blog_posts,
                    'num_comments': num_comments,
                    'num_likes': num_likes,
                    'num_followers': num_followers,
                    'num_following': num_following,
                    'scraped_date': scraped_date,
                    'vendor_name': 'matvey_fedosenko'
                }
                logger.info(author_dict_to_append)

                # logger.info('\n\nDEBUG VALUES SECTION\n\n')
                # for key, value in author_dict_to_append.items():
                #     logger.info(f'{key}: {value}')


                authors_parsed_list.append(author_dict_to_append)

                await browser.close()
        except CaptchaException as e:
            logger.error(f'Captcha, except block: {e}')
            logger.info('Initiating the anti-captcha bypass process')
            fetch_anticaptchacom_solved_obj.solve_obj(link, seek_alpha_login, seek_alpha_pswd)
            semaphore.release()
            return await run_task_article(link, task_index, semaphore)

        except EmptyTaskException as e:
            logger.error(f"{author_url} is not appended, since all the values are empty")


        except Exception as e:
            logger.error(f'Caught exception running single task: {e}')





async def init_script():
    try:
        async with async_playwright() as playwright:
            browser, context = await setup_browser_context(playwright, state=True)
            page = await context.new_page()
            # config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
            # await stealth_async(page, config)
            await page.goto(initial_link)
            logger.info('waiting for the network idle')
            try:
                await page.wait_for_load_state('networkidle', timeout=20000)
            except Exception as e:
                logger.error(f"{e}, ale let\'s go")
            logger.info('Network idle')
            if await check_for_captcha(page):
                logger.error('Captcha has been located! Retrying...')
                await browser.close()
                fetch_anticaptchacom_solved_obj.solve_obj('https://seekingalpha.com/latest-articles', seek_alpha_login, seek_alpha_pswd)
                return await init_script()
            if await page.locator("div[data-test-id='user-menu-dropdown']").is_visible(timeout=5000):
                logger.info('The session is successfully logged! Continue!')
                pass
            else:
                # reject_cookies_btn = page.locator("button#onetrust-reject-all-handler")
                sign_in_btn = page.locator("button[data-test-id='header-button-sign-in']")
                # await reject_cookies_btn.click()
                await sign_in_btn.click()
                email_input_box = page.locator("input[name='email']")
                pswd_input_box = page.locator("input[name='password']")
                submit_login_btn = page.locator("button[data-test-id='sign-in-button']")
                await email_input_box.fill(seek_alpha_login)
                await pswd_input_box.fill(seek_alpha_pswd)
                await submit_login_btn.click()
            await page.wait_for_timeout(2500)
            show_the_date_btn = page.locator("button[data-test-id='date-range-dropdown']")
            await show_the_date_btn.click()
            date_string = get_date_string(-4)  #regulate the date you want to scrape here
            day_btn = page.get_by_label(date_string)
            # day_btn = page.get_by_label("Today, Saturday, November 2nd,")
            try:
                await day_btn.click(timeout=5500)
            except Exception as e:
                logger.error(f'couldn\'t find the day button, choosing the previous month: {e}')
                get_to_the_prev_month = page.locator('button[aria-label="Go to the Previous Month"]')
                await get_to_the_prev_month.click(timeout=2500)
                await page.wait_for_timeout(2500)
                await day_btn.click()
            await page.wait_for_timeout(1350)
            await day_btn.click()
            await page.wait_for_timeout(2500)
            submit_the_date_button = page.locator("button[data-test-id='date-picker-apply-button']")
            await submit_the_date_button.click()
            await page.wait_for_timeout(3000)
            await page.wait_for_timeout(2500)
            await page.reload()
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
            except Exception as e:
                logger.error(f"{e}, ale let\'s go")
            if await check_for_captcha(page):
                logger.error('Captcha has been located! Retrying...')
                await browser.close()
                fetch_anticaptchacom_solved_obj.solve_obj('https://seekingalpha.com/latest-articles', seek_alpha_login, seek_alpha_pswd)
                return await init_script()
            # scrolling part
            max_scrolls = 100
            scroll_count = 0
            scroll_step = 450
            scroll_delay = 1350
            no_new_content_count = 0
            max_no_new_content = 5  # Number of scrolls without new content before stopping

            last_height = await page.evaluate("document.body.scrollHeight")

            while scroll_count < max_scrolls:
                # Get current scroll position
                current_position = await page.evaluate("window.pageYOffset")

                # Scroll down smoothly
                new_position = current_position + scroll_step
                await page.evaluate(f"window.scrollTo({{top: {new_position}, behavior: 'smooth'}})")

                # Wait for potential new content to load
                await page.wait_for_timeout(scroll_delay)

                # Check new scroll height
                new_height = await page.evaluate("document.body.scrollHeight")

                if new_height == last_height:
                    no_new_content_count += 1
                else:
                    no_new_content_count = 0

                # If no new content has been loaded for several scrolls, stop
                if no_new_content_count >= max_no_new_content:
                    print(f"No new content after {no_new_content_count} scrolls. Stopping.")
                    break

                last_height = new_height
                scroll_count += 1
            items_list_container = page.locator("div[data-test-id='post-list']")
            all_articles = await items_list_container.locator('article').all()
            article_links_list = []
            article_author_links_list = []
            for index, article in enumerate(all_articles):
                print(f'Processing: {index}')
                article_link = await article.locator("a[data-test-id='post-list-item-title']").get_attribute('href')
                article_link = 'https://seekingalpha.com' + article_link
                article_author_links = await article.locator("footer[data-test-id='post-footer'] a").evaluate_all("elements => elements.map(el => el.href)")
                article_author_link = next((link for link in article_author_links if 'author' in link), None)
                article_links_list.append(article_link)
                article_author_links_list.append(article_author_link)
            artauthlink_rep = count_repetitions([extract_author_name(link) for link in article_author_links_list])
            article_author_links_list = filter_aliases(article_author_links_list, artauthlink_rep)
            article_links_list = [link.split('#')[0] for link in article_links_list]
            article_author_links_list = [link.split('#')[0] for link in article_author_links_list]
            for article in article_links_list:
                print(article)
            for author in article_author_links_list:
                print(author)
            # storage_state = await context.storage_state(path='state.json')
            articles_semaphore = asyncio.Semaphore(1)
            authors_semaphore = asyncio.Semaphore(1)
            articles_tasks_to_exec = [run_task_article(link, index+1, articles_semaphore) for index, link in enumerate(article_links_list)]
            authors_tasks_to_exec = [run_task_author(link, index+1, authors_semaphore) for index, link in enumerate(article_author_links_list)]

            # temporarily shadowed to collect and test the authors
            await asyncio.gather(*articles_tasks_to_exec, return_exceptions=True)

            articles_csv_file = "articles_output.csv"
            logger.info('saving the articles csv')
            with open(articles_csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=articles_parsed_list[0].keys())
                writer.writeheader()
                for data in articles_parsed_list:
                    writer.writerow(data)


            # temp shadowed to collect the articles
            # await asyncio.gather(*authors_tasks_to_exec, return_exceptions=True)
            #
            # authors_csv_file = 'authors_output.csv'
            # logger.info('saving the authors csv')
            # with open(authors_csv_file, mode='w', newline='', encoding='utf-8') as file:
            #     writer = csv.DictWriter(file, fieldnames=authors_parsed_list[0].keys())
            #     writer.writeheader()
            #     for data in authors_parsed_list:
            #         writer.writerow(data)

    except Exception as e:
        logger.error(f'some global error in the initscript: {e}')
        # global retry_init_failure_count
        # while retry_init_failure_count < 5:
        #     fetch_anticaptchacom_solved_obj.solve_obj('https://seekingalpha.com/latest-articles', seek_alpha_login, seek_alpha_pswd)
        #     retry_init_failure_count =+ 1
        #     await init_script()



async def main():
    await init_script()


if __name__ == "__main__":
    asyncio.run(main())