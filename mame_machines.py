import subprocess
import xml.etree.ElementTree as ElementTree
import configparser
import os
import sys

import config
import common
import launchers
import emulator_info
from metadata import EmulationStatus, Metadata, SystemSpecificInfo

debug = '--debug' in sys.argv

def find_main_cpu(machine):
	for chip in machine.findall('chip'):
		tag = chip.attrib['tag']
		if tag == 'maincpu' or tag == 'mainpcb:maincpu':
			return chip

	#If no maincpu, just grab the first CPU chip
	for chip in machine.findall('chip'):
		if chip.attrib['type'] == 'cpu':
			return chip

	#Alto I and HP 2100 have no chips, apparently.  Huh?  Oh well
	return None

def mame_verifyroms(basename):
	#FIXME Okay this is way too fuckin' slow
	status = subprocess.run(['mame', '-verifyroms', basename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
	return status == 0

def get_catlist():
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.catlist_path)
	return parser
	
def get_languages():
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.languages_path)
	return parser

catlist = get_catlist()
languages = get_languages()

def get_category(basename):
	cat = None
	for section in catlist.sections():
		if basename in catlist[section]:
			cat = section
			break
	if not cat:
		return 'Unknown', 'Unknown', 'Unknown', 'Unknown'

	if ': ' in cat:
		category, _, genres = cat.partition(': ')
		genre, _, subgenre = genres.partition(' / ')
		is_nsfw = False
		if subgenre.endswith('* Mature *'):
			is_nsfw = True
			subgenre = subgenre[:-10]
		
		return category, genre, subgenre, is_nsfw
	
	category, genre = cat.split(' / ', 1)
	return category, genre, None, False
		
def get_language(basename):
	lang = None
	for section in languages.sections():
		if basename in languages[section]:
			lang = section
			break
			
	return lang

def get_input_type(machine):
	input_element = machine.find('input')
	if input_element is None:
		#Seems like this doesn't actually happen
		if debug:
			print('Oi m8', machine.attrib['name'], '/', machine.findtext('description'), 'has no input')
		return 'No input somehow'

	control_element = input_element.find('control')
	if control_element is None:
		if 'players' not in input_element.attrib or input_element.attrib['players'] == '0':				
			return None
			
		return 'Custom'
		#Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
		#pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
		#playable just fine, so we'll leave them in

	input_type = control_element.attrib['type']
	if input_type:
		if input_type == 'doublejoy':
			return 'Twin Joystick'
		elif input_type == 'joy':
			return 'Normal'
		elif input_type == 'lightgun':
			return 'Light Gun'
				
		return input_type.replace('_', ' ').capitalize()

	if debug:
		print("This shouldn't happen either but for", machine.attrib['name'], "it did")
	return None

def add_metadata(metadata, machine):
	basename = machine.attrib['name']

	category, genre, subgenre, metadata.nsfw = get_category(basename)
	language = get_language(basename)

	source_file = os.path.splitext(machine.attrib['sourcefile'])[0]
	metadata.system_specific_info.append(SystemSpecificInfo('Source-File', source_file, True))
	
	main_cpu = find_main_cpu(machine)
	if main_cpu:
		metadata.main_cpu = main_cpu.attrib['name']
		
	metadata.platform = 'Arcade'
	if source_file == 'megatech':
		metadata.platform = 'Mega-Tech'
	elif source_file == 'megaplay':
		metadata.platform = 'Mega-Play'
	elif source_file == 'playch10':
		metadata.platform = 'PlayChoice-10'
	elif source_file == 'nss':
		metadata.platform = 'Nintendo Super System'
	elif category == 'Game Console':
		metadata.platform = 'Plug & Play' 
		#Since we're skipping over stuff with software lists, anything that's still classified as a game console is a plug &
        #play system
	elif category == 'Handheld':
		metadata.platform = 'Handheld' 
		#Could also be a tabletop system which takes AC input, but since catlist.ini doesn't take that into account, I don't
		#really have a way of doing so either
	elif category == 'Misc.':
		metadata.platform = genre
	elif category == 'Computer':
		metadata.platform = 'Computer'
	elif genre == 'Electromechanical' and subgenre == 'Reels':
		metadata.platform = 'Pokies'
		category = 'Pokies'
	elif genre == 'Electromechanical' and subgenre == 'Pinball':
		metadata.platform = 'Pinball'
		category = 'Pinball'

	if language is not None and language != 'English':
		category += ' untranslated'

	if category:
		metadata.categories = [category]
	if language:
		metadata.languages = [language]
	metadata.genre = genre
	metadata.subgenre = subgenre

	metadata.emulator_name = 'MAME'
	metadata.year = machine.findtext('year')
	metadata.author = machine.findtext('manufacturer')
	
	emulation_status = machine.find('driver').attrib['status']
	if emulation_status == 'good':
		metadata.emulation_status = EmulationStatus.Good
	elif emulation_status == 'imperfect':
		metadata.emulation_status = EmulationStatus.Imperfect
	elif emulation_status == 'preliminary':
		metadata.emulation_status = EmulationStatus.Broken

	#Some other things we could get from XML if we decide we care about it:
	#Display type/resolution/refresh rate/number of screens
	#Sound channels
	#Number of players
	
	
def should_process_machine(machine):
	if machine.attrib['runnable'] == 'no':
		return False

	if machine.attrib['isbios'] == 'yes':
		return False

	if machine.attrib['isdevice'] == 'yes':
		return False

	return True

def process_machine(machine):
	if not should_process_machine(machine):
		return
	
	basename = machine.attrib['name']
	family = machine.attrib['cloneof'] if 'cloneof' in machine.attrib else basename
	name = machine.findtext('description')
	
	if not (machine.find('softwarelist') is None) and family not in config.okay_to_have_software:
		return

	input_type = get_input_type(machine)
	if not input_type:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
		if debug:
			print('Skipping %s (%s) as it has no controls' % (basename, name))
		return
	
	metadata = Metadata()
	add_metadata(metadata, machine)
	metadata.input_method = input_type
	metadata.system_specific_info.append(SystemSpecificInfo('Family', family, True))

	command_line = emulator_info.make_mame_command_line(basename)
	launchers.make_launcher(command_line, name, metadata)
		
def get_mame_drivers():
	drivers = []

	process = subprocess.run(['mame', '-listsource'], stdout=subprocess.PIPE, universal_newlines=True)
	status = process.returncode
	output = process.stdout
	if status != 0:
		print('Shit')
		return []

	for line in output.splitlines():
		try:		
			driver, source_file = line.split(None, 1)
			drivers.append((driver, os.path.splitext(source_file)[0]))
		except ValueError:
			print('For fucks sake ' + line)
			continue	

	return drivers
	
def get_mame_xml(driver):
	process = subprocess.run(['mame', '-listxml', driver], stdout=subprocess.PIPE)
	status = process.returncode
	output = process.stdout
	if status != 0:
		print('Fucking hell ' + driver)
		return None

	return ElementTree.fromstring(output)

def process_arcade():
	#Fuck iterparse by the way, if you stumble across this script and think "oh you should use iterparse instead of this
	#kludge!" you are wrong
	#(Okay, if you want an attempt at a reason why: I've tried it, and MAME's machine elements are actually more
	#complicated and seemingly refer to other machine elements that are displayed alongside the main one with an
	#individual -listxml)
	#Could it be faster to use -verifyroms globally and parse the output somehow and then get individual XML from
	#successful results?

	for driver, source_file in get_mame_drivers():
		if source_file in config.too_slow_drivers:
			continue
			
		if common.starts_with_any(source_file, config.skip_fruit_machines):
			#Get those fruit machines outta here (they take too long to process and verify that we don't have them, and tend to
			#not work anyway, otherwise I'd consider still including them)
			continue

		#You probably think this is why it's slow, right?  You think "Oh, that's silly, you're verifying every single romset
		#in existence before just getting the XML", that's what you're thinking, right?  Well, I am doing that, but as it
		#turns out if I do the verification inside process_machine it takes a whole lot longer.  I don't fully understand why
		#but I'll have you know I actually profiled it
		if not mame_verifyroms(driver):
			continue

		xml = get_mame_xml(driver)
		if xml is None:
			continue
		process_machine(xml.find('machine'))
