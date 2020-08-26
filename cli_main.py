#!/usr/bin/env python3

import datetime
import time
import sys

from mame_helpers import have_mame
import config.main_config
import main

overall_time_started = time.perf_counter()

def print_callback(data, _):
	if data:
		print(data)

mame_enabled = '--no-arcade' not in sys.argv and have_mame()
main.main(print_callback, mame_enabled=mame_enabled)

if config.main_config.main_config.print_times:
	overall_time_ended = time.perf_counter()
	print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
