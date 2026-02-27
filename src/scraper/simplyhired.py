from typing import List, Dict
from loguru import logger
from src.scraper.base import BaseScraper
from src.core.utils import human_delay, scroll_page


class SimplyHiredScraper(BaseScraper):
    async def search_jobs(self, role: str, location: str, **kwargs) -> List[Dict]:
        await self.initialize()
        
        max_pages = kwargs.get("max_pages", 10)
        mongo_writer = kwargs.get("mongo_writer")
        category = kwargs.get("category", "")
        
        days_old = kwargs.get("days_old", 30)
        
        # SimplyHired Search URL with proper format
        base_url = f"https://www.simplyhired.com/search?q={role.replace(' ', '+')}&l=United+States&fdb={days_old}"
        
        all_jobs = []
        current_page = 1
        consecutive_failures = 0
        
        while current_page <= max_pages:
            # SimplyHired uses pn= for pagination
            url = f"{base_url}&pn={current_page}"
            
            logger.info(f"Navigating to SimplyHired page {current_page}: {url}")
            
            try:
                await self.navigate(url)
                consecutive_failures = 0
            except Exception as e:
                logger.warning(f"SimplyHired navigation failed on page {current_page}: {e}")
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logger.error("Too many consecutive failures, stopping.")
                    break
                current_page += 1
                await human_delay(3.0, 5.0)
                continue
                
            await human_delay(3.0, 5.0)
            
            try:
                jobs = await self._scrape_current_page(current_page)
                
                # Enrich with category and save IMMEDIATELY
                if jobs:
                    for job in jobs:
                        job["category"] = category
                    
                    # Save to MongoDB after each page
                    if mongo_writer:
                        mongo_writer.upsert_jobs(jobs)
                        logger.success(f"Saved {len(jobs)} jobs from page {current_page} to MongoDB")
                    
                    all_jobs.extend(jobs)
                    logger.info(f"Extracted {len(jobs)} jobs from SimplyHired page {current_page}")
                else:
                    logger.info("No jobs found on this page, stopping.")
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping page {current_page}: {e}")
                break
            
            current_page += 1
            await human_delay(2.0, 4.0)
        
        logger.info(f"Total jobs scraped from SimplyHired: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_current_page(self, page_num: int) -> List[Dict]:
        jobs = []
        seen_urls = set()  # Deduplicate within this page
        try:
            # Full page scroll - 10 steps
            await scroll_page(self.page, steps=10)
            
            # Based on screenshot: job cards are in a list
            cards = await self.page.locator("article, div[data-jobkey], li.css-0").all()
            
            if not cards or len(cards) == 0:
                # Alternative: find by job title links
                title_links = await self.page.locator("a[href*='/job/'], h2 a, h3 a").all()
                logger.info(f"Found {len(title_links)} job links on SimplyHired page {page_num}")
                
                for link_el in title_links:
                    try:
                        title = await link_el.text_content()
                        link = await link_el.get_attribute("href")
                        
                        if not title or len(title.strip()) < 3:
                            continue
                        
                        if not link or "/job/" not in link:
                            continue
                        
                        if not link.startswith("http"):
                            full_link = f"https://www.simplyhired.com{link}"
                        else:
                            full_link = link
                        
                        company = "Unknown"
                        loc = "USA"
                        try:
                            parent = link_el.locator("xpath=ancestor::article | ancestor::div[contains(@data-jobkey,'')]").first
                            if await parent.count() > 0:
                                comp_el = parent.locator("span[data-testid='companyName'], .company").first
                                if await comp_el.count() > 0:
                                    company = await comp_el.text_content()
                                loc_el = parent.locator("span[data-testid='location'], .location").first
                                if await loc_el.count() > 0:
                                    loc = await loc_el.text_content()
                        except:
                            pass
                        
                        # Skip duplicates
                        if full_link in seen_urls:
                            continue
                        seen_urls.add(full_link)
                        
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": loc.strip() if loc else "USA",
                            "url": full_link,
                            "source": "SimplyHired",
                            "page": page_num
                        })
                    except:
                        continue
                
                return jobs
            
            logger.info(f"Found {len(cards)} potential job cards on SimplyHired page {page_num}")

            for card in cards:
                try:
                    title_el = card.locator("a.SerpJob-link, h2 a, a[href*='/job/']").first
                    
                    if await title_el.count() == 0:
                        continue
                    
                    title = await title_el.text_content()
                    
                    if not title or len(title.strip()) < 3:
                        continue
                    
                    company_el = card.locator("span.companyName, span[data-testid='companyName'], .company").first
                    company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                    
                    loc_el = card.locator("span.companyLocation, span[data-testid='location'], .location").first
                    loc = await loc_el.text_content() if await loc_el.count() > 0 else "USA"
                    
                    link = await title_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        full_link = f"https://www.simplyhired.com{link}"
                    else:
                        full_link = link

                    if title and full_link:
                        # Skip duplicates
                        if full_link in seen_urls:
                            continue
                        seen_urls.add(full_link)
                        
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip() if company else "Unknown",
                            "location": loc.strip() if loc else "USA",
                            "url": full_link,
                            "source": "SimplyHired",
                            "page": page_num
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping SimplyHired page {page_num}: {e}")
            
        return jobs
