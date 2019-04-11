# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request
import re
from pytz import timezone
import logging


def send_email(SUBJECT, BODY, TO, FROM, SENDER, PASSWORD, SMTP_SERVER, SMTP_PORT):
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


def email_user(profile, SUBJECT="", BODY=""):
    """
    sends an email.

    Arguments:
        profile -- contains information related to the user (e.g., email
                   address)
        SUBJECT -- subject line of the email
        BODY -- body text of the email
    """
    if not BODY:
        return False

    body = 'Hello %s,' % profile['first_name']
    body += '\n\n' + BODY.strip() + '\n\n'
    body += 'Best Regards,\nNaomi\n'

    recipient = None


    if profile['email']['address']:
        recipient = profile['email']['address']
        if profile['first_name'] and profile['last_name']:
            first_name=profile['first_name']
            last_name=profile['last_name']
            recipient = "{first_name} {last_name} <{recipient}>".format(
                    first_name=profile['first_name'],
                    last_name=profile['last_name'],
                    recipient=recipient)


    else:
        if profile['carrier'] and profile['phone_number']:
            recipient = "%s@%s" % (
                str(profile['phone_number']),
                profile['carrier'])

    if not recipient:
        return False

    try:
        user = profile['email']['address']
        password = profile['email']['password']
        server = profile['email']['smtp']
        try:
            port = profile ['email']['smtp_port']
        except KeyError:
            port = 587

        send_email(SUBJECT, body, recipient, user,
                   "Naomi <naomi>", password, server, port)

    except Exception:
        return False
    else:
        return True


def get_timezone(profile):
    """
    Returns the pytz timezone for a given profile.

    Arguments:
        profile -- contains information related to the user (e.g., email
                   address)
    """
    try:
        return timezone(profile['timezone'])
    except:
        return None


def generate_tiny_URL(URL):
    """
    Generates a compressed URL.

    Arguments:
        URL -- the original URL to-be compressed
    """
    target = "http://tinyurl.com/api-create.php?url=" + URL
    response = urllib_request.urlopen(target)
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
