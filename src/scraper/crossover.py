from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class CrossoverScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Crossover Search URL
        # https://www.crossover.com/jobs?q=Python
        # Crossover is extremely specific, URL might be different
        url = f"https://www.crossover.com/jobs"
        logger.info(f"Navigating to Crossover: {url}")
        
        await self.navigate(url)
        await human_delay(4.0, 7.0)
        
        jobs = []
        try:
             # Crossover is heavy SPA
            # Try to search if input exists
            try:
                await self.page.locator("input[placeholder='Search jobs']").fill(role)
                await self.page.keyboard.press("Enter")
                await human_delay(3.0, 5.0)
            except:
                logger.warning("Could not perform search on Crossover, scraping default list")
            
            await scroll_page(self.page, steps=3)
            
            # Job cards
            # div.job-card
            cards = await self.page.locator("div.job-card").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Crossover")

            for card in cards:
                try:
                    title_el = card.locator("div.job-card-title").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = "Crossover / Client"
                    
                    # Link
                    link_el = card.locator("a").first
                    link = await link_el.get_attribute("href")
                    
                    full_link = f"https://www.crossover.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": "Remote",
                        "url": full_link,
                        "source": "Crossover"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Crossover: {e}")
            
        return jobs
