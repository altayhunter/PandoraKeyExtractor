#!/usr/bin/python3
from argparse import ArgumentParser
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
import csv

# Return a list of URLs given a list of anchor elements
def extractUrls(elements):
	return [e.get_attribute('href') for e in elements]

# Return the key given a list of song attributes
def extractKey(attributes):
	for attr in attributes:
		if 'tonality' in attr:
			if 'mixed' in attr:
				return 'mixed'
			elif 'minor' in attr:
				return 'minor'
			elif 'major' in attr:
				return 'major'
			else:
				assert False, 'Could not parse key from: {}'.format(attr)
	return 'unknown'

if __name__ == "__main__":
	# Parse the CLI arguments
	parser = ArgumentParser(
		description='Generate a CSV with key/tonality data for each thumbs up '
		'song in the given station. Output is written to songs.csv in the '
		'current directory.')
	parser.add_argument(
		'--station', metavar='81143498671257753', type=int, required=True,
		help='the Pandora station ID')
	parser.add_argument(
		'--username', metavar='email@address.com', type=str, required=True,
		help='username for Pandora login')
	parser.add_argument(
		'--password', metavar='********', type=str, required=True,
		help='password for Pandora login')
	args = parser.parse_args()

	# Start up the browser
	display = Display(visible=0, size=(1280, 800))
	display.start()
	driver = webdriver.Firefox()

	# Load main Pandora page to avoid a redirect
	driver.get('https://www.pandora.com')
	sleep(1)
	# Load login page
	driver.get('https://www.pandora.com/account/sign-in')
	sleep(3)
	# Find and populate the form with the credentials
	elems = driver.find_elements_by_tag_name('input')
	assert len(elems) == 3, 'Expected 3 input fields; encountered {}'.format(len(elems))
	for elem in elems:
		assert 'Login' in elem.get_attribute('class'), 'Expected class name to contain Login; encountered {}'.format(elem.get_attribute('class'))
	driver.find_elements_by_tag_name('input')[0].send_keys(args.username)
	driver.find_elements_by_tag_name('input')[1].send_keys(args.password)
	submit = driver.find_elements_by_tag_name('button')[0]
	assert submit.text == 'Log In', 'Unexpected login button text: {}'.format(submit.text)
	submit.click()
	# Load the station details page
	driver.get('https://pandora.com/station/' + str(args.station))
	# Requires about a second per 10 songs in station; increase if >200 songs
	sleep(20)
	elems = driver.find_elements_by_class_name('StationDetailsListItem__primaryText')
	print('Found', len(elems), 'liked songs on station.')
	with open('songs.csv', 'w') as file:
		wr = csv.writer(file, quoting=csv.QUOTE_ALL)
		wr.writerow(['Title', 'Artist', 'Key', 'Link'])
		for url in extractUrls(elems):
			driver.get(url)
			track = driver.execute_script('return window._store["v1/music/track"][0]')
			print(track['songTitle'], track['artist']['name'], extractKey(track['focusTraits']))
			wr.writerow([track['songTitle'], track['artist']['name'], extractKey(track['focusTraits']), url])
	driver.close()
