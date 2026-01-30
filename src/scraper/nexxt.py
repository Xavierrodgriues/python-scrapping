from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class NexxtScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Nexxt Search URL based on screenshot
        # https://www.nexxt.com/jobs/search?soid=1&k=Network+Analyst&l=United+States
        if not location or location.lower() == "usa":
            location = "United States"
            
        url = f"https://www.nexxt.com/jobs/search?soid=1&k={role.replace(' ', '+')}&l={location.replace(' ', '+')}"
        logger.info(f"Navigating to Nexxt: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            # Infinite scroll - start with more steps
            logger.info("Scrolling to load more jobs...")
            await scroll_page(self.page, steps=20)
            
            # Additional wait for lazy loading
            await human_delay(2.0, 3.0)
            
            # Job cards - trying multiple potential selectors based on standard bootstrap/job board layouts
            # Screenshot shows a list layout.
            cards = await self.page.locator("div.list-group-item, div.job-result, div.result-card").all()
            
            # If no cards found with specific classes, try a more generic approach if there are result headers
            if not cards:
                 cards = await self.page.locator("div[class*='job'], div[class*='result']").all()

            logger.info(f"Found {len(cards)} potential job cards on Nexxt")

            for card in cards:
                try:
                    # Title
                    # Looking for the main link which usually acts as title
                    title_el = card.locator("h3 a, h4 a, a.job-title").first
                    if await title_el.count() == 0:
                         # Fallback: look for any link with bold text or specific class
                         title_el = card.locator("a").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    if not title or len(title.strip()) < 3:
                        continue

                    # Company & Location often in the same line or adjacent
                    # Screenshot: "Arcadia Strategy Group LLC • Herndon, VA 20170"
                    # This suggests a single element containing both or two spans
                    subtitle_el = card.locator("div.card-body > div, small, .company-name").first
                    subtitle_text = await subtitle_el.text_content() if await subtitle_el.count() > 0 else ""
                    
                    company = "Unknown"
                    loc = location
                    
                    if "•" in subtitle_text:
                        parts = subtitle_text.split("•")
                        company = parts[0].strip()
                        loc = parts[1].strip()
                    elif subtitle_text:
                         company = subtitle_text.strip()
                    
                    link = await title_el.get_attribute("href")
                    # Usually full or relative
                    full_link = f"https://www.nexxt.com{link}" if link and not link.startswith("http") else link

                    # Validate valid job link
                    if not full_link or "javascript:" in full_link:
                        continue

                    jobs.append({
                        "title": title.strip(),
                        "company": company,
                        "location": loc,
                        "url": full_link,
                        "source": "Nexxt"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Nexxt: {e}")
            
        return jobs
