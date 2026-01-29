from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class RemoteCoScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        mongo_writer = kwargs.get("mongo_writer")
        category = kwargs.get("category", "")
        
        # Remote.co Search URL
        base_url = f"https://remote.co/remote-jobs/search?searchkeyword={role.replace(' ', '+')}&joblocations=USA%2C%20null%2C%20%40%40%40%2C%208anywhere&us=1"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            url = f"{base_url}&page={current_page}" if current_page > 1 else base_url
            
            logger.info(f"Navigating to Remote.co page {current_page}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.warning(f"Remote.co navigation failed: {e}")
                break
                
            await human_delay(3.0, 5.0)
            
            try:
                jobs = await self._scrape_current_page(current_page)
                
                if jobs:
                    for job in jobs:
                        job["category"] = category
                    
                    if mongo_writer:
                        mongo_writer.upsert_jobs(jobs)
                        logger.success(f"Saved {len(jobs)} jobs from page {current_page} to MongoDB")
                    
                    all_jobs.extend(jobs)
                    logger.info(f"Extracted {len(jobs)} jobs from Remote.co page {current_page}")
                else:
                    logger.info("No jobs found on this page, stopping.")
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping page {current_page}: {e}")
                break
            
            current_page += 1
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from Remote.co: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        seen_urls = set()
        try:
            await scroll_page(self.page, steps=10)
            
            # Based on screenshot: Job titles are links like "Senior DevOps Engineer"
            # They appear in article elements with the job title as a heading
            
            # Get all links on the page first
            all_links = await self.page.locator("a").all()
            logger.debug(f"Total links on page: {len(all_links)}")
            
            for link_el in all_links:
                try:
                    href = await link_el.get_attribute("href")
                    text = await link_el.text_content()
                    
                    if not href or not text:
                        continue
                    
                    text = text.strip()
                    
                    # Skip short text, navigation links, and common non-job text
                    if len(text) < 10:
                        continue
                    
                    skip_keywords = [
                        'next', 'previous', 'page', 'search', 'filter', 'home', 
                        'log in', 'sign', 'register', 'resources', 'companies',
                        'remote jobs', 'get started', 'grow remotely', 'navigate',
                        'read more', 'view all', 'load more', 'cookie', 'privacy',
                        'terms', 'contact', 'about', 'blog', 'help', 'faq'
                    ]
                    
                    if any(skip in text.lower() for skip in skip_keywords):
                        continue
                    
                    # Check if this looks like a job title (contains job-related words or is a proper title)
                    job_indicators = [
                        'engineer', 'developer', 'manager', 'analyst', 'designer',
                        'architect', 'lead', 'senior', 'junior', 'specialist',
                        'coordinator', 'director', 'consultant', 'administrator',
                        'devops', 'backend', 'frontend', 'full stack', 'software',
                        'data', 'cloud', 'security', 'qa', 'test', 'mobile', 'ios',
                        'android', 'python', 'java', 'react', 'node', 'aws', 'azure'
                    ]
                    
                    is_job_title = any(indicator in text.lower() for indicator in job_indicators)
                    
                    if not is_job_title:
                        continue
                    
                    # Make full URL
                    if not href.startswith("http"):
                        full_link = f"https://remote.co{href}"
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
                        "location": "Remote - USA",
                        "url": full_link,
                        "source": "Remote.co",
                        "page": page_num
                    })
                    
                except Exception as e:
                    continue
            
            logger.info(f"Extracted {len(jobs)} jobs from Remote.co page {page_num}")
                    
        except Exception as e:
            logger.error(f"Error scraping Remote.co page {page_num}: {e}")
            
        return jobs
