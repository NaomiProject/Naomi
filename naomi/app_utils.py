# -*- coding: utf-8 -*-
import email
import imaplib
import smtplib
from dateutil import parser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request
import re
from pytz import timezone
import logging
from naomi import profile


# AaronC - This is currently used to clean phone numbers
def clean_number(s):
    return re.sub(r'[^0-9]', '', s)


def get_date(email):
    return parser.parse(email.get('date'))


def send_email(
    SUBJECT,
    BODY,
    TO,
    SENDER=profile.get(['keyword'], ['Naomi'])[0]
):
    """Sends an HTML email."""

    USERNAME = profile.get_profile_password(['email', 'username'])
    FROM = profile.get_profile_password(['email', 'address'])
    PASSWORD = profile.get_profile_password(['email', 'password'])
    SERVER = profile.get(['email', 'smtp', 'server'])
    PORT = profile.get(['email', 'smtp', 'port'], 587)

    msg = MIMEMultipart()
    msg['From'] = "{} <{}>".format(SENDER, FROM)
    msg['To'] = TO
    msg['Subject'] = SUBJECT
    msg.attach(MIMEText(BODY.encode('UTF-8'), 'html', 'UTF-8'))

    FROM = profile.get_profile_password(['email', 'address'])
    logging.info('using %s, and %s as port', SERVER, PORT)

    session = smtplib.SMTP(SERVER, PORT)

    session.starttls()

    session.login(USERNAME, PASSWORD)
    session.sendmail(SENDER, TO, msg.as_string())
    session.quit()
    logging.info('Successful.')


def email_user(SUBJECT="", BODY=""):
    """
    sends an email to the user.

    Arguments:
        SUBJECT -- subject line of the email
        BODY -- body text of the email
    """
    SENDER = profile.get(['keyword'], ['Naomi'])[0]
    if not BODY:
        return False

    body = 'Hello {},'.format(profile.get(['first_name']))
    body += '\n\n' + BODY.strip() + '\n\n'
    body += 'Best Regards,\n{}\n'.format(SENDER)

    recipient = None

    if profile.get(['email', 'address']):
        recipient = profile.get_profile_password(['email', 'address'])
        first_name = profile.get(['first_name'])
        last_name = profile.get(['last_name'])
        if first_name and last_name:
            recipient = "{first_name} {last_name} <{recipient}>".format(
                first_name=first_name,
                last_name=last_name,
                recipient=recipient
            )
    else:
        phone_number = clean_number(profile.get_profile_password(['phone_number']))
        carrier = profile.get(['carrier'])
        if phone_number and carrier:
            recipient = "{}@{}".format(
                str(phone_number),
                carrier
            )

    if not recipient:
        return False

    try:
        send_email(
            SUBJECT,
            body,
            recipient
        )

    except Exception as e:
        print(e)
        return False
    else:
        return True


def fetch_emails(since=None, filter="", markRead=False, limit=None):
    """
        Fetches a list of unread email objects from a user's Email inbox.

        Arguments:
        since -- if provided, no emails before this date will be returned
        markRead -- if True, marks all returned emails as read in target
                    inbox

        Returns:
        A list of unread email objects.
    """
    host = profile.get_profile_var(['email', 'imap', 'server'])
    port = int(profile.get_profile_var(['email', 'imap', 'port'], "993"))
    conn = imaplib.IMAP4_SSL(host, port)
    conn.debug = 0

    conn.login(
        profile.get_profile_password(['email', 'username']),
        profile.get_profile_password(['email', 'password'])
    )
    conn.select(readonly=(not markRead))

    msgs = []
    (retcode, messages) = conn.search(None, filter)

    if retcode == 'OK' and messages != ['']:
        numUnread = len(messages[0].split(b' '))
        if limit and numUnread > limit:
            return numUnread

        for num in messages[0].split(b' '):
            # parse email RFC822 format
            ret, data = conn.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            raw_email_str = raw_email.decode("utf-8")
            msg = email.message_from_string(raw_email_str)

            if not since or get_date(msg) > since:
                msgs.append(msg)
    conn.close()
    conn.logout()

    return msgs


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
    return bool(re.search(r'\b(no(t)?|don\'t|stop|end|n|false)\b', phrase,
                          re.IGNORECASE))


def is_positive(phrase):
    """
        Returns True if the input phrase has a positive sentiment.

        Arguments:
        phrase -- the input phrase to-be evaluated
    """
    return bool(re.search(r'\b(sure|yes|yeah|go|yup|y|true)\b',
                          phrase,
                          re.IGNORECASE))
