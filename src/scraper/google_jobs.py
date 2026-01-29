from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page

class GoogleJobsScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # Google Jobs Immersive View
        # tbs=qdr:m for past month, qdr:w for past week
        time_filter = "qdr:w" if kwargs.get("days_old", 30) <= 7 else "qdr:m"
        url = f"https://www.google.com/search?q={role}+jobs+near+{location}&ibp=htl;jobs&tbs={time_filter}"
        
        logger.info(f"Navigating to Google Jobs: {url}")
        await self.navigate(url)
        await human_delay(2.0, 4.0)
        
        jobs = []
        try:
            # The list of jobs is usually in a scrollable container
            # We need to find the job list items. 
            # In Google Jobs, they are often <li> elements within a <ul> with class 'iFjolb' or similar, but classes generate dynamically.
            # We look for common attributes or structure.
            
            # This selector targets the sidebar items in the immersive view
            cards = await self.page.locator("div.Pwje4b").all() # Common class for job item container in recent UI
            if not cards:
                 cards = await self.page.locator("li").filter(has_text="Apply").all() # Heuristic fallback
            
            logger.info(f"Found {len(cards)} potential job cards on Google Jobs")
            
            for card in cards:
                try:
                    # Click to expand detail? Not strictly necessary for basic info
                    # Extract info directly from list item
                    
                    text = await card.text_content()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    
                    # Heuristic parsing since classes are obfuscated
                    title = lines[0] if lines else "Unknown"
                    company = lines[1] if len(lines) > 1 else "Unknown"
                    loc = lines[2] if len(lines) > 2 else "Unknown"
                    
                    # URL is tricky; usually clicking it updates the right pane.
                    # We might not get a direct link easily without clicking.
                    # For now, we'll store the Google Jobs link or try to find 'data-share-url'
                    
                    # Sometimes there is a 'data-share-url' on the share button, but we have to click to see it.
                    # We will just mark it as "Google Jobs View"
                    
                    link = url # Default to the search page for now
                    
                    if title != "Unknown":
                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": loc,
                            "url": link,
                            "source": "Google Jobs"
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Google Jobs: {e}")
            
        return jobs
