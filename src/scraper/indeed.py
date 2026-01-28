import asyncio
from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class IndeedScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Indeed URL structure
        days = kwargs.get("days_old", 30)
        url = f"https://www.indeed.com/jobs?q={role.replace(' ', '+')}&l={location.replace(' ', '+')}&fromage={days}"
        
        logger.info(f"Navigating to Indeed: {url}")
        await self.browser_manager.navigate(url)
        
        # Wait for potential Cloudflare or Captcha
        try:
            # Check for common blocking titles
            title = await self.page.title()
            if "Cloudflare" in title or "Just a moment" in title:
                logger.warning("Indeed blockage detected (Cloudflare/Captcha). Waiting longer...")
                await human_delay(5.0, 10.0)
        except:
            pass

        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            # Dismiss popup if present
            try:
                await self.page.locator("button[aria-label='close']").click(timeout=2000)
            except:
                pass

            await scroll_page(self.page, steps=3)
            
            # Wait for job cards specifically
            try:
                await self.page.wait_for_selector("div.job_seen_beacon", timeout=5000)
            except:
                logger.warning("No job cards found on Indeed (or selector changed).")
            
            # Select job cards
            cards = await self.page.locator("div.job_seen_beacon").all()
            # Fallback selector
            if not cards:
                cards = await self.page.locator("td.resultContent").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Indeed")
            
            for card in cards:
                try:
                    title_el = card.locator("h2.jobTitle span").first
                    title = await title_el.text_content() if await title_el.count() > 0 else "Unknown Title"
                    
                    company_el = card.locator("[data-testid='company-name']").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown Company"
                    
                    location_el = card.locator("[data-testid='text-location']").first
                    loc = await location_el.text_content() if await location_el.count() > 0 else "Unknown Location"
                    
                    url_el = card.locator("h2.jobTitle a").first
                    link = await url_el.get_attribute("href")
                    full_link = f"https://www.indeed.com{link}" if link and not link.startswith("http") else link
                    
                    if title != "Unknown Title":
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": loc.strip(),
                            "url": full_link,
                            "source": "Indeed"
                        })
                        logger.debug(f"Extracted: {title.strip()} at {company.strip()}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse a job card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
            
        return jobs
