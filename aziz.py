#!/usr/bin/env python3

"""
This is the mailing-list code, to check wether there are some emails waiting
for validation.
"""

import datetime
import email
import imaplib
import mysql.connector
import re
import sys

from libjarvis import tools
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
            decoded = decoded.replace("Le message", '').replace("\r\n", " ") \
                .strip().split(" ")
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
        match = re.search(r"\nDISTRIBUTE (\S) (\S)\n", str(main_msg))
        if not match:
            return False
        liste = match.group(1)
        token = match.group(2)
        return ("distribution", token, liste, subject, author)


if __name__ == "__main__":
    print('Connecting to ' + config.get("imap_server") + '… ', end='')
    conn = imaplib.IMAP4_SSL(config.get("imap_server"))
    print('Connected')
    to_send = []

    try:
        print('Logging as ' + config.get("imap_user") + '… ', end='')
        conn.login(config.get("imap_user"), config.get("imap_password"))
    except:
        print('Failed')
        print(sys.exc_info()[1])
        sys.exit(1)
    print('Logged in')

    try:
        bdd = mysql.connector.connect(**config.get("mysql"))
        bdd_cursor = bdd.cursor()
    except mysql.connector.Error as err:
        tools.warning(err)
        sys.exit(1)

    try:
        # Fetch new emails in INBOX, using uids
        conn.select("inbox")
        result, data = conn.uid('search', None, "ALL")
        uids_list = data[0].split()
        for uid in uids_list:
            result, data = conn.uid("fetch", uid, "(RFC822)")
            parsed = handle_raw_email(data[0][1])

            if parsed[0] == "sympa":
                query = "UPDATE moderation SET moderated=%s WHERE \
                         token=%s AND liste=%s"
                if parsed[1] == "rejeté":
                    values = (-1, parsed[2], parsed[3])
                elif parsed[1] == "distribué":
                    values = (1, parsed[2], parsed[3])
            elif parsed[0] == "distribution":
                query = "INSERT INTO moderation(subject, author, date, liste, \
                token, moderated) VALUES(%s, %s, %s, %s, %s, %s)"
                values = (parsed[3], parsed[4],
                          datetime.datetime.now(), parsed[2], 1)
            else:
                sys.exit(1)
            bdd_cursor.execute(query, values)

        # Delete parsed emails
        for uid in uids_list:
            conn.uid("store", uid.decode("utf-8"), "+FLAGS", "(\\Deleted)")
        conn.expunge()
    finally:
        try:
            conn.close()
            bdd_cursor.close()
            bdd.close()
        except:
            pass
        conn.logout()
