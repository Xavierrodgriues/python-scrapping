from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class WorkingNomadsScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        mongo_writer = kwargs.get("mongo_writer")
        category = kwargs.get("category", "")
        
        # Working Nomads URL format from screenshot
        # URL: workingnomads.com/jobs?tag=backend-developer&location=north-america
        tag = role.lower().replace(' ', '-')
        url = f"https://www.workingnomads.com/jobs?tag={tag}&location=north-america"
        
        logger.info(f"Navigating to Working Nomads: {url}")
        
        try:
            await self.navigate(url)
        except Exception as e:
            logger.error(f"Working Nomads navigation failed: {e}")
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
        
        logger.info(f"Total jobs scraped from Working Nomads: {len(jobs)}")
        return jobs
    
    async def _scrape_current_page(self) -> List[Dict]:
        jobs = []
        seen_urls = set()
        try:
            # Keyword-based job detection like other scrapers            
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
                        'log in', 'sign', 'register', 'post a job', 'find a job',
                        'remote jobs', 'companies', 'go premium', 'get free',
                        'cookie', 'privacy', 'terms', 'contact', 'about', 
                        'relevance', 'date', 'sort by'
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
                    is_job_url = '/jobs/' in href or '/job/' in href
                    
                    if not is_job_title and not is_job_url:
                        continue
                    
                    # Make full URL
                    if not href.startswith("http"):
                        full_link = f"https://www.workingnomads.com{href}"
                    else:
                        full_link = href
                    
                    # Skip if already seen
                    if full_link in seen_urls:
                        continue
                    seen_urls.add(full_link)
                    
                    # Try to get company from parent element
                    company = "Unknown"
                    try:
                        parent = link_el.locator("xpath=..")
                        company_el = parent.locator("span, .company, p").first
                        if await company_el.count() > 0:
                            comp_text = await company_el.text_content()
                            if comp_text and len(comp_text) < 50:
                                company = comp_text.strip()
                    except:
                        pass
                    
                    logger.debug(f"Found job: {text[:50]}... -> {href[:50]}...")
                    
                    jobs.append({
                        "title": text,
                        "company": company,
                        "location": "Remote - North America",
                        "url": full_link,
                        "source": "Working Nomads"
                    })
                    
                except Exception as e:
                    continue
            
            logger.info(f"Extracted {len(jobs)} jobs from Working Nomads")
                    
        except Exception as e:
            logger.error(f"Error scraping Working Nomads: {e}")
            
        return jobs
