import asyncio
from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class ZipRecruiterScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        # ZipRecruiter Search URL with pagination
        days = kwargs.get("days_old", 30)
        max_pages = kwargs.get("max_pages", 10)
        mongo_writer = kwargs.get("mongo_writer")
        category = kwargs.get("category", "")
        
        base_url = f"https://www.ziprecruiter.com/candidate/search?search={role.replace(' ', '+')}&location=United+States&days={days}"
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            # ZipRecruiter uses ?page= parameter
            url = f"{base_url}&page={current_page}" if current_page > 1 else base_url
            
            logger.info(f"Navigating to ZipRecruiter page {current_page}: {url}")
            
            try:
                await self.navigate(url)
            except Exception as e:
                logger.warning(f"ZipRecruiter navigation timed out or failed: {e}")
                break

            # Handle capturing popup specifically
            await self.handle_blockers()
            
            # Special check for the "email capture" logic
            try:
                content = await self.page.content()
                if "We found" in content and "open positions" in content:
                    logger.info("ZipRecruiter email capture detected. Trying aggressive dismissal.")
                    await self.page.mouse.click(10, 10)
                    await human_delay(1.0, 2.0)
            except:
                pass

            await human_delay(3.0, 5.0)
            
            try:
                jobs = await self._scrape_current_page(current_page)
                
                # Enrich with category and save IMMEDIATELY (like SimplyHired/Adzuna)
                if jobs:
                    for job in jobs:
                        job["category"] = category
                    
                    # Save to MongoDB after each page
                    if mongo_writer:
                        mongo_writer.upsert_jobs(jobs)
                        logger.success(f"Saved {len(jobs)} jobs from page {current_page} to MongoDB")
                    
                    all_jobs.extend(jobs)
                    logger.info(f"Extracted {len(jobs)} jobs from ZipRecruiter page {current_page}")
                else:
                    logger.info("No jobs found on this page, stopping.")
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping page {current_page}: {e}")
                break
            
            current_page += 1
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from ZipRecruiter: {len(all_jobs)}")
        return all_jobs

    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        seen_urls = set()  # Deduplicate within this page
        try:
            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Expanded Job card selectors
            selectors = [
                "article.job_result",
                "div.job_content",
                "div[class*='job_result']", 
                "li.job-listing",
                "article"
            ]
            
            cards = []
            for sel in selectors:
                cards = await self.page.locator(sel).all()
                if cards:
                    logger.debug(f"Matched selector: {sel} with {len(cards)} items")
                    break
            
            logger.info(f"Found {len(cards)} potential job cards on ZipRecruiter page {page_num}")

            for card in cards:
                try:
                    title_el = card.locator("h2, h3, .job_title").first
                    company_el = card.locator(".company_name, .company_location, p.org").first
                    
                    if await title_el.count() == 0:
                        continue
                        
                    title = await title_el.text_content()
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    link_el = card.locator("a.job_link, a").first
                    link = await link_el.get_attribute("href")
                    
                    # Ensure full URL
                    if link and not link.startswith("http"):
                        full_link = f"https://www.ziprecruiter.com{link}"
                    else:
                        full_link = link
                    
                    if title and full_link:
                        # Skip duplicates within this page
                        if full_link in seen_urls:
                            continue
                        seen_urls.add(full_link)
                        
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": "USA", 
                            "url": full_link,
                            "source": "ZipRecruiter",
                            "page": page_num
                        })
                except Exception as e:
                    continue
        except Exception as e:
            logger.error(f"Error scraping ZipRecruiter page {page_num}: {e}")
            
        return jobs
