from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class PangianScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        mongo_writer = kwargs.get("mongo_writer")
        category = kwargs.get("category", "")
        
        # Pangian URL format from screenshot
        # URL: pangian.com/remote/job-board with search
        search_term = role.replace(' ', '+')
        url = f"https://pangian.com/remote/job-board?search={search_term}&location=us"
        
        logger.info(f"Navigating to Pangian: {url}")
        
        try:
            await self.navigate(url)
        except Exception as e:
            logger.error(f"Pangian navigation failed: {e}")
            return []
            
        await human_delay(3.0, 5.0)
        await scroll_page(self.page, steps=10)
        
        jobs = await self._scrape_current_page()
        
        if jobs:
            for job in jobs:
                job["category"] = category
            
            # Save to MongoDB
            if mongo_writer:
                mongo_writer.upsert_jobs(jobs)
                logger.success(f"Saved {len(jobs)} jobs to MongoDB")
        
        logger.info(f"Total jobs scraped from Pangian: {len(jobs)}")
        return jobs
    
    async def _scrape_current_page(self) -> List[Dict]:
        jobs = []
        seen_urls = set()
        try:
            # Keyword-based job detection
            all_links = await self.page.locator("a").all()
            logger.debug(f"Total links on page: {len(all_links)}")
            
            for link_el in all_links:
                try:
                    href = await link_el.get_attribute("href")
                    text = await link_el.text_content()
                    
                    if not href or not text:
                        continue
                    
                    text = text.strip()
                    
                    # Skip short text and navigation links
                    if len(text) < 10:
                        continue
                    
                    skip_keywords = [
                        'next', 'previous', 'page', 'search', 'filter', 'home', 
                        'log in', 'sign', 'register', 'post a job', 'find a',
                        'upgrade', 'pro', 'menu', 'profile', 'resume', 'career',
                        'companies', 'join', 'secrets', 'blocked', 'customize',
                        'cookie', 'privacy', 'terms', 'contact', 'about'
                    ]
                    
                    if any(skip in text.lower() for skip in skip_keywords):
                        continue
                    
                    # Check if this looks like a job title
                    job_indicators = [
                        'engineer', 'developer', 'manager', 'analyst', 'designer',
                        'architect', 'lead', 'senior', 'junior', 'specialist',
                        'coordinator', 'director', 'consultant', 'administrator',
                        'devops', 'backend', 'frontend', 'full stack', 'software',
                        'data', 'cloud', 'security', 'qa', 'test', 'mobile', 'ios',
                        'android', 'python', 'java', 'react', 'node', 'aws', 'azure',
                        'product', 'marketing', 'sales', 'support', 'customer'
                    ]
                    
                    is_job_title = any(indicator in text.lower() for indicator in job_indicators)
                    
                    # Also check if the URL looks like a job listing
                    is_job_url = '/job/' in href or '/jobs/' in href or '/remote-job/' in href
                    
                    if not is_job_title and not is_job_url:
                        continue
                    
                    # Make full URL
                    if not href.startswith("http"):
                        full_link = f"https://pangian.com{href}"
                    else:
                        full_link = href
                    
                    # Skip if already seen
                    if full_link in seen_urls:
                        continue
                    seen_urls.add(full_link)
                    
                    logger.debug(f"Found job: {text[:50]}... -> {href[:50]}...")
                    
                    jobs.append({
                        "title": text,
                        "company": "Unknown",
                        "location": "Remote - US",
                        "url": full_link,
                        "source": "Pangian"
                    })
                    
                except Exception as e:
                    continue
            
            logger.info(f"Extracted {len(jobs)} jobs from Pangian")
                    
        except Exception as e:
            logger.error(f"Error scraping Pangian: {e}")
            
        return jobs
