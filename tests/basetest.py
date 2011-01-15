#!/usr/bin/env python
import sys, tempfile, os, shutil, StringIO
import unittest
import logging
import warnings
warnings.filterwarnings("ignore", message = 'The CObject type')

# Catch silly mistakes...
os.environ['HOME'] = '/home/idontexist'
os.environ['LANGUAGE'] = 'C'

sys.path.insert(0, '..')
from zeroinstall.injector import qdom
from zeroinstall.injector import iface_cache, download, distro, model, handler, policy
from zeroinstall.zerostore import Store, Stores; Store._add_with_helper = lambda *unused: False
from zeroinstall import support, helpers
from zeroinstall.support import basedir

dpkgdir = os.path.join(os.path.dirname(__file__), 'dpkg')

empty_feed = qdom.parse(StringIO.StringIO("""<interface xmlns='http://zero-install.sourceforge.net/2004/injector/interface'>
<name>Empty</name>
<summary>just for testing</summary>
</interface>"""))

import my_dbus
sys.modules['dbus'] = my_dbus
sys.modules['dbus.glib'] = my_dbus
my_dbus.types = my_dbus
sys.modules['dbus.types'] = my_dbus
sys.modules['dbus.mainloop'] = my_dbus
sys.modules['dbus.mainloop.glib'] = my_dbus

mydir = os.path.dirname(__file__)

# Catch us trying to run the GUI and return a dummy string instead
old_execvp = os.execvp
def test_execvp(prog, args):
	if prog.endswith('/0launch-gui'):
		prog = os.path.join(mydir, 'test-gui')
	return old_execvp(prog, args)

os.execvp = test_execvp

test_locale = (None, None)
assert model.locale
class TestLocale:
	LC_ALL = 0	# Note: LC_MESSAGES not present on Windows
	def getlocale(self, x):
		return test_locale
model.locale = TestLocale()

class DummyPackageKit:
	available = False

	def get_candidates(self, package, factory, prefix):
		pass

class DummyHandler(handler.Handler):
	__slots__ = ['ex', 'tb']

	def __init__(self):
		handler.Handler.__init__(self)
		self.ex = None

	def wait_for_blocker(self, blocker):
		self.ex = None
		handler.Handler.wait_for_blocker(self, blocker)
		if self.ex:
			raise self.ex, None, self.tb

	def report_error(self, ex, tb = None):
		assert self.ex is None, self.ex
		self.ex = ex
		self.tb = tb

		#import traceback
		#traceback.print_exc()

class TestFetcher:
	def download_impls(self, impls, stores):
		assert impls == [], impls

class TestConfig:
	freshness = 0
	help_test_new_versions = False
	network_use = model.network_full

	def __init__(self):
		self.iface_cache = iface_cache.IfaceCache()
		self.handler = DummyHandler()
		self.stores = Stores()
		self.fetcher = TestFetcher()

class BaseTest(unittest.TestCase):
	def setUp(self):
		warnings.resetwarnings()

		self.config_home = tempfile.mktemp()
		self.cache_home = tempfile.mktemp()
		self.cache_system = tempfile.mktemp()
		self.gnupg_home = tempfile.mktemp()
		os.environ['GNUPGHOME'] = self.gnupg_home
		os.environ['XDG_CONFIG_HOME'] = self.config_home
		os.environ['XDG_CONFIG_DIRS'] = ''
		os.environ['XDG_CACHE_HOME'] = self.cache_home
		os.environ['XDG_CACHE_DIRS'] = self.cache_system
		reload(basedir)
		assert basedir.xdg_config_home == self.config_home

		os.mkdir(self.config_home, 0700)
		os.mkdir(self.cache_home, 0700)
		os.mkdir(self.cache_system, 0500)
		os.mkdir(self.gnupg_home, 0700)

		if os.environ.has_key('DISPLAY'):
			del os.environ['DISPLAY']

		self.config = TestConfig()
		policy._config = self.config	# XXX

		logging.getLogger().setLevel(logging.WARN)

		download._downloads = {}

		self.old_path = os.environ['PATH']
		os.environ['PATH'] = dpkgdir + ':' + self.old_path

		distro._host_distribution = distro.DebianDistribution(dpkgdir + '/status',
								      dpkgdir + '/pkgcache.bin')
		distro._host_distribution._packagekit = DummyPackageKit()

		my_dbus.system_services = {}

	def tearDown(self):
		assert self.config.handler.ex is None, self.config.handler.ex

		shutil.rmtree(self.config_home)
		support.ro_rmtree(self.cache_home)
		shutil.rmtree(self.cache_system)
		shutil.rmtree(self.gnupg_home)

		os.environ['PATH'] = self.old_path
