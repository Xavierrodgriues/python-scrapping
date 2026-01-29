from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class GlassdoorScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Glassdoor URL often requires specific IDs, but we can try generic search
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={role}&locT=C&locId=0&locKeyword={location}"
        
        logger.info(f"Navigating to Glassdoor: {url}")
        # Glassdoor is extremely aggressive with blocks.
        try:
            await self.navigate(url)
        except Exception as e:
             logger.error(f"Glassdoor navigation failed: {e}")
             return []

        await human_delay(3.0, 6.0)
        
        jobs = []
        try:
            # Check for popup and close if possible (often hard with Playwright on Glassdoor)
            try:
                 close_button = self.page.locator("span.SVGInline.modal_closeIcon").first
                 if await close_button.is_visible(timeout=5000):
                     await close_button.click()
                     await human_delay(1.0, 2.0)
            except:
                pass

            await scroll_page(self.page, steps=3)
            
            # Select job cards - valid as of early 2024, but changes often
            cards = await self.page.locator("li[data-test='jobListing']").all()
            logger.info(f"Found {len(cards)} potential job cards on Glassdoor")
            
            for card in cards:
                try:
                    title_el = card.locator("a[data-test='job-title']").first
                    title = await title_el.text_content() if await title_el.count() > 0 else "Unknown Title"
                    
                    company_el = card.locator("div.employer-name").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown Company"
                    
                    location_el = card.locator("div[data-test='emp-location']").first
                    loc = await location_el.text_content() if await location_el.count() > 0 else "Unknown Location"
                    
                    url_el = card.locator("a[data-test='job-title']").first
                    link = await url_el.get_attribute("href")
                    full_link = f"https://www.glassdoor.com{link}" if link and not link.startswith("http") else link

                    if title != "Unknown Title":
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": loc.strip(),
                            "url": full_link,
                            "source": "Glassdoor"
                        })
                        logger.debug(f"Extracted: {title.strip()} at {company.strip()}")
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Glassdoor: {e}")
            
        return jobs
