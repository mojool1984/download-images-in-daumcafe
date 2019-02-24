#!/usr/bin/env python3

import argparse
import os
import requests
import re
import sys

from selenium import webdriver
from bs4 import BeautifulSoup

WEBDRIVER_PATH='files/chromedriver'

def parse_cmdline():
	parser = argparse.ArgumentParser()
	parser.add_argument('-u', '--username', help='username', required=True)
	parser.add_argument('-p', '--password', help='password', required=True)
	parser.add_argument('-c', '--cafename', help='cafename', required=True)
	return parser.parse_args()

def login(username, password):
	driver = webdriver.Chrome(WEBDRIVER_PATH)
	driver.implicitly_wait(5)
	driver.get('https://logins.daum.net/accounts/loginform.do')

	driver.find_element_by_name('id').send_keys(username)
	driver.find_element_by_name('pw').send_keys(password)

	driver.find_element_by_xpath('//*[@id="loginBtn"]').click()

	driver.implicitly_wait(10)

	if 'logins.daum.net' in driver.current_url:
		return None

	session = requests.Session()
	headers = {'User-Agent': driver.execute_script('return navigator.userAgent')}
	session.headers.update(headers)

	session.cookies.update( {c['name']: c['value'] for c in driver.get_cookies()} )

	return session


def get_article_images(article_url, session):
	req = session.get(article_url)
	html = req.text
	soup = BeautifulSoup(html, 'html.parser')

	# get a title
	title = soup.find_all('h3', class_='tit_subject')[0].getText().strip()
	date  = soup.find_all('span', class_='num_subject')[0].getText().strip()

	for link in soup.find_all('img'):
		if 'txc-image' not in link['class']:
			continue

		sub_dir = '{}_{}_{}'.format(date, article_url.split('/')[-1].zfill(3), title)
		#sub_dir = '{}_{}'.format(date, title)
		sub_dir = re.sub('/', ',', sub_dir)
		download_image(link['src'], sub_dir, session)


def download_image(image_url, sub_dir, session):
	req = session.get(image_url)
	#print(image_url, req.headers)
	d = req.headers.get('content-disposition', None)
	if d:
		filename = re.findall('filename="(.+)"', d)[0]
	else:
		filename = image_url.split('/')[-1].strip()+'.jpg'

	print('  Downloading {} image.'.format(filename))

	if not os.path.exists(os.path.join('images', sub_dir)):
		os.makedirs(os.path.join('images', sub_dir))

	with open(os.path.join('images', sub_dir, filename), 'wb') as outfile:
		outfile.write(req.content)

if __name__ == '__main__':
	args = parse_cmdline()

	sess = login(args.username, args.password)
	if not sess:
		print('Login failed.')
		sys.exit(0)

	for k in range(34, 429+1):
		get_article_images('http://m.cafe.daum.net/{}/{}'.format(args.cafename, k), sess)
