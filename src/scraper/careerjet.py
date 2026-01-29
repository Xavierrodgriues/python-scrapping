from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class CareerjetScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Careerjet Search URL
        # https://www.careerjet.com/search/jobs?s=Python&l=USA
        url = f"https://www.careerjet.com/search/jobs?s={role.replace(' ', '+')}&l={location.replace(' ', '+')}"
        logger.info(f"Navigating to Careerjet: {url}")
        
        await self.navigate(url)
        await human_delay(3.0, 5.0)
        
        jobs = []
        try:
            await scroll_page(self.page, steps=3)
            
            # Job cards
            # article.job
            cards = await self.page.locator("article.job").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Careerjet")

            for card in cards:
                try:
                    title_el = card.locator("h2 a").first
                    company_el = card.locator("p.company").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link = await title_el.get_attribute("href")
                    full_link = f"https://www.careerjet.com{link}" if link and not link.startswith("http") else link

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location,
                        "url": full_link,
                        "source": "Careerjet"
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Careerjet: {e}")
            
        return jobs
