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
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

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
        
        html = "<h2>Stock Analysis Insights</h2>"
        html += "<table border='1' cellspacing='0' cellpadding='5'>"
        html += "<tr><th>Score</th><th>Sentiment</th><th>Snippet</th></tr>"
        
        for insight in insights:
            score = insight.get('likelihood_score', 0)
            color = "green" if score > 0 else "red"
            html += f"<tr>"
            html += f"<td style='color:{color};'><b>{score:.1f}</b></td>"
            html += f"<td>{insight.get('sentiment_score', 0):.2f}</td>"
            html += f"<td>{insight.get('snippet', '')}</td>"
            html += "</tr>"
        
        html += "</table>"
        return html
