import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Set
import os
import json
from dotenv import load_dotenv

load_dotenv()

class RealContactFinder:
    def __init__(self):
        """Initialize the ContactFinder with configuration for real email hunting"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Email regex pattern
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Keywords that indicate recruiter/HR roles
        self.hr_keywords = [
            'recruiter', 'talent acquisition', 'hr', 'human resources',
            'hiring manager', 'talent sourcer', 'recruitment consultant',
            'talent partner', 'people operations', 'head of talent',
            'hr manager', 'hr director', 'people lead', 'talent lead',
            'recruitment', 'staffing', 'talent management', 'campus placement'
        ]
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Store found contacts to avoid duplicates
        self.found_contacts: Set[str] = set()
        
        # Google Custom Search API endpoint
        self.google_search_url = "https://www.googleapis.com/customsearch/v1"
        
        # Known Indian fintech companies with their actual domains
        self.indian_fintech_companies = [
            {'name': 'Paytm', 'domain': 'paytm.com', 'website': 'https://paytm.com'},
            {'name': 'Razorpay', 'domain': 'razorpay.com', 'website': 'https://razorpay.com'},
            {'name': 'PhonePe', 'domain': 'phonepe.com', 'website': 'https://phonepe.com'},
            {'name': 'Zerodha', 'domain': 'zerodha.com', 'website': 'https://zerodha.com'},
            {'name': 'CRED', 'domain': 'cred.club', 'website': 'https://cred.club'},
            {'name': 'BharatPe', 'domain': 'bharatpe.com', 'website': 'https://bharatpe.com'},
            {'name': 'Pine Labs', 'domain': 'pinelabs.com', 'website': 'https://pinelabs.com'},
            {'name': 'Lendingkart', 'domain': 'lendingkart.com', 'website': 'https://lendingkart.com'},
            {'name': 'Cashfree', 'domain': 'cashfree.com', 'website': 'https://cashfree.com'},
            {'name': 'Instamojo', 'domain': 'instamojo.com', 'website': 'https://instamojo.com'},
            {'name': 'Mobikwik', 'domain': 'mobikwik.com', 'website': 'https://mobikwik.com'},
            {'name': 'Capital Float', 'domain': 'capitalfloat.com', 'website': 'https://capitalfloat.com'}
        ]
    
    def google_custom_search(self, query: str, api_key: str, cse_id: str, num: int = 10) -> Dict:
        """
        Perform Google Custom Search API request
        """
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': query,
            'num': min(num, 10),
            'gl': 'in'
        }
        
        try:
            response = requests.get(self.google_search_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Google Search API error: {str(e)}")
            return {}
    
    def find_real_hr_emails(self, api_key: str, cse_id: str, max_companies: int = 6) -> List[Dict]:
        """
        Find real HR emails from Indian fintech companies
        """
        all_contacts = []
        
        # Use predefined companies for better accuracy
        companies = self.indian_fintech_companies[:max_companies]
        
        self.logger.info(f"Processing {len(companies)} Indian fintech companies")
        
        for i, company in enumerate(companies, 1):
            self.logger.info(f"Processing company {i}/{len(companies)}: {company['name']}")
            
            company_contacts = []
            
            # Method 1: Search for specific HR contacts at the company
            search_contacts = self._search_real_hr_contacts(company, api_key, cse_id)
            company_contacts.extend(search_contacts)
            
            # Method 2: Scrape company careers page
            careers_contacts = self._scrape_careers_page(company)
            company_contacts.extend(careers_contacts)
            
            # Method 3: Search for LinkedIn profiles and extract contact info
            linkedin_contacts = self._find_linkedin_hr_contacts(company, api_key, cse_id)
            company_contacts.extend(linkedin_contacts)
            
            # Method 4: Search for job postings with contact info
            job_contacts = self._find_job_posting_contacts(company, api_key, cse_id)
            company_contacts.extend(job_contacts)
            
            # Add company info to contacts
            for contact in company_contacts:
                contact.update({
                    'company': company['name'],
                    'company_domain': company['domain'],
                    'company_website': company['website'],
                    'country': 'india',
                    'industry': 'fintech'
                })
                
            all_contacts.extend(company_contacts)
            
            self.logger.info(f"Found {len(company_contacts)} real contacts for {company['name']}")
            
            # Rate limiting
            time.sleep(3)
            
        return all_contacts
    
    def _search_real_hr_contacts(self, company: Dict, api_key: str, cse_id: str) -> List[Dict]:
        """
        Search for real HR contacts using specific queries
        """
        contacts = []
        
        try:
            # Specific search queries to find real HR contacts
            search_queries = [
                f'"{company["name"]}" HR email contact site:{company["domain"]}',
                f'"{company["name"]}" recruiter email site:{company["domain"]}',
                f'"{company["name"]}" careers contact email',
                f'"{company["name"]}" talent acquisition email',
                f'"{company["name"]}" hiring manager email',
                f'site:{company["domain"]} "careers@" OR "hr@" OR "jobs@" OR "recruitment@"'
            ]
            
            for query in search_queries:
                results = self.google_custom_search(query, api_key, cse_id, num=5)
                
                if 'items' in results:
                    for item in results['items']:
                        snippet = item.get('snippet', '')
                        title = item.get('title', '')
                        link = item.get('link', '')
                        
                        # Find emails in the content
                        all_text = f"{title} {snippet}"
                        emails = self.email_pattern.findall(all_text)
                        
                        for email in emails:
                            if self._is_real_hr_email(email, company['domain']) and email not in self.found_contacts:
                                contact_info = self._extract_contact_details(all_text, email)
                                contacts.append({
                                    'email': email,
                                    'name': contact_info.get('name', ''),
                                    'title': contact_info.get('title', ''),
                                    'source': 'Google Search - Real HR',
                                    'source_url': link,
                                    'confidence': 'high'
                                })
                                self.found_contacts.add(email)
                                
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error searching real HR contacts for {company['name']}: {str(e)}")
            
        return contacts
    
    def _scrape_careers_page(self, company: Dict) -> List[Dict]:
        """
        Scrape company careers page for real HR contacts
        """
        contacts = []
        
        try:
            careers_urls = [
                f"{company['website']}/careers",
                f"{company['website']}/jobs",
                f"{company['website']}/career",
                f"{company['website']}/join-us",
                f"{company['website']}/work-with-us",
                f"{company['website']}/hiring",
                f"{company['website']}/contact"
            ]
            
            for url in careers_urls:
                try:
                    response = self.session.get(url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for contact sections, forms, or email links
                        page_text = soup.get_text()
                        emails = self.email_pattern.findall(page_text)
                        
                        # Also check for mailto links
                        mailto_links = soup.find_all('a', href=re.compile(r'mailto:'))
                        for link in mailto_links:
                            href = link.get('href', '')
                            email_match = re.search(r'mailto:([^?&\s]+)', href)
                            if email_match:
                                emails.append(email_match.group(1))
                        
                        for email in emails:
                            if self._is_real_hr_email(email, company['domain']) and email not in self.found_contacts:
                                # Try to find context around the email
                                context = self._find_email_context_on_page(soup, email)
                                contacts.append({
                                    'email': email,
                                    'name': context.get('name', ''),
                                    'title': context.get('title', ''),
                                    'source': 'Careers Page Scraping',
                                    'source_url': url,
                                    'confidence': 'high'
                                })
                                self.found_contacts.add(email)
                                
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.warning(f"Error scraping {url}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error scraping careers pages for {company['name']}: {str(e)}")
            
        return contacts
    
    def _find_linkedin_hr_contacts(self, company: Dict, api_key: str, cse_id: str) -> List[Dict]:
        """
        Find HR professionals on LinkedIn and try to get their contact info
        """
        contacts = []
        
        try:
            linkedin_query = f'"{company["name"]}" "HR" OR "Talent Acquisition" OR "Recruiter" site:linkedin.com/in india'
            
            results = self.google_custom_search(linkedin_query, api_key, cse_id, num=8)
            
            if 'items' in results:
                for item in results['items']:
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                    linkedin_url = item.get('link', '')
                    
                    # Extract name and title from LinkedIn profile
                    if 'linkedin.com/in' in linkedin_url:
                        name = title.replace(' - LinkedIn', '').replace(' | LinkedIn', '').strip()
                        
                        # Check if it's actually HR related
                        combined_text = f"{title} {snippet}".lower()
                        if any(keyword in combined_text for keyword in self.hr_keywords):
                            
                            # Try to find associated email through additional search
                            email_search_query = f'"{name}" "{company["name"]}" email contact'
                            email_results = self.google_custom_search(email_search_query, api_key, cse_id, num=3)
                            
                            found_email = None
                            if 'items' in email_results:
                                for email_item in email_results['items']:
                                    email_text = f"{email_item.get('title', '')} {email_item.get('snippet', '')}"
                                    emails = self.email_pattern.findall(email_text)
                                    
                                    for email in emails:
                                        if company['domain'] in email or self._is_real_hr_email(email, company['domain']):
                                            found_email = email
                                            break
                                    
                                    if found_email:
                                        break
                            
                            contacts.append({
                                'email': found_email or '',
                                'name': name,
                                'title': self._extract_title_from_linkedin(snippet),
                                'linkedin_url': linkedin_url,
                                'source': 'LinkedIn HR Search',
                                'source_url': linkedin_url,
                                'confidence': 'medium' if found_email else 'low'
                            })
                            
            time.sleep(2)
            
        except Exception as e:
            self.logger.error(f"Error finding LinkedIn HR contacts for {company['name']}: {str(e)}")
            
        return contacts
    
    def _find_job_posting_contacts(self, company: Dict, api_key: str, cse_id: str) -> List[Dict]:
        """
        Search for job postings that might contain HR contact information
        """
        contacts = []
        
        try:
            job_query = f'"{company["name"]}" job posting "contact" "apply" email'
            
            results = self.google_custom_search(job_query, api_key, cse_id, num=5)
            
            if 'items' in results:
                for item in results['items']:
                    snippet = item.get('snippet', '')
                    title = item.get('title', '')
                    link = item.get('link', '')
                    
                    # Look for emails in job postings
                    all_text = f"{title} {snippet}"
                    emails = self.email_pattern.findall(all_text)
                    
                    for email in emails:
                        if self._is_real_hr_email(email, company['domain']) and email not in self.found_contacts:
                            contacts.append({
                                'email': email,
                                'name': '',
                                'title': 'HR Contact (from job posting)',
                                'source': 'Job Posting',
                                'source_url': link,
                                'confidence': 'medium'
                            })
                            self.found_contacts.add(email)
                            
        except Exception as e:
            self.logger.error(f"Error finding job posting contacts for {company['name']}: {str(e)}")
            
        return contacts
    
    def _is_real_hr_email(self, email: str, company_domain: str) -> bool:
        """
        Check if email is a real HR email (not generated)
        """
        email_lower = email.lower()
        
        # Must contain company domain or be from a known HR email pattern
        is_company_email = company_domain in email_lower
        
        # HR indicators
        hr_patterns = ['hr@', 'careers@', 'jobs@', 'talent@', 'recruiting@', 'recruitment@']
        has_hr_pattern = any(pattern in email_lower for pattern in hr_patterns)
        
        # Exclude generic/automated emails
        exclude_patterns = [
            'noreply@', 'no-reply@', 'donotreply@', 'support@', 'info@', 
            'admin@', 'webmaster@', 'hello@', 'contact@', 'sales@'
        ]
        is_excluded = any(pattern in email_lower for pattern in exclude_patterns)
        
        # Check for personal emails (gmail, yahoo, etc.)
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        is_personal = any(domain in email_lower for domain in personal_domains)
        
        return (is_company_email or has_hr_pattern) and not is_excluded and not is_personal
    
    def _extract_contact_details(self, text: str, email: str) -> Dict:
        """
        Extract name and title associated with an email
        """
        details = {'name': '', 'title': ''}
        
        # Look for patterns around the email
        sentences = text.split('.')
        for sentence in sentences:
            if email in sentence:
                # Look for name patterns (Title Case words)
                names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', sentence)
                if names:
                    details['name'] = names[0]
                
                # Look for title patterns
                for keyword in self.hr_keywords:
                    if keyword.lower() in sentence.lower():
                        details['title'] = sentence.strip()[:100]
                        break
                        
        return details
    
    def _find_email_context_on_page(self, soup: BeautifulSoup, email: str) -> Dict:
        """
        Find context around an email on a webpage
        """
        context = {'name': '', 'title': ''}
        
        # Find elements containing the email
        email_elements = soup.find_all(string=re.compile(email))
        
        for element in email_elements:
            # Look at parent elements for context
            current = element.parent
            for _ in range(3):  # Check up to 3 parent levels
                if current:
                    text = current.get_text().strip()
                    
                    # Look for names
                    name_matches = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
                    if name_matches and not context['name']:
                        context['name'] = name_matches[0]
                    
                    # Look for titles
                    for keyword in self.hr_keywords:
                        if keyword.lower() in text.lower() and not context['title']:
                            context['title'] = text[:100]
                            break
                            
                    current = current.parent
                else:
                    break
                    
        return context
    
    def _extract_title_from_linkedin(self, snippet: str) -> str:
        """
        Extract job title from LinkedIn snippet
        """
        # Common patterns in LinkedIn snippets
        title_patterns = [
            r'(HR Manager|Talent Acquisition|Recruiter|Hiring Manager)',
            r'(Head of Talent|People Operations|HR Director)',
            r'(Recruitment|Staffing|Human Resources)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                return match.group(1)
                
        return "HR Professional"
    
    def save_contacts_to_csv(self, contacts: List[Dict], filename: str = None):
        """
        Save real contacts to CSV file
        """
        if not contacts:
            self.logger.warning("No contacts to save")
            return
            
        if not filename:
            timestamp = int(time.time())
            filename = f"real_hr_contacts_{timestamp}.csv"
            
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        
        fieldnames = ['company', 'company_domain', 'industry', 'country', 'name', 'email', 
                     'title', 'linkedin_url', 'source', 'source_url', 'confidence', 'company_website']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for contact in contacts:
                row = {field: contact.get(field, '') for field in fieldnames}
                writer.writerow(row)
                
        self.logger.info(f"Saved {len(contacts)} real contacts to {filepath}")
        return filepath

if __name__ == "__main__":
    finder = RealContactFinder()
    
    # Get API credentials from environment
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
    
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("Error: Please set GOOGLE_API_KEY and GOOGLE_CSE_ID in your .env file")
        exit(1)
    
    print("Searching for REAL HR contacts from Indian fintech companies...")
    print("This will take longer as we're finding actual emails, not generating them.")
    
    # Find real HR contacts
    contacts = finder.find_real_hr_emails(GOOGLE_API_KEY, GOOGLE_CSE_ID, max_companies=6)
    
    # Filter out contacts without real emails
    real_contacts = [c for c in contacts if c.get('email') and '@' in c.get('email', '')]
    
    # Save contacts to CSV
    if real_contacts:
        filepath = finder.save_contacts_to_csv(real_contacts)
        print(f"\nFound {len(real_contacts)} REAL HR contacts!")
        print(f"Contacts saved to: {filepath}")
        
        # Display sample contacts
        print("\nReal HR contacts found:")
        for i, contact in enumerate(real_contacts[:5], 1):
            print(f"\n{i}. Company: {contact.get('company', 'N/A')}")
            print(f"   Name: {contact.get('name', 'N/A')}")
            print(f"   Email: {contact.get('email', 'N/A')}")
            print(f"   Title: {contact.get('title', 'N/A')}")
            print(f"   Source: {contact.get('source', 'N/A')}")
            print(f"   Confidence: {contact.get('confidence', 'N/A')}")
    else:
        print("No real email contacts found. The companies might have strong email protection.")
        print("You might need to use LinkedIn outreach or contact forms instead.")