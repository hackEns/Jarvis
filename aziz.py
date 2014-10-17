#!/usr/bin/env python3

"""
This is the mailing-list code, to check wether there are some emails waiting
for validation.
"""

import email
import imaplib
import re
import sys

from libjarvis.config import Config

config = Config()


def handle_raw_email(body):
    """This function handles a single email body"""
    mail = email.message_from_bytes(body)

    if "sympa@lists.ens.fr" in mail["From"]:
        for part in mail.walk():
            if part.get_content_type() != "text/plain":
                continue
            decoded = part.get_payload(decode=True).decode('utf-8')
            decoded = decoded.replace("Le message", '').replace("\r\n", " ").strip().split(" ")
            token = decoded[0]
            liste = decoded[4]
            action = decoded[-1].strip('.')
        return ("sympa", action, token, liste)

    elif("hackens-membres-editor@ens.fr" in mail["To"] or
            "hackens-editor@ens.fr" in mail["To"]):
        try:
            multipart_msg = mail.get_payload(1)
            if multipart_msg.is_multipart():
                subject = multipart_msg.get_payload(0)['Subject']
                author = multipart_msg.get_payload(0)['From']
        except (IndexError, TypeError):
            return False
        main_msg = mail.get_payload(0)
        match = re.search("\nDISTRIBUTE (\S) (\S)\n", str(main_msg))
        if not match:
            return False
        liste = match.group(1)
        token = match.group(2)
        return ("distribution", "nouveau", token, liste, subject, author)


if __name__ == "__main__":
    print('Connecting to '+config.get("imap_server")+'… ', end='')
    conn = imaplib.IMAP4_SSL(config.get("imap_server"))
    print('Connected')
    to_send = []

    try:
        print('Logging as '+config.get("imap_user")+'… ', end='')
        conn.login(config.get("imap_user"), config.get("imap_password"))
    except:
        print('Failed')
        print(sys.exc_info()[1])
        sys.exit(1)
    print('Logged in')

    try:
        # Fetch new emails in INBOX, using uids
        conn.select("inbox")
        result, data = conn.uid('search', None, "ALL")
        uids_list = data[0].split()
        for uid in uids_list:
            result, data = conn.uid("fetch", uid, "(RFC822)")
            handle_raw_email(data[0][1])

        # Delete parsed emails
        for uid in uids_list:
            conn.uid("store", uid.decode("utf-8"), "+FLAGS", "(\\Deleted)")
        conn.expunge()
    finally:
        try:
            conn.close()
        except:
            pass
        conn.logout()
