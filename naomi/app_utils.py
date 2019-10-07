# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request
import re
from pytz import timezone
import logging
from naomi import profile


def send_email(
    SUBJECT,
    BODY,
    TO,
    FROM,
    SENDER,
    PASSWORD,
    SMTP_SERVER,
    SMTP_PORT
):
    """Sends an HTML email."""

    msg = MIMEMultipart()
    msg['From'] = SENDER
    msg['To'] = TO
    msg['Subject'] = SUBJECT

    msg.attach(MIMEText(BODY.encode('UTF-8'), 'html', 'UTF-8'))

    logging.info('using %s, and %s as port', SMTP_SERVER, SMTP_PORT)

    session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

    session.starttls()

    session.login(FROM, PASSWORD)
    session.sendmail(SENDER, TO, msg.as_string())
    session.quit()
    logging.info('Successful.')


def email_user(SUBJECT="", BODY=""):
    """
    sends an email.

    Arguments:
        SUBJECT -- subject line of the email
        BODY -- body text of the email
    """
    if not BODY:
        return False

    body = 'Hello {},'.format(profile.get(['first_name']))
    body += '\n\n' + BODY.strip() + '\n\n'
    body += 'Best Regards,\nNaomi\n'

    recipient = None

    if profile.get(['email', 'address']):
        recipient = profile.get(['email', 'address'])
        first_name = profile.get(['first_name'])
        last_name = profile.get(['last_name'])
        if first_name and last_name:
            recipient = "{first_name} {last_name} <{recipient}>".format(
                first_name=first_name,
                last_name=last_name,
                recipient=recipient
            )
    else:
        phone_number = profile.get(['phone_number'])
        carrier = profile.get(['carrier'])
        if phone_number and carrier:
            recipient = "{}@{}".format(
                str(phone_number),
                carrier
            )

    if not recipient:
        return False

    try:
        user = profile.get(['email', 'username'])
        password = profile.get_profile_password(['email', 'password'])
        server = profile.get(['email', 'smtp'])
        port = profile.get(['email', 'smtp_port'], 587)

        send_email(
            SUBJECT,
            body,
            recipient,
            user,
            "Naomi <naomi>",
            password,
            server,
            port
        )

    except Exception:
        return False
    else:
        return True


def get_timezone():
    """
    Returns the pytz timezone for a given profile.

    Arguments: None
    """
    return timezone(profile.get(['timezone']))


def generate_tiny_URL(URL):
    """
    Generates a compressed URL.

    Arguments:
        URL -- the original URL to-be compressed
    """
    target = "http://tinyurl.com/api-create.php?url=" + URL
    response = urllib_request.urlopen(target)  # nosec
    return response.read()


def is_negative(phrase):
    """
    Returns True if the input phrase has a negative sentiment.

    Arguments:
        phrase -- the input phrase to-be evaluated
    """
    return bool(re.search(r'\b(no(t)?|don\'t|stop|end|n)\b', phrase,
                          re.IGNORECASE))


def is_positive(phrase):
    """
        Returns True if the input phrase has a positive sentiment.

        Arguments:
        phrase -- the input phrase to-be evaluated
    """
    return bool(re.search(r'\b(sure|yes|yeah|go|yup|y)\b',
                          phrase,
                          re.IGNORECASE))
