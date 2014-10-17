#!/usr/bin/env python3

"""
This is the mailing-list code, to check wether there are some emails waiting
for validation.
"""

import email
import imaplib
import sys

from libjarvis.config import Config

config = Config()


def handle_raw_email(body):
    """This function handles a single email body"""
    mail = email.message_from_bytes(body)

    if "sympa@lists.ens.fr" in mail["From"]:
        for part in mail.walk():
            if part.is_multipart() == 'multipart':
                continue
            part = part.replace("Le message", '').strip().split(" ")
            ident = part[0].strip()
            liste = part[4].strip()
            data = ["valider", ident, liste]

    elif("hackens-membres-editor@ens.fr" in mail["From"] or
            "hackens-editor@ens.fr" in mail["From"]):
        # TODO
        subject = mail.get_payload()[1].get_payload()[0]['Subject']
        author = mail.get_payload()[1].get_payload()[0]['From']
        for line in reversed(body):
            try:
                line = line.decode('utf-8').strip()
            except UnicodeError:
                line = line.decode('iso-8859-1').strip()
            if line.lower().startswith("subject") and subject is None:
                subject = ':'.join(line.split(':')[1:]).strip()
            if line.lower().startswith("from") and author is None:
                author = ':'.join(line.split(':')[1:]).strip()

        content = (mail.get_payload()[0]
                    .get_payload(decode=True)
                    .decode('utf-8'))
        for line in content.split('\n'):
            if line.strip().startswith("DISTRIBUTE"):
                line = line.split(" ")
                ident = line[-1].strip()
                liste = line[1].strip()
                break
        data = ["nouveau", ident, liste, subject, author]


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
            print(uid)
            result, data = conn.fetch(uid, "(RFC822)")
            handle_raw_email(data[0][1])

        # Delete parsed emails
        #conn.uid("store", ", ".join(uids_list), "+FLAGS", "(\Deleted)")
        #conn.expunge()
    finally:
        try:
            conn.close()
        except:
            pass
        conn.logout()
