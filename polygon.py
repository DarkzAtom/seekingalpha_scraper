import asyncio
import random
import time
from asyncio import timeout

from undetected_playwright.async_api import async_playwright, expect, Playwright
from playwright_stealth import stealth_async, StealthConfig
import json
import logging
from datetime import date
from collections import Counter
import re
import pyautogui
import random
import datetime
import fetch_anticaptchacom_solved_obj
import csv
from main import run_task_author, run_task_article
from main import setup_browser_context



logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),  # Write logs to a file
        logging.StreamHandler()  # Print logs to the console
    ]
)
logger = logging.getLogger(__name__)

test_link = 'https://seekingalpha.com/article/4732314-meta-stock-ai-train-isnt-slowing-down-anytime-soon'







async def polygon_main():
    test_semaphore = asyncio.Semaphore(1)
    await run_task_article(test_link, 1, test_semaphore)

if __name__ == '__main__':
    asyncio.run(polygon_main())