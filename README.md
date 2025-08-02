# 🤖 Agentic Cold Email System

An autonomous agent that finds recruiter contacts, writes personalized cold emails using AI, and manages email campaigns for job seekers targeting Indian fintech companies.

## 🚀 Features

- **Autonomous Contact Discovery**: Finds real HR/recruiter email addresses from company websites
- **AI-Powered Email Generation**: Uses GPT to write personalized cold emails
- **Smart Email Validation**: Filters out generic emails and focuses on real HR contacts
- **Multi-Source Data Collection**: 
  - Web scraping of careers pages
  - Google Custom Search API integration
  - LinkedIn profile analysis
  - Job posting contact extraction
- **Email Campaign Management**: Track sent emails, replies, and bouncebacks
- **Indian Market Focus**: Specialized for Indian fintech companies

## 📋 Prerequisites

- Python 3.8+
- Google Cloud Platform account (for Custom Search API)
- Valid email account for sending (Gmail/SendGrid)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/agentic-coldemail.git
   cd agentic-coldemail
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## 🔑 API Setup

### Google Custom Search API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Custom Search API**
4. Create an **API Key** in Credentials section
5. Set up [Custom Search Engine](https://programmablesearchengine.google.com/):
   - Sites to search: `*` (entire web)
   - Copy your Search Engine ID

### Environment Variables

Create a `.env` file with:

```env
# Google Custom Search API
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id

# OpenAI API (for email generation)
OPENAI_API_KEY=your_openai_api_key

# Email Configuration
SENDER_EMAIL=your_email@domain.com
SENDER_NAME=Your Name

# SendGrid API (optional)
SENDGRID_API_KEY=your_sendgrid_key
```

## 🚀 Quick Start

### 1. Find HR Contacts

```bash
python agent/contactFinder_real.py
```

This will:
- Search for HR contacts at major Indian fintech companies
- Scrape company websites for real email addresses
- Save results to `data/real_hr_contacts_[timestamp].csv`

### 2. Generate Cold Emails

```python
from agent.emailGenerator import EmailGenerator

generator = EmailGenerator()
email_content = generator.generate_personalized_email(
    company_name="Razorpay",
    recipient_name="John Doe",
    recipient_title="HR Manager"
)
```

### 3. Send Email Campaign

```python
from agent.emailSender import EmailSender

sender = EmailSender()
sender.send_campaign_emails("data/real_hr_contacts_123456.csv")
```

## 📁 Project Structure

```
agentic-coldemail/
├── agent/
│   ├── contactFinder_real.py      # Real contact discovery
│   ├── emailGenerator.py          # AI email generation
│   ├── emailSender.py             # Email campaign management
│   └── utils/                     # Utility functions
├── data/                          # Contact databases (gitignored)
├── templates/                     # Email templates
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## 🎯 Target Companies

Currently focuses on major Indian fintech companies:

- **Paytm** - Digital payments leader
- **Razorpay** - Payment gateway solutions
- **PhonePe** - UPI-based payments
- **Zerodha** - Online brokerage
- **CRED** - Credit card management
- **BharatPe** - Merchant payments
- **Pine Labs** - POS solutions
- **Lendingkart** - SME lending
- **Cashfree** - Payment solutions
- **Instamojo** - E-commerce payments

## 📊 Usage Examples

### Find Contacts for Specific Domain

```python
from agent.contactFinder_real import RealContactFinder

finder = RealContactFinder()
contacts = finder.find_real_hr_emails(
    api_key="your_google_api_key",
    cse_id="your_cse_id",
    max_companies=5
)

# Save to CSV
finder.save_contacts_to_csv(contacts)
```

### Batch Email Generation

```python
import pandas as pd
from agent.emailGenerator import EmailGenerator

# Load contacts
df = pd.read_csv('data/real_hr_contacts_123456.csv')

generator = EmailGenerator()

for _, contact in df.iterrows():
    email = generator.generate_personalized_email(
        company_name=contact['company'],
        recipient_name=contact['name'],
        recipient_title=contact['title']
    )
    print(f"Email for {contact['company']}: {email[:100]}...")
```

## 🔒 Privacy & Ethics

### Data Protection
- All contact data is stored locally and gitignored
- No sensitive information is committed to version control
- Respects robots.txt and rate limiting

### Ethical Usage
- ✅ **DO**: Use for legitimate job searching
- ✅ **DO**: Personalize emails and respect recipients
- ✅ **DO**: Follow CAN-SPAM and GDPR guidelines
- ❌ **DON'T**: Spam or send unsolicited bulk emails
- ❌ **DON'T**: Use for marketing unrelated to job seeking
- ❌ **DON'T**: Share or sell collected contact data

## 📈 API Limits & Costs

### Google Custom Search API
- **Free Tier**: 100 searches/day
- **Paid**: $5 per 1,000 additional queries
- **Rate Limit**: 10 QPS

### OpenAI API
- **Usage-based pricing**: ~$0.002 per 1K tokens
- **Rate Limits**: Vary by plan

## 🐛 Troubleshooting

### Common Issues

1. **"400 Bad Request" from Google API**
   ```bash
   # Check your API key and CSE ID in .env file
   # Ensure Custom Search API is enabled
   ```

2. **No contacts found**
   ```bash
   # Companies may have strong email protection
   # Try LinkedIn outreach instead
   # Check if websites are blocking scraping
   ```

3. **Rate limiting errors**
   ```bash
   # Increase sleep time between requests
   # Reduce max_companies parameter
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is designed for legitimate job searching purposes only. Users are responsible for:
- Complying with applicable laws and regulations
- Respecting email marketing guidelines
- Using collected data ethically and responsibly
- Not engaging in spam or unsolicited communications

## 🙏 Acknowledgments

- [Google Custom Search API](https://developers.google.com/custom-search/v1/overview)
- [OpenAI API](https://openai.com/api/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for web scraping
- Indian fintech ecosystem for inspiration

---

**Happy Job Hunting! 🎯**

*Built with ❤️ for the Indian tech community*