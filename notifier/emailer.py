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

    def format_results(self, insights):
        if not insights:
            return "No high-value insights found."
        
        greeting = "<p>Hello financial trader,<br>Are you ready to make some $$$ tday?</p>"
        html = greeting + "<h2>Stock Analysis Insights</h2>"
        html += "<table border='1' cellspacing='0' cellpadding='5'>"
        html += "<tr><th>Score</th><th>Sentiment</th><th>Snippet</th></tr>"
        
        for insight in insights:
            score = insight.get('likelihood_score', 0)
            color = "green" if score > 0 else "red"
            html += f"<tr>"
            html += f"<td style='color:{color};'><b>{score:.1f}</b></td>"
            html += f"<td>{insight.get('sentiment_score', 0):.2f}</td>"
            snippet = insight.get('snippet', '')
            source_url = insight.get('source_url', '#')
            html += f"<td>{snippet}<br><br><a href='{source_url}'>Check it out</a></td>"
            html += "</tr>"
        
        html += "</table>"
        return html
