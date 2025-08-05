import google.generativeai as genai
import os
import logging
import json
import pandas as pd
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class EmailWriter:
    def __init__(self):
        """Initialize the EmailWriter with Gemini AI configuration"""
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Configure Gemini AI
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        genai.configure(api_key=api_key)
        
        # Initialize the model with updated name
        try:
            # Try the new model names first
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Using gemini-1.5-flash model")
        except Exception:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                self.logger.info("Using gemini-1.5-pro model")
            except Exception:
                try:
                    self.model = genai.GenerativeModel('gemini-pro')
                    self.logger.info("Using gemini-pro model")
                except Exception as e:
                    # List available models and show error
                    self.logger.error("Failed to initialize any model. Available models:")
                    try:
                        for model in genai.list_models():
                            if 'generateContent' in model.supported_generation_methods:
                                self.logger.info(f"  - {model.name}")
                    except Exception:
                        pass
                    raise ValueError(f"Could not initialize Gemini model: {str(e)}")
        
        # Company information for better personalization
        self.company_insights = {
            'Paytm': {
                'business': 'Digital payments and financial services',
                'key_products': 'Paytm Wallet, UPI payments, Paytm Mall',
                'recent_news': 'Leading digital payments platform in India',
                'culture': 'Innovation-focused, customer-centric'
            },
            'Razorpay': {
                'business': 'Payment gateway and financial services',
                'key_products': 'Payment gateway, RazorpayX, Capital',
                'recent_news': 'Unicorn status, expanding to Southeast Asia',
                'culture': 'Developer-first, transparency, growth mindset'
            },
            'PhonePe': {
                'business': 'Digital payments and financial services',
                'key_products': 'UPI payments, Switch platform, insurance',
                'recent_news': 'Market leader in UPI transactions',
                'culture': 'Innovation, inclusion, customer obsession'
            },
            'Zerodha': {
                'business': 'Online stock brokerage',
                'key_products': 'Kite trading platform, Coin, Varsity',
                'recent_news': 'Largest retail broker in India',
                'culture': 'Bootstrapped, customer-first, tech-driven'
            },
            'CRED': {
                'business': 'Credit card management and rewards',
                'key_products': 'CRED app, CRED Pay, CRED Cash',
                'recent_news': 'Premium customer base, high engagement',
                'culture': 'Design-focused, premium experience, trust'
            },
            'BharatPe': {
                'business': 'Merchant payments and lending',
                'key_products': 'QR code payments, POS devices, loans',
                'recent_news': 'Expanding merchant network rapidly',
                'culture': 'Merchant-first, aggressive growth, innovation'
            }
        }
        
        # User profile for personalization - UPDATE FOR INTERNSHIP
        self.user_profile = {
            'name': os.getenv('SENDER_NAME', 'Your Name'),
            'year': os.getenv('USER_YEAR', 'Third year'),
            'experience': os.getenv('USER_EXPERIENCE', '1+ years of project experience'),
            'skills': os.getenv('USER_SKILLS', 'Python, Machine Learning, Data Analysis'),
            'current_role': os.getenv('CURRENT_ROLE', 'Computer Science Student'),
            'education': os.getenv('EDUCATION', 'B.Tech Computer Science'),
            'achievements': os.getenv('ACHIEVEMENTS', 'Led multiple successful projects'),
            'graduation_year': os.getenv('GRADUATION_YEAR', '2026')
        }

    def write_personalized_email(self, 
                                contact_info: Dict, 
                                email_type: str = 'internship_application',
                                internship_type: str = None,
                                additional_context: str = None) -> Dict:
        """
        Write a personalized internship email using Gemini AI
        """
        
        try:
            # Get company insights
            company_data = self.company_insights.get(
                contact_info.get('company', ''), 
                {'business': 'Technology and financial services', 'culture': 'Innovation-focused'}
            )
            
            # Create a simplified prompt
            prompt = self._create_simple_prompt(
                contact_info=contact_info,
                email_type=email_type,
                internship_type=internship_type,
                company_data=company_data
            )
            
            # Generate email using Gemini
            response = self.model.generate_content(prompt)
            email_content = response.text
            
            # Parse the response to extract subject and body
            parsed_email = self._parse_email_response(email_content)
            
            # Add metadata
            parsed_email.update({
                'generated_at': datetime.now().isoformat(),
                'recipient': contact_info.get('name', 'Hiring Manager'),
                'company': contact_info.get('company', 'Company'),
                'email_type': email_type,
                'internship_type': internship_type,
                'confidence_score': self._calculate_confidence_score(parsed_email)
            })
            
            self.logger.info(f"Generated {email_type} email for internship at {contact_info.get('company', 'Unknown Company')}")
            
            return parsed_email
            
        except Exception as e:
            self.logger.error(f"Error generating email: {str(e)}")
            return {
                'subject': f"Internship Application - {internship_type or 'Software Development'} at {contact_info.get('company', 'Your Company')}",
                'body': self._get_fallback_internship_email(contact_info, email_type, internship_type),
                'error': str(e)
            }

    def _create_simple_prompt(self, contact_info: Dict, email_type: str, internship_type: str, company_data: Dict) -> str:
        """Create a simplified prompt that works better with Gemini"""
        
        recipient_name = contact_info.get('name', 'Hiring Manager')
        company_name = contact_info.get('company', 'the company')
        
        prompt = f"""Write a professional internship application email.

STUDENT DETAILS:
- Name: {self.user_profile['name']}
- Status: {self.user_profile['current_role']}
- Year: {self.user_profile['year']}
- Skills: {self.user_profile['skills']}
- Graduation: {self.user_profile['graduation_year']}

RECIPIENT:
- Name: {recipient_name}
- Company: {company_name}
- Business: {company_data.get('business', 'Technology services')}

INTERNSHIP TYPE: {internship_type or 'Software Development Intern'}

Write a 150-200 word email that:
1. Greets {recipient_name} professionally
2. Introduces the student seeking internship
3. Mentions specific interest in {company_name}
4. Highlights relevant skills and projects
5. Shows eagerness to learn
6. Requests opportunity to discuss
7. Ends professionally

Format the response EXACTLY like this:
SUBJECT: [Your subject line here]

BODY:
[Your email body here]

Make it personal, enthusiastic, and professional. Focus on learning opportunity."""

        return prompt

    def _parse_email_response(self, email_content: str) -> Dict:
        """Parse Gemini's response to extract subject and body - IMPROVED"""
        
        try:
            content = email_content.strip()
            
            # Initialize variables
            subject = ""
            body = ""
            
            # Split into lines and find SUBJECT and BODY sections
            lines = content.split('\n')
            
            subject_found = False
            body_found = False
            body_lines = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for SUBJECT line
                if line.upper().startswith('SUBJECT:'):
                    subject = line[8:].strip()  # Remove "SUBJECT:"
                    subject_found = True
                    continue
                
                # Look for BODY line
                if line.upper().startswith('BODY:'):
                    body_found = True
                    # Collect all lines after BODY:
                    body_lines = [l.strip() for l in lines[i+1:] if l.strip()]
                    break
            
            # If structured parsing worked
            if subject_found and body_found:
                body = '\n\n'.join(body_lines)
            else:
                # Fallback parsing
                all_lines = [line.strip() for line in lines if line.strip()]
                
                if all_lines:
                    # First non-empty line as subject if it's reasonably short
                    if len(all_lines[0]) < 100:
                        subject = all_lines[0]
                        body_lines = all_lines[1:]
                    else:
                        subject = "Software Development Internship Application"
                        body_lines = all_lines
                    
                    body = '\n\n'.join(body_lines)
            
            # Clean up
            subject = subject.replace('**', '').replace('*', '').strip('"\'')
            body = body.replace('**', '').replace('*', '')
            
            # Ensure we have content
            if not subject:
                subject = "Software Development Internship Application"
            
            if not body or len(body) < 50:
                # Use fallback if body is too short
                body = self._get_fallback_internship_email({}, 'internship_application', 'Software Development')
            
            return {
                'subject': subject,
                'body': body
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing email response: {str(e)}")
            return {
                'subject': "Internship Application",
                'body': email_content if email_content else "Failed to generate email content."
            }

    def _calculate_confidence_score(self, email_data: Dict) -> float:
        """Calculate a confidence score for the generated email"""
        
        score = 0.5  # Base score
        
        # Check email length
        word_count = len(email_data.get('body', '').split())
        if 120 <= word_count <= 250:
            score += 0.2
        elif 80 <= word_count <= 300:
            score += 0.1
        
        # Check if subject line is reasonable length
        subject_len = len(email_data.get('subject', ''))
        if 10 <= subject_len <= 80:
            score += 0.1
        
        # Check for internship-specific indicators
        body = email_data.get('body', '').lower()
        internship_words = ['intern', 'learning', 'student', 'academic', 'project', 'course']
        if any(word in body for word in internship_words):
            score += 0.1
        
        # Check for call-to-action
        if any(phrase in body for phrase in ['discuss', 'chat', 'connect', 'meeting', 'opportunity']):
            score += 0.1
        
        return min(score, 1.0)

    def _get_fallback_internship_email(self, contact_info: Dict, email_type: str, internship_type: str) -> str:
        """Fallback email template if AI generation fails"""
        
        recipient_name = contact_info.get('name', 'Hiring Manager')
        company_name = contact_info.get('company', 'your company')
        
        return f"""Dear {recipient_name},

I hope this email finds you well. I am {self.user_profile['name']}, a {self.user_profile['year']} {self.user_profile['education']} student, writing to express my strong interest in software internship opportunities at {company_name}.

With {self.user_profile['experience']} and skills in {self.user_profile['skills']}, I am eager to gain hands-on industry experience and contribute to {company_name}'s innovative projects in the fintech space.

I am particularly excited about the opportunity to learn from your team and contribute to your mission while developing my technical skills in a real-world environment.

I would be grateful for the opportunity to discuss how my academic background and passion for technology align with your internship programs.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,
{self.user_profile['name']}
{self.user_profile['current_role']}
Expected Graduation: {self.user_profile['graduation_year']}"""

    def generate_bulk_internship_emails(self, contacts_csv: str, email_type: str = 'internship_application', 
                                      internship_type: str = 'Software Development Intern') -> List[Dict]:
        """Generate internship emails for multiple contacts from a CSV file"""
        
        try:
            # Read contacts from CSV
            df = pd.read_csv(contacts_csv)
            self.logger.info(f"Loaded {len(df)} contacts from {contacts_csv}")
            
            generated_emails = []
            
            for index, contact in df.iterrows():
                self.logger.info(f"Generating internship email {index + 1}/{len(df)} for {contact.get('company', 'Unknown')}")
                
                contact_info = {
                    'name': contact.get('name', 'Hiring Manager'),
                    'company': contact.get('company', 'Company'),
                    'title': contact.get('title', 'HR Professional'),
                    'email': contact.get('email', ''),
                    'linkedin_url': contact.get('linkedin_url', '')
                }
                
                email_data = self.write_personalized_email(
                    contact_info=contact_info,
                    email_type=email_type,
                    internship_type=internship_type
                )
                
                # Add contact info to email data
                email_data.update(contact_info)
                generated_emails.append(email_data)
                
                # Rate limiting to be respectful to the API
                import time
                time.sleep(3)  # 3 second delay between requests
                
                # Progress indicator
                if (index + 1) % 5 == 0:
                    self.logger.info(f"Completed {index + 1}/{len(df)} emails...")
            
            # Save generated emails
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"internship_emails_{timestamp}.csv"
            filepath = self._save_generated_emails(generated_emails, filename)
            
            self.logger.info(f"✅ Successfully generated {len(generated_emails)} internship emails")
            self.logger.info(f"📁 Emails saved to: {filepath}")
            
            return generated_emails
            
        except Exception as e:
            self.logger.error(f"Error generating bulk internship emails: {str(e)}")
            return []

    def _save_generated_emails(self, emails: List[Dict], filename: str = None):
        """Save generated emails to CSV"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_emails_{timestamp}.csv"
        
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(emails)
        df.to_csv(filepath, index=False)
        
        self.logger.info(f"Saved {len(emails)} generated emails to {filepath}")
        return filepath

# Example usage and testing
if __name__ == "__main__":
    
    # Initialize email writer
    writer = EmailWriter()
    
    # Test with a sample contact for INTERNSHIP
    sample_contact = {
        'name': 'Priya Sharma',
        'company': 'Razorpay',
        'title': 'Senior Talent Acquisition Manager',
        'email': 'priya.sharma@razorpay.com'
    }
    
    print("🚀 Testing Internship Email Writer with Gemini AI")
    print("=" * 50)
    
    # Test internship application email
    print("\n📧 Generating Internship Application Email...")
    internship_email = writer.write_personalized_email(
        contact_info=sample_contact,
        email_type='internship_application',
        internship_type='Software Development Intern'
    )
    
    print(f"\nSubject: {internship_email['subject']}")
    print(f"\nBody:\n{internship_email['body']}")
    print(f"\nConfidence Score: {internship_email.get('confidence_score', 'N/A')}")
    
    # Test internship inquiry email
    print("\n" + "=" * 50)
    print("\n📧 Generating Internship Inquiry Email...")
    inquiry_email = writer.write_personalized_email(
        contact_info=sample_contact,
        email_type='internship_inquiry'
    )
    
    print(f"\nSubject: {inquiry_email['subject']}")
    print(f"\nBody:\n{inquiry_email['body']}")
    print(f"\nConfidence Score: {inquiry_email.get('confidence_score', 'N/A')}")