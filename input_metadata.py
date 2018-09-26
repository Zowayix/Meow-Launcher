
def _pluralize(n, singular, plural=None):
	if not plural:
		plural = singular + 's'
	if n == 1:
		return singular
	return '%d %s' % (n, plural)

class InputType():
	def describe(self):
		return type(self).__name__

class NormalInput(InputType):
	def __init__(self):
		self.face_buttons = 0
		self.shoulder_buttons = 0
		self.dpads = 0
		self.analog_sticks = 0
		self.analog_triggers = 0

	@property
	def is_standard(self):
		"""
		If this input setup is compatible with a standard modern controller: 4 face buttons, 2 shoulder buttons, 2 analog triggers, 2 analog sticks, one dpad, start + select. Dunno how I feel about clickable analog sticks. Also any "guide" or "home" button doesn't count, because that should be free for emulator purposes instead of needing the game to map to it. Hmm. Maybe analog triggers aren't that standard. Some modern gamepads just have 2 more shoulder buttons instead, after all.
		So if your gamepad has more stuff than this "standard" one, which it probably does, that's great, it just means it can support non-standard emulated controls.
		"""

		if self.analog_sticks > 2:
			return False
		if self.dpads > 1:
			if (self.analog_sticks + self.dpads) > 3:
				#It's okay to have two digital joysticks if one can just be mapped to one of the analog sticks
				return False

		if self.face_buttons > 4:
			return False

		if self.shoulder_buttons > 2:
			return False

		if self.analog_triggers > 2:
			#Anything more than that is definitely non-standard, regardless of how I go with my "are analog triggers standard" debate
			return False

		return True

	def describe(self):
		if self.is_standard:
			return "Standard"

		description = []
		if self.face_buttons:
			description.append(_pluralize(self.face_buttons, 'button'))
		if self.shoulder_buttons:
			description.append(_pluralize(self.shoulder_buttons, 'shoulder button'))
		if self.dpads:
			description.append(_pluralize(self.dpads, 'dpad'))
		if self.analog_sticks:
			description.append(_pluralize(self.analog_sticks, 'analog stick'))
		if self.analog_triggers:
			description.append(_pluralize(self.analog_triggers, 'analog trigger'))

		return ' + '.join(description)

class Biological(InputType):
	#e.g. Mindlink for Atari 2600 (actually just senses muscle movement); N64 heart rate sensor
	pass

class Dial(InputType):
	pass

class Gambling(InputType):
	pass

class Hanafuda(InputType):
	pass

class Keyboard(InputType):
	#TODO: Number of keys
	pass

class Keypad(InputType):
	#TODO Number of keys
	pass

class LightGun(InputType):
	def describe(self):
		return 'Light Gun'

class Mahjong(InputType):
	pass

class MotionControls(InputType):
	def describe(self):
		return 'Motion Controls'

class Mouse(InputType):
	#TODO Buttons
	pass

class Paddle(InputType):
	pass

class Pedal(InputType):
	pass

class Positional(InputType):
	#What the heck is this
	pass

class SteeringWheel(InputType):
	def describe(self):
		return 'Steering Wheel'

class Touchscreen(InputType):
	pass

class Trackball(InputType):
	pass

class Custom(InputType):
	pass

class InputOption():
	def __init__(self):
		self.inputs = []
		self._known = False
		#TODO: Have such a thing as a "main" input option, which would help with metadata shown in the launcher and whatnot

	def describe(self):
		if not self.inputs:
			return 'Nothing'
		if len(self.inputs) == 1:
			return self.inputs[0].describe()
		return ' + '.join([input.describe() for input in self.inputs])

class InputInfo():
	def __init__(self):
		self.input_options = []
		self._known = False

	def add_option(self, inputs):
		opt = InputOption()
		opt.inputs = inputs
		self.input_options.append(opt)

	@property
	def known(self):
		#Need a better name for this. Basically determines if this has been initialized and hence the information is not missing
		return self.input_options or self._known

	def set_known(self):
		self._known = True

	def describe(self):
		return [opt.describe() for opt in self.input_options] if self.input_options else ['Nothing']