from common import pluralize

class Controller():
	def describe(self):
		return type(self).__name__

	@property
	def is_standard(self):
		return False

class NormalController(Controller):
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
			if (self.shoulder_buttons + self.analog_triggers) > 4:
				#It's okay to have 4 shoulder buttons if two can be mapped to the analog triggers
				return False

		if self.analog_triggers > 2:
			#Anything more than that is definitely non-standard, regardless of how I go with my "are analog triggers standard" debate
			return False

		return True

	def describe(self):
		description = []
		if self.face_buttons:
			description.append(pluralize(self.face_buttons, 'button'))
		if self.shoulder_buttons:
			description.append(pluralize(self.shoulder_buttons, 'shoulder button'))
		if self.dpads:
			description.append(pluralize(self.dpads, 'dpad'))
		if self.analog_sticks:
			description.append(pluralize(self.analog_sticks, 'analog stick'))
		if self.analog_triggers:
			description.append(pluralize(self.analog_triggers, 'analog trigger'))

		return ' + '.join(description)

class Biological(Controller):
	#e.g. Mindlink for Atari 2600 (actually just senses muscle movement); N64 heart rate sensor
	pass

class Dial(Controller):
	def __init__(self):
		self.buttons = 0

	def describe(self):
		if self.buttons > 0:
			return '{0}-button dial'.format(self.buttons)
		return 'Dial'

class Gambling(Controller):
	def __init__(self):
		self.buttons = 0

	def describe(self):
		if self.buttons > 0:
			return '{0}-button gambling controls'.format(self.buttons)
		return 'Gambling Controls'

class Hanafuda(Controller):
	def __init__(self):
		self.buttons = 0 #Or are they more accurately called keys

	def describe(self):
		if self.buttons > 0:
			return '{0}-button hanafuda controller'.format(self.buttons)
		return 'Hanafuda Controller'

class Keyboard(Controller):
	def __init__(self):
		self.keys = 0

	def describe(self):
		if self.keys > 0:
			return '{0}-key keyboard'.format(self.keys)
		return 'Keyboard'

class Keypad(Controller):
	def __init__(self):
		self.keys = 0

	def describe(self):
		if self.keys > 0:
			return '{0}-key keypad'.format(self.keys)
		return 'Keypad'

class LightGun(Controller):
	def __init__(self):
		self.buttons = 0

	def describe(self):
		if self.buttons > 0:
			return '{0}-button light gun'.format(self.buttons)
		return 'Light Gun'

class Mahjong(Controller):
	def __init__(self):
		self.buttons = 0 #Or are they more accurately called keys (is this even really a different controller type anyway?)

	def describe(self):
		if self.buttons > 0:
			return '{0}-button mahjong controller'.format(self.buttons)
		return 'Mahjong Controller'

class MotionControls(Controller):
	def describe(self):
		return 'Motion Controls'

class Mouse(Controller):
	def __init__(self):
		self.buttons = 0

	def describe(self):
		if self.buttons > 0:
			return '{0}-button mouse'.format(self.buttons)
		return 'Mouse'

class Paddle(Controller):
	def __init__(self):
		self.buttons = 0

	def describe(self):
		if self.buttons > 0:
			return '{0}-button paddle'.format(self.buttons)
		return 'Paddle'

class Pedal(Controller):
	pass

class Positional(Controller):
	#What the heck is this
	pass

class SteeringWheel(Controller):
	def describe(self):
		return 'Steering Wheel'

class Touchscreen(Controller):
	pass

class Trackball(Controller):
	def __init__(self):
		self.buttons = 0

	def describe(self):
		if self.buttons > 0:
			return '{0}-button trackball'.format(self.buttons)
		return 'Trackball'

class Custom(Controller):
	def __init__(self, custom_description=None):
		self.custom_description = custom_description

	def describe(self):
		return self.custom_description if self.custom_description else 'Custom'

class CombinedController(Controller):
	def __init__(self, components=None):
		self.components = []
		if components:
			for component in components:
				self.components.append(component)

	@property
	def is_standard(self):
		return all([component.is_standard for component in self.components])

	def describe(self):
		if not self.components:
			#Theoretically shouldn't happen. $2 says I will be proven wrong and have to delete this comment
			return '<weird controller>'
		if len(self.components) == 1:
			return self.components[0].describe()
		return ' + '.join([component.describe() for component in self.components])

class InputOption():
	def __init__(self):
		self.inputs = []

	@property
	def is_standard(self):
		#Hmm could this be wrong... feel like there's a case I'm not thinking of right now where something could be standard inputs individually but not usable with standard controllers when all together
		return all([input.is_standard for input in self.inputs])

	def describe(self):
		if not self.inputs:
			return 'Nothing'
		if len(self.inputs) == 1:
			return self.inputs[0].describe()
		return ' + '.join([input.describe() for input in self.inputs])

class InputInfo():
	def __init__(self):
		self.input_options = []
		self._is_inited = False

	def add_option(self, inputs):
		opt = InputOption()
		opt.inputs = inputs if isinstance(inputs, list) else [inputs]
		self.input_options.append(opt)

	@property
	def is_inited(self):
		return self.input_options or self._is_inited

	def set_inited(self):
		self._is_inited = True

	@property
	def has_standard_inputs(self):
		return any([option.is_standard for option in self.input_options]) or not self.input_options

	def describe(self):
		return [opt.describe().capitalize() for opt in self.input_options] if self.input_options else ['Nothing']
