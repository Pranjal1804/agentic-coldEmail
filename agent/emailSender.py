import os
import base64
import json
import logging
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime
import time

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import load_dotenv
load_dotenv()

class GmailEmailSender:
    def __init__(self):
        """Initialize Gmail API email sender"""
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Gmail API scopes
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        
        # Initialize Gmail service
        self.service = self._authenticate_gmail()
        
        # Sender information
        self.sender_name = os.getenv('SENDER_NAME', 'Your Name')
        self.sender_email = os.getenv('SENDER_EMAIL', 'your.email@gmail.com')
        
        # Email tracking
        self.sent_emails = []
        self.failed_emails = []
        
        # Rate limiting settings
        self.emails_per_minute = 5  # Conservative limit
        self.delay_between_emails = 12  # seconds (60/5 = 12)
        
    def _authenticate_gmail(self):
        """Authenticate and return Gmail service object"""
        
        creds = None
        token_file = 'gmail_token.json'
        credentials_file = 'gmail_credentials.json'
        
        # Check if we have saved credentials
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.warning(f"Token refresh failed: {str(e)}")
                    creds = None
            
            if not creds:
                if not os.path.exists(credentials_file):
                    raise FileNotFoundError(
                        f"Gmail credentials file '{credentials_file}' not found. "
                        "Please download it from Google Cloud Console and place it in the project root."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            service = build('gmail', 'v1', credentials=creds)
            self.logger.info("✅ Gmail API authenticated successfully")
            return service
        except Exception as e:
            self.logger.error(f"❌ Failed to build Gmail service: {str(e)}")
            raise
    
    def create_email_message(self, 
                           to_email: str, 
                           subject: str, 
                           body: str, 
                           to_name: str = None,
                           is_html: bool = False) -> Dict:
        """Create an email message"""
        
        try:
            # Create message container
            message = MIMEMultipart('alternative')
            
            # Set headers
            message['From'] = f"{self.sender_name} <{self.sender_email}>"
            message['To'] = f"{to_name} <{to_email}>" if to_name else to_email
            message['Subject'] = subject
            
            # Add custom headers for better deliverability
            message['Reply-To'] = self.sender_email
            message['X-Mailer'] = 'Agentic Cold Email System'
            
            # Create body parts
            if is_html:
                # Convert plain text to simple HTML if needed
                if not body.strip().startswith('<'):
                    html_body = body.replace('\n\n', '</p><p>').replace('\n', '<br>')
                    html_body = f"<html><body><p>{html_body}</p></body></html>"
                else:
                    html_body = body
                
                # Add both plain text and HTML versions
                text_part = MIMEText(self._html_to_text(html_body), 'plain')
                html_part = MIMEText(html_body, 'html')
                
                message.attach(text_part)
                message.attach(html_part)
            else:
                # Plain text only
                text_part = MIMEText(body, 'plain')
                message.attach(text_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            return {
                'raw': raw_message,
                'message_obj': message
            }
            
        except Exception as e:
            self.logger.error(f"Error creating email message: {str(e)}")
            raise
    
    def send_single_email(self, 
                         to_email: str, 
                         subject: str, 
                         body: str, 
                         to_name: str = None,
                         dry_run: bool = False) -> Dict:
        """Send a single email"""
        
        try:
            # Create the email message
            email_data = self.create_email_message(to_email, subject, body, to_name)
            
            if dry_run:
                self.logger.info(f"🧪 DRY RUN - Would send email to {to_email}")
                return {
                    'success': True,
                    'message_id': 'dry_run_id',
                    'recipient': to_email,
                    'subject': subject,
                    'status': 'dry_run'
                }
            
            # Send the email
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': email_data['raw']}
            ).execute()
            
            message_id = sent_message.get('id')
            
            self.logger.info(f"✅ Email sent successfully to {to_email} (ID: {message_id})")
            
            # Track sent email
            sent_info = {
                'success': True,
                'message_id': message_id,
                'recipient': to_email,
                'recipient_name': to_name,
                'subject': subject,
                'sent_at': datetime.now().isoformat(),
                'status': 'sent'
            }
            
            self.sent_emails.append(sent_info)
            return sent_info
            
        except HttpError as e:
            error_details = json.loads(e.content.decode('utf-8'))
            error_message = error_details.get('error', {}).get('message', str(e))
            
            self.logger.error(f"❌ Gmail API error sending to {to_email}: {error_message}")
            
            failed_info = {
                'success': False,
                'recipient': to_email,
                'recipient_name': to_name,
                'subject': subject,
                'error': error_message,
                'failed_at': datetime.now().isoformat(),
                'status': 'failed'
            }
            
            self.failed_emails.append(failed_info)
            return failed_info
            
        except Exception as e:
            self.logger.error(f"❌ Unexpected error sending to {to_email}: {str(e)}")
            
            failed_info = {
                'success': False,
                'recipient': to_email,
                'recipient_name': to_name,
                'subject': subject,
                'error': str(e),
                'failed_at': datetime.now().isoformat(),
                'status': 'failed'
            }
            
            self.failed_emails.append(failed_info)
            return failed_info
    
    def send_bulk_emails(self, 
                        emails_csv: str, 
                        dry_run: bool = True,
                        max_emails: int = None,
                        start_from: int = 0) -> Dict:
        """Send bulk emails from CSV file"""
        
        try:
            # Read emails from CSV
            df = pd.read_csv(emails_csv)
            self.logger.info(f"📧 Loaded {len(df)} emails from {emails_csv}")
            
            # Apply limits
            if start_from > 0:
                df = df.iloc[start_from:]
                self.logger.info(f"⏭️ Starting from email {start_from + 1}")
            
            if max_emails:
                df = df.head(max_emails)
                self.logger.info(f"📊 Limiting to {max_emails} emails")
            
            # Check required columns
            required_columns = ['email', 'subject', 'body']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Send emails with rate limiting
            results = []
            total_emails = len(df)
            
            self.logger.info(f"🚀 Starting to send {total_emails} emails...")
            if dry_run:
                self.logger.info("🧪 DRY RUN MODE - No emails will actually be sent")
            
            for index, row in df.iterrows():
                email_num = index + 1
                
                self.logger.info(f"📤 Sending email {email_num}/{total_emails} to {row.get('company', 'Unknown')}")
                
                # Send email
                result = self.send_single_email(
                    to_email=row['email'],
                    subject=row['subject'],
                    body=row['body'],
                    to_name=row.get('name', ''),
                    dry_run=dry_run
                )
                
                results.append(result)
                
                # Rate limiting (skip on last email)
                if email_num < total_emails:
                    self.logger.info(f"⏳ Waiting {self.delay_between_emails} seconds before next email...")
                    time.sleep(self.delay_between_emails)
                
                # Progress update every 5 emails
                if email_num % 5 == 0:
                    successful = sum(1 for r in results if r.get('success'))
                    self.logger.info(f"📊 Progress: {email_num}/{total_emails} processed, {successful} successful")
            
            # Generate summary
            successful_sends = [r for r in results if r.get('success')]
            failed_sends = [r for r in results if not r.get('success')]
            
            summary = {
                'total_processed': total_emails,
                'successful_sends': len(successful_sends),
                'failed_sends': len(failed_sends),
                'success_rate': len(successful_sends) / total_emails * 100 if total_emails > 0 else 0,
                'dry_run': dry_run,
                'results': results,
                'processed_at': datetime.now().isoformat()
            }
            
            # Save results
            self._save_sending_results(summary, emails_csv)
            
            self.logger.info(f"✅ Bulk email sending completed!")
            self.logger.info(f"📊 Summary: {len(successful_sends)}/{total_emails} sent successfully ({summary['success_rate']:.1f}%)")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Error in bulk email sending: {str(e)}")
            raise
    
    def send_generated_emails(self, 
                            emails_csv: str = None,
                            dry_run: bool = True,
                            max_emails: int = 10) -> Dict:
        """Send emails generated by emailWriter"""
        
        # If no CSV specified, find the latest generated emails
        if not emails_csv:
            emails_csv = self._find_latest_generated_emails()
        
        if not emails_csv or not os.path.exists(emails_csv):
            raise FileNotFoundError("No generated emails CSV file found. Run emailWriter first.")
        
        self.logger.info(f"📧 Sending emails from: {emails_csv}")
        
        return self.send_bulk_emails(
            emails_csv=emails_csv,
            dry_run=dry_run,
            max_emails=max_emails
        )
    
    def _find_latest_generated_emails(self) -> str:
        """Find the latest generated emails CSV file"""
        
        data_dir = "data"
        if not os.path.exists(data_dir):
            return None
        
        # Look for internship emails files
        email_files = [
            f for f in os.listdir(data_dir) 
            if f.startswith('internship_emails_') and f.endswith('.csv')
        ]
        
        if not email_files:
            return None
        
        # Return the most recent file
        latest_file = sorted(email_files)[-1]
        return os.path.join(data_dir, latest_file)
    
    def _save_sending_results(self, summary: Dict, source_csv: str):
        """Save email sending results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        os.makedirs("data/email_results", exist_ok=True)
        
        # Save summary as JSON
        summary_file = f"data/email_results/sending_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed results as CSV
        results_file = f"data/email_results/sending_results_{timestamp}.csv"
        df_results = pd.DataFrame(summary['results'])
        df_results.to_csv(results_file, index=False)
        
        self.logger.info(f"📁 Results saved to:")
        self.logger.info(f"   Summary: {summary_file}")
        self.logger.info(f"   Details: {results_file}")
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        # Simple HTML to text conversion
        import re
        
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        
        # Replace HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_sending_statistics(self) -> Dict:
        """Get statistics about sent emails"""
        
        return {
            'total_sent': len(self.sent_emails),
            'total_failed': len(self.failed_emails),
            'success_rate': len(self.sent_emails) / (len(self.sent_emails) + len(self.failed_emails)) * 100 
                           if (len(self.sent_emails) + len(self.failed_emails)) > 0 else 0,
            'sent_emails': self.sent_emails,
            'failed_emails': self.failed_emails
        }
    
    def test_gmail_connection(self) -> bool:
        """Test Gmail API connection"""
        
        try:
            # Try to get user profile
            profile = self.service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress')
            
            self.logger.info(f"✅ Gmail connection successful!")
            self.logger.info(f"📧 Connected as: {email}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Gmail connection test failed: {str(e)}")
            return False

# Example usage and testing
if __name__ == "__main__":
    
    print("🚀 Testing Gmail Email Sender")
    print("=" * 50)
    
    try:
        # Initialize sender
        sender = GmailEmailSender()
        
        # Test connection
        print("\n🔧 Testing Gmail API connection...")
        if sender.test_gmail_connection():
            print("✅ Gmail API is working!")
        else:
            print("❌ Gmail API connection failed!")
            exit(1)
        
        # Test single email (dry run)
        print("\n📧 Testing single email (DRY RUN)...")
        test_result = sender.send_single_email(
            to_email="test@example.com",
            subject="Test Internship Application",
            body="Dear Hiring Manager,\n\nThis is a test email.\n\nBest regards,\nTest User",
            to_name="Test Recipient",
            dry_run=True
        )
        
        print(f"Result: {test_result}")
        
        # Check for generated emails and offer to send them
        latest_emails = sender._find_latest_generated_emails()
        
        if latest_emails:
            print(f"\n📁 Found generated emails: {latest_emails}")
            
            # Load and show preview
            df = pd.read_csv(latest_emails)
            print(f"📊 Contains {len(df)} emails")
            
            if len(df) > 0:
                print("\n📧 Email preview:")
                for i, row in df.head(2).iterrows():
                    print(f"  {i+1}. To: {row.get('company', 'N/A')} ({row.get('email', 'N/A')})")
                    print(f"     Subject: {row.get('subject', 'N/A')}")
                
                # Ask if user wants to send (dry run)
                send_test = input(f"\n🤔 Run dry-run test with these emails? (y/N): ").strip().lower()
                
                if send_test == 'y':
                    print("\n🧪 Running dry-run test...")
                    
                    result = sender.send_bulk_emails(
                        emails_csv=latest_emails,
                        dry_run=True,
                        max_emails=3
                    )
                    
                    print(f"\n📊 Dry-run Results:")
                    print(f"   Processed: {result['total_processed']}")
                    print(f"   Would send: {result['successful_sends']}")
                    print(f"   Success rate: {result['success_rate']:.1f}%")
        else:
            print("\n❌ No generated emails found.")
            print("💡 Run emailWriter.py first to generate emails.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Make sure you have:")
        print("   1. gmail_credentials.json in project root")
        print("   2. Enabled Gmail API in Google Cloud Console")
        print("   3. Installed required packages: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")