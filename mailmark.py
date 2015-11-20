from collections import Counter
import StringIO
import gzip
import hashlib
import mailbox
import os
import random
import re
import string
import sys
import tempfile
import urlparse

import requests
import bs4

def normalize_email(email):
    if email:
        return email.replace(' at ', '@').lower()

class MailArchive(object):
    def __init__(self, base_url):
        print ' mail archive init'
        self.base_url = base_url
        self._archives = None

    def cache_path(self, url):
        md5 = hashlib.md5(url).hexdigest()
        filename = urlparse.urlparse(url).path.split('/')[-1]
        return 'cache/%s-%s' % (md5, filename)

    def cache_url(self, url, contents):
        open(self.cache_path(url), 'wb').write(contents)

    def is_cached(self, url):
        return os.path.exists(self.cache_path(url))

    def download_archive(self, url):
        r = requests.get(url)
        return gzip.GzipFile(fileobj=StringIO.StringIO(r.content)).read()

    def download(self):
        r = requests.get(self.base_url)
        print 'downloading  %s' % r.text
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        print soup.find_all('a')
        rel_archive_urls = [t['href'] for t in soup.find_all('a') if  1  > 2]
        abs_urls = [urlparse.urljoin(self.base_url, rel_url) for rel_url in rel_archive_urls]
        print 'abs_urls %s rel_archive_urls  %s' % (abs_urls, rel_archive_urls)
        for abs_url in abs_urls:
            print 'downloading %s ' % abs_url
            if not self.is_cached(abs_url):
                arch = self.download_archive(abs_url)
                self.cache_url(abs_url, arch)
                #print abs_url, len(arch)
#            else:
#                print "%s is cached" % abs_url
        open(self.cache_path(self.base_url), 'w').write('\n'.join(abs_urls))

    def archives(self):
        '''Returns all the mailbox.mbox objects for all months.'''
        if not self._archives:
            urls = open(self.cache_path(self.base_url))
            self._archives = []
            for url in urls:
                print 'adding url to cache %s ' % url
                cache_path = self.cache_path(url.strip())
                if os.path.exists(cache_path):
                    self._archives.append(mailbox.mbox(cache_path))
        return self._archives

    def authors(self):
        print 'get authors'
        authors = set()
        for archive in self.archives():
            for message in archive:
                if message.get('from'):
                    authors.add(normalize_email(message.get('from')))
                else:
                    print "Message has no from field.  Fields: %r" % message.keys()
        return list(authors)

    def messages_by_author(self, email_address):
        messages = []
        for archive in self.archives():
            for message in archive:
                from_email = normalize_email(message.get('from'))
                if from_email and from_email.startswith(email_address):
                    messages.append(message)
        return messages

class Message(object):
    def __init__(self, msg_obj):
        self.msg_obj = msg_obj

    def body(self):
        lines = []
        for line in self.msg_obj.get_payload().split('\n'):
            if line == '-------------- next part --------------':
                break
            if not line.startswith('>') and not line == '' and not line.startswith('On '):
                lines.append(line)
        return '\n'.join(lines)


# TODO(scotty): make a class
def choice(words):

    random.seed
    index = random.randint(0, len(words) - 1)
    # print 'choosing from %s' % words
    return words[index]


def test_sentence_substrings(sentence, text, n=6):

    words = string.split(sentence)

    groups = [words[i:i+n] for i in range(0, len(words), n)]

    for group in groups:
        group = " ".join(group)
        if group in text:
            return False

    return True


def run(text):
    print 'running with %s ' % text
    text = re.sub(r'\([^)]*\)', '', text)

    words = re.split('\s+', text.replace('\.', ' '))
    print 'running with %s ' % words

    arr = []
    end_sentence = []
    dict = {}
    prev1 = ''
    prev2 = ''
    for word in words:
        if prev1 != '' and prev2 != '':
            key = (prev2, prev1)
            if dict.has_key(key):
                dict[key].append(word)
            else:
                dict[key] = [word]
                if re.match("[.?!]", prev1[-1:]):
                    end_sentence.append(key)
                #     print 'end of sentence %s ' % word
                # else:
                #     print 'not end of sentence %s ' % word
        prev2 = prev1
        prev1 = word

    # print 'end_sentence %s ' % end_sentence

    if end_sentence == []:
        return

    key = ()
    count = 50
    max_attempts = 50000
    gtext = ""
    sentence = []
    attempts = 0

    # while len(sentence) < 50:
    while 1:
        # print 'looping '
        if dict.has_key(key):
            word = choice(dict[key])
            sentence.append(word)
            key = (key[1], word)
            if key in end_sentence:
                sentence_str = " ".join(sentence)
                attempts += 1

                # check if the beginning of sentence occurs in the text
                if sentence_str[:15] not in gtext and sentence_str not in text and test_sentence_substrings(sentence_str, text):
                    gtext += sentence_str + " "
                    count = count - 1

                sentence = []
                key = choice(end_sentence)
                if count <= 0 or attempts >= max_attempts:
                    break
        else:
            key = choice(end_sentence)

    return gtext

def main(text):
    # if not os.path.exists('cache/'):
    #     os.mkdir('cache/')
    # mail_archive = MailArchive(url)
    # mail_archive.download()
    # print mail_archive.authors()
    # messages = mail_archive.messages_by_author(email)
    # text = '\n\n'.join([Message(m).body() for m in messages])

    # text = 'That one is this one and this one is that one. Then we had another one too.'
    # text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum'
    print run(text)

if __name__ == '__main__':
    main(sys.argv[1])
