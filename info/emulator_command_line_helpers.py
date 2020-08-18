import os
from common_types import EmulationNotSupportedException
from mame_helpers import have_mame
from software_list_info import get_software_list_by_name
from launchers import LaunchParams

def _get_autoboot_script_by_name(name):
	this_package = os.path.dirname(__file__)
	root_package = os.path.dirname(this_package)
	return os.path.join(root_package, 'mame_autoboot', name + '.lua')

def _verify_supported_mappers(game, supported_mappers, detected_mappers):
	mapper = game.metadata.specific_info.get('Mapper', None)

	if not mapper:
		#If there was a problem detecting the mapper, or it's something invalid, it probably won't run
		raise EmulationNotSupportedException('Mapper is not detected at all')

	if game.metadata.specific_info.get('Override-Mapper', False) and mapper not in detected_mappers:
		#If the mapper in the ROM header is different than what the mapper actually is, it won't work, since we can't override it from the command line or anything
		#But it'll be okay if the mapper is something that gets autodetected outside of the header anyway
		raise EmulationNotSupportedException('Overriding the mapper to {0} is not supported'.format(mapper))

	if mapper not in supported_mappers and mapper not in detected_mappers:
		raise EmulationNotSupportedException('Mapper ' + mapper + ' not supported')

def verify_mgba_mapper(game):
	supported_mappers = ['ROM only', 'MBC1', 'MBC2', 'MBC3', 'HuC1', 'MBC5', 'HuC3', 'MBC6', 'MBC7', 'Pocket Camera', 'Bandai TAMA5']
	detected_mappers = ['MBC1 Multicart', 'MMM01', 'Wisdom Tree']

	_verify_supported_mappers(game, supported_mappers, detected_mappers)

def _is_software_available(software_list_name, software_name):
	if not have_mame():
		return False

	software_list = get_software_list_by_name(software_list_name)
	if not software_list:
		return False
	available_software = software_list.get_available_software()
	for software in available_software:
		if software.name == software_name:
			return True
	return False

def _is_highscore_cart_available():
	return _is_software_available('a7800', 'hiscore')
	#FIXME: This is potentially wrong for A7800, where the software directory could be different than MAME... I've just decided to assume it's set up that way

def mednafen_base(module):
	return LaunchParams('mednafen', ['-video.fs', '1', '-force_module', module, '$<path>'])

def mame_base(driver, slot=None, slot_options=None, has_keyboard=False, autoboot_script=None, software=None):
	args = ['-skip_gameinfo']
	if has_keyboard:
		args.append('-ui_active')

	args.append(driver)
	if software:
		args.append(software)

	if slot_options:
		for name, value in slot_options.items():
			if not value:
				value = ''
			args.append('-' + name)
			args.append(value)

	if slot:
		args.append('-' + slot)
		args.append('$<path>')

	if autoboot_script:
		args.append('-autoboot-script')
		args.append(_get_autoboot_script_by_name(autoboot_script))

	return args

def mame_system(driver, slot=None, slot_options=None, has_keyboard=False, autoboot_script=None):
	args = mame_base(driver, slot, slot_options, has_keyboard, autoboot_script)
	return LaunchParams('mame', args)
