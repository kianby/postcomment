#!/usr/bin/env python

import sys
from daemon import Daemon
import SimpleHTTPServer
import SocketServer
import logging
import cgi
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

HOST_NAME = "127.0.0.1"
PORT_NUMBER = 8001
DEFAULT_REDIRECT = "http://blogduyax.madyanne.fr"
EMAIL_FROM = "blogduyax@madyanne.fr"
EMAIL_TO = "blogduyax@madyanne.fr"
COMMENTS_DIR = "/srv/postcomment/comments"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
fh = logging.FileHandler("postcomment.log", "a")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        logger.info("GET %s" % self.headers)
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        logger.info("POST %s" % self.headers)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # debug
        #logging.info(self.headers)
        #for item in form.list:
        #    logging.info(item)

        # get form values and create comment file
        author = form.getvalue('author', 'Unname')
        email = form.getvalue('email', '')
        site = form.getvalue('site', '')
        article = form.getvalue('article', '')
        message = form.getvalue('message', '')
        now = datetime.now()
        filename = '%s/comment-%s.md' % (COMMENTS_DIR, now.strftime("%Y%m%d-%H%M%S"))
        with open(filename, 'a') as f:
            f.write('author: %s\n' % author)
            f.write('email: %s\n' % email)
            f.write('site: %s\n' % site)
            f.write('date: %s\n' % now.strftime("%Y-%m-%d %H:%M:%S"))
            f.write('article: %s\n\n' % article)
            f.write('%s\n' % message)

        # Send an email

        # Create the container (outer) email message.
        msg = MIMEMultipart()
        msg['Subject'] = 'Nouveau commentaire'
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg.preamble = 'Nouveau commentaire'

        # Create body email
        fp = open(filename, 'rb')
        txt = MIMEText(fp.read())
        fp.close()
        msg.attach(txt)

        # Send the email via our own SMTP server.
        s = smtplib.SMTP('localhost')
        s.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        s.quit()

        # Redirect browser to same URL
        redirect_location = self.headers.get('referer', DEFAULT_REDIRECT)
        self.send_response(301)
        self.send_header("Location", redirect_location)
        self.end_headers()


class MyDaemon(Daemon):
    def run(self):
        Handler = ServerHandler
        httpd = SocketServer.TCPServer((HOST_NAME, PORT_NUMBER), Handler)
        logger.info("Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
        logger.info("Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))

 
if __name__ == "__main__":
    daemon = MyDaemon('/tmp/postcomment.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
