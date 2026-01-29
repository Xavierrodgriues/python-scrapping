from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class SkipTheDriveScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        mongo_writer = kwargs.get("mongo_writer")
        category = kwargs.get("category", "")
        
        # SkipTheDrive URL format from screenshot
        # URL: skipthedrive.com/page/2/?s=devops+engineer+in+usa
        search_term = role.replace(' ', '+') + "+in+usa"
        base_url = f"https://www.skipthedrive.com/?s={search_term}"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            # First page has no /page/, subsequent pages use /page/2/, /page/3/, etc.
            if current_page == 1:
                url = base_url
            else:
                url = f"https://www.skipthedrive.com/page/{current_page}/?s={search_term}"
            
            logger.info(f"Navigating to SkipTheDrive page {current_page}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"SkipTheDrive navigation failed: {e}")
                break
                
            await human_delay(3.0, 5.0)
            
            try:
                jobs = await self._scrape_current_page(current_page)
                
                if jobs:
                    for job in jobs:
                        job["category"] = category
                    
                    # Save to MongoDB after each page
                    if mongo_writer:
                        mongo_writer.upsert_jobs(jobs)
                        logger.success(f"Saved {len(jobs)} jobs from page {current_page} to MongoDB")
                    
                    all_jobs.extend(jobs)
                    logger.info(f"Extracted {len(jobs)} jobs from SkipTheDrive page {current_page}")
                else:
                    logger.info("No jobs found on this page, stopping.")
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping page {current_page}: {e}")
                break
            
            current_page += 1
            await human_delay(2.0, 3.0)
        
        logger.info(f"Total jobs scraped from SkipTheDrive: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        seen_urls = set()
        try:
            await scroll_page(self.page, steps=10)
            
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
                        'browse categories', 'get updates', 'remote job resources',
                        'email me', 'email address', 'part time', 'full time', 
                        'contract', 'relevance', 'date', 'talroo', 'ads',
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
                        'product', 'marketing', 'sales', 'support', 'customer',
                        'remote', 'work from home'
                    ]
                    
                    is_job_title = any(indicator in text.lower() for indicator in job_indicators)
                    
                    # Check if the URL looks like a job listing
                    is_job_url = '/job/' in href or 'skipthedrive.com/2' in href
                    
                    if not is_job_title and not is_job_url:
                        continue
                    
                    # Skip pagination and search URLs
                    if '/page/' in href or '?s=' in href:
                        continue
                    
                    # Make full URL
                    if not href.startswith("http"):
                        full_link = f"https://www.skipthedrive.com{href}"
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
                        "location": "Remote - USA",
                        "url": full_link,
                        "source": "SkipTheDrive",
                        "page": page_num
                    })
                    
                except Exception as e:
                    continue
            
            logger.info(f"Extracted {len(jobs)} jobs from SkipTheDrive page {page_num}")
                    
        except Exception as e:
            logger.error(f"Error scraping SkipTheDrive page {page_num}: {e}")
            
        return jobs
