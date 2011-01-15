"""
Holds information about what the user asked for (which program, version constraints, etc).
"""

# Copyright (C) 2011, Thomas Leonard
# See the README file for details, or visit http://0install.net.

from zeroinstall import _

class Requirements(object):
	"""
	Holds information about what the user asked for (which program, version constraints, etc).
	"""
	__slots__ = [
		'interface_uri',
		'command',
		'source',
		'before', 'not_before',
		'os', 'cpu',
		'message',
	]

	def __init__(self, interface_uri):
		self.interface_uri = interface_uri
		self.command = 'run'
		self.source = False
		self.before = self.not_before = None
		self.os = self.cpu = None
		self.message = None

	def get_as_options(self):
		gui_args = []
		if self.not_before:
			gui_args.insert(0, self.not_before)
			gui_args.insert(0, '--not-before')
		if self.before:
			gui_args.insert(0, self.before)
			gui_args.insert(0, '--before')
		if self.source:
			gui_args.insert(0, '--source')
		if self.message:
			gui_args.insert(0, self.message)
			gui_args.insert(0, '--message')
		if self.cpu:
			gui_args.insert(0, self.cpu)
			gui_args.insert(0, '--cpu')
		if self.os:
			gui_args.insert(0, self.os)
			gui_args.insert(0, '--os')
		if self.command is not None:
			gui_args.append('--command')
			gui_args.append(self.command)

		return gui_args
