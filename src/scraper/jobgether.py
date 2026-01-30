from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class JobgetherScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        mongo_writer = kwargs.get("mongo_writer")
        category = kwargs.get("category", "")
        
        # Jobgether URL format: jobgether.com/remote-jobs/usa/{role}/{page}
        # Example: jobgether.com/remote-jobs/usa/business-analyst/2
        search_term = role.lower().replace(' ', '-')
        base_url = f"https://jobgether.com/remote-jobs/usa/{search_term}"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            # First page has no page number, subsequent pages use /2, /3, etc.
            if current_page == 1:
                url = base_url
            else:
                url = f"{base_url}/{current_page}"
            
            logger.info(f"Navigating to Jobgether page {current_page}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.error(f"Jobgether navigation failed: {e}")
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
                    logger.info(f"Extracted {len(jobs)} jobs from Jobgether page {current_page}")
                else:
                    logger.info("No jobs found on this page, stopping.")
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping page {current_page}: {e}")
                break
            
            current_page += 1
            await human_delay(2.0, 3.0)
        
        logger.info(f"Total jobs scraped from Jobgether: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        seen_urls = set()
        
        try:
            await scroll_page(self.page, steps=10)
            
            # Look for job cards - based on the screenshot, jobs appear as cards
            # with title, company, location info
            job_cards = await self.page.locator("article, [data-testid*='job'], .job-card, [class*='job-item'], [class*='JobCard']").all()
            
            if not job_cards:
                # Fallback: keyword-based job detection
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
                            'for talent', 'for companies', 'blog', 'about us',
                            'cookie', 'privacy', 'terms', 'contact', 'more...',
                            'operations manager', 'operations specialist', 'apply now',
                            'view similar'
                        ]
                        
                        if any(skip in text.lower() for skip in skip_keywords):
                            continue
                        
                        # Check if URL looks like a job listing
                        if '/offer/' not in href and '/job/' not in href:
                            continue
                        
                        # Skip pagination URLs
                        if href.endswith('/1') or href.endswith('/2') or href.endswith('/3'):
                            if '/remote-jobs/' in href and '/offer/' not in href:
                                continue
                        
                        # Make full URL
                        if not href.startswith("http"):
                            full_link = f"https://jobgether.com{href}"
                        else:
                            full_link = href
                        
                        # Skip if already seen
                        if full_link in seen_urls:
                            continue
                        seen_urls.add(full_link)
                        
                        # Try to get company from nearby elements
                        company = "Unknown"
                        location_text = "Remote - USA"
                        
                        try:
                            parent = link_el.locator("xpath=..")
                            # Try to find company info
                            company_el = parent.locator("span, p, [class*='company']").first
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
                            "location": location_text,
                            "url": full_link,
                            "source": "Jobgether",
                            "page": page_num
                        })
                        
                    except Exception as e:
                        continue
            else:
                # Process job cards
                for card in job_cards:
                    try:
                        # Get job link and title
                        link_el = card.locator("a").first
                        if await link_el.count() == 0:
                            continue
                            
                        href = await link_el.get_attribute("href")
                        title = await link_el.text_content()
                        
                        if not href or not title:
                            continue
                        
                        title = title.strip()
                        
                        # Skip if too short
                        if len(title) < 5:
                            continue
                        
                        # Make full URL
                        if not href.startswith("http"):
                            full_link = f"https://jobgether.com{href}"
                        else:
                            full_link = href
                        
                        # Skip if already seen
                        if full_link in seen_urls:
                            continue
                        seen_urls.add(full_link)
                        
                        # Try to extract company
                        company = "Unknown"
                        try:
                            company_el = card.locator("[class*='company'], span:has-text('Inc'), span:has-text('LLC')").first
                            if await company_el.count() > 0:
                                company = (await company_el.text_content()).strip()
                        except:
                            pass
                        
                        # Try to extract location
                        location_text = "Remote - USA"
                        try:
                            loc_el = card.locator("[class*='location'], :has-text('Remote')").first
                            if await loc_el.count() > 0:
                                loc_text = (await loc_el.text_content()).strip()
                                if loc_text:
                                    location_text = loc_text
                        except:
                            pass
                        
                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": location_text,
                            "url": full_link,
                            "source": "Jobgether",
                            "page": page_num
                        })
                        
                    except Exception as e:
                        continue
            
            logger.info(f"Extracted {len(jobs)} jobs from Jobgether page {page_num}")
                    
        except Exception as e:
            logger.error(f"Error scraping Jobgether page {page_num}: {e}")
            
        return jobs
