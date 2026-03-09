import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings

class Emailer:
    def __init__(self):
        self.sender = settings.email_sender
        self.password = settings.email_password
        self.recipient = settings.email_recipient
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port

    def send_email(self, subject, body):
        if not self.sender or not self.password or not self.recipient:
            print("Email configuration missing. Skipping email.")
            return

        try:
            from email.utils import formatdate, make_msgid
            from bs4 import BeautifulSoup

            # Create message container - the correct MIME type is multipart/alternative.
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Stock Analyzer <{self.sender}>"
            msg['To'] = self.recipient
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid()

            # Generate plain text from HTML for fallback
            text_body = "Stock Analysis Report\n\n"
            try:
                soup = BeautifulSoup(body, "html.parser")
                text_body += soup.get_text(separator="\n", strip=True)
            except Exception as e:
                text_body += f"Error generating plain text: {e}\n\nPlease view HTML version."

            # Record the MIME types of both parts - text/plain and text/html.
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(body, 'html')

            # Attach parts into message container.
            # According to RFC 2046, the last part of a multipart message, in this case
            # the HTML message, is best and preferred.
            msg.attach(part1)
            msg.attach(part2)

            if int(self.smtp_port) == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            server.login(self.sender, self.password)
            text = msg.as_string()
            server.sendmail(self.sender, self.recipient, text)
            server.quit()
            print(f"Email sent to {self.recipient}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def format_results(self, pos_insights, neg_insights):
        if not pos_insights and not neg_insights:
            return "No high-value insights found."
            
        import datetime
        from email.utils import formatdate
        
        # Start the wrapper
        html = """
        <div style="background-color: #050505; padding: 24px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
          <!-- Header / Intro -->
          <div style="text-align: center; margin-bottom: 24px;">
            <h2 style="color: #ffffff; margin: 0; font-size: 20px;">Hourly Trade Report</h2>
            <p style="color: #64748b; font-size: 12px; margin-top: 4px;">Live Signal Feed</p>
          </div>
        """
        
        def build_card(insight, is_positive):
            score = insight.get('likelihood_score', 0)
            
            ticker = insight.get('ticker', '')
            if ticker is None or str(ticker).strip().lower() in ['none', 'unknown']:
                ticker = ''
                
            company = insight.get('company', '')
            if company is None or str(company).strip().lower() in ['none', 'unknown']:
                company = ''
                
            snippet = insight.get('snippet', '')
            source_url = insight.get('source_url', '#')
            
            # Remove ticker bracket notation from snippet if present: " [NYSE: AAPL]"
            import re
            clean_snippet = re.sub(r'\s*\[.*?\]$', '', snippet).strip()
            
            # Determine styling based on sentiment
            if is_positive:
                bg_color = "#101e1a" # ~ rgba(16, 185, 129, 0.1) on #0f1115
                border_color = "rgba(16, 185, 129, 0.2)"
                badge_bg = "rgba(16, 185, 129, 0.1)"
                badge_text = "#34d399"
                badge_label = "↗ BULLISH SIGNAL"
                link_color = "#34d399"
            else:
                bg_color = "#26141a" # ~ rgba(244, 63, 94, 0.1) on #0f1115
                border_color = "rgba(244, 63, 94, 0.2)"
                badge_bg = "rgba(244, 63, 94, 0.1)"
                badge_text = "#fb7185"
                badge_label = "↘ BEARISH ALERT"
                link_color = "#fb7185"
                
            # Time formatted nicely (e.g. 09:31 AM EST) - using local time for now
            time_str = datetime.datetime.now().strftime("%I:%M %p")
            
            header_text = ""
            if ticker and company:
                header_text = f'<strong style="color: #ffffff;">${ticker}</strong> {company}'
            elif ticker:
                header_text = f'<strong style="color: #ffffff;">${ticker}</strong>'
            elif company:
                header_text = f'{company}'
                
            header_html = f'<div style="font-size: 16px; color: #e2e8f0; margin-bottom: 6px;">{header_text}</div>' if header_text else ''
            
            card_html = f"""
          <div style="background-color: #0f1115; border: 1px solid {border_color}; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 12px;">
              <tr>
                <td align="left" valign="top">
                  <span style="display: inline-block; background-color: {badge_bg}; color: {badge_text}; font-size: 12px; font-weight: 600; padding: 4px 8px; border-radius: 4px; text-transform: uppercase;">
                    {badge_label}
                  </span>
                </td>
                <td align="right" valign="top" style="font-family: 'Courier New', monospace; font-size: 12px; color: #64748b; text-align: right;">
                  Impact Score: <strong style="color: #e2e8f0;">{abs(score):.0f}/100</strong><br/>
                  {time_str}
                </td>
              </tr>
            </table>
            {header_html}
            <div style="font-size: 13px; color: #94a3b8; line-height: 1.5; margin-bottom: 12px;">
              {clean_snippet}
            </div>
            <a href="{source_url}" style="color: {link_color}; font-size: 12px; text-decoration: none; font-weight: bold;">
              Read Full Source →
            </a>
          </div>
            """
            return card_html
            
        if pos_insights:
            for insight in pos_insights:
                html += build_card(insight, is_positive=True)
                
        if neg_insights:
            for insight in neg_insights:
                html += build_card(insight, is_positive=False)
                
        html += """
        </div>
        """
        
        return html
