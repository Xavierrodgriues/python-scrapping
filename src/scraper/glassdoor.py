from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class GlassdoorScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Glassdoor USA search URL with proper country filter
        # Using locT=N (nation) and locId=1 (USA) in the query parameters
        encoded_role = role.replace(' ', '%20')
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={encoded_role}&locT=N&locId=1&locKeyword=United%20States"
        
        logger.info(f"Navigating to Glassdoor USA: {url}")
        try:
            await self.navigate(url)
        except Exception as e:
            logger.error(f"Glassdoor navigation failed: {e}")
            return []

        await human_delay(3.0, 6.0)
        
        jobs = []
        try:
            # Check for popup and close if possible
            try:
                close_button = self.page.locator("span.SVGInline.modal_closeIcon, button[aria-label='Close'], button.CloseButton").first
                if await close_button.is_visible(timeout=3000):
                    await close_button.click()
                    await human_delay(1.0, 2.0)
            except:
                pass

            await scroll_page(self.page, steps=5)
            
            # Select job cards
            cards = await self.page.locator("li[data-test='jobListing'], div.JobCard, article.job-card").all()
            
            if not cards or len(cards) == 0:
                # Alternative selector
                cards = await self.page.locator("div[data-test='job-card'], li.react-job-listing").all()
            
            logger.info(f"Found {len(cards)} potential job cards on Glassdoor")
            
            for card in cards:
                try:
                    title_el = card.locator("a[data-test='job-title'], a.JobCard_jobTitle, h3 a").first
                    title = await title_el.text_content() if await title_el.count() > 0 else None
                    
                    if not title or len(title.strip()) < 3:
                        continue
                    
                    company_el = card.locator("div.employer-name, span.EmployerProfile_companyName, .employer-name").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    location_el = card.locator("div[data-test='emp-location'], span.JobCard_location, .location").first
                    loc = await location_el.text_content() if await location_el.count() > 0 else "USA"
                    
                    url_el = card.locator("a[data-test='job-title'], a.JobCard_jobTitle, a[href*='/job-listing/']").first
                    link = await url_el.get_attribute("href") if await url_el.count() > 0 else None
                    
                    if link and not link.startswith("http"):
                        full_link = f"https://www.glassdoor.com{link}"
                    else:
                        full_link = link

                    if title and full_link:
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": loc.strip() if loc else "USA",
                            "url": full_link,
                            "source": "Glassdoor"
                        })
                        logger.debug(f"Extracted: {title.strip()} at {company.strip()}")
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Glassdoor: {e}")
            
        return jobs
