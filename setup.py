import os, subprocess, re
from distutils.core import setup, Command
from distutils.command.sdist import sdist as _sdist
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
import os
from os import path

here = path.abspath(path.dirname(__file__))

VERSION_PY = """
# This file is originally generated from Git information by running 'setup.py
# version'. Distribution tarballs contain a pre-generated copy of this file.
__version__ = '%s'
"""

def update_version_py():
	if not os.path.isdir(".git"):
		print "This does not appear to be a Git repository."
		return
	try:
		p = subprocess.Popen(["git", "describe",
							  "--tags", "--dirty", "--always"],
							 stdout=subprocess.PIPE)
	except EnvironmentError:
		print "unable to run git, leaving mpos/_version.py alone"
		return
	stdout = p.communicate()[0]
	if p.returncode != 0:
		print "unable to run git, leaving mpos/_version.py alone"
		return
	# we use tags like "python-ecdsa-0.5", so strip the prefix
	print stdout
	assert stdout.startswith("mpos-")
	ver = stdout[len("mpos-"):].strip()
	f = open("mpos/_version.py", "w")
	f.write(VERSION_PY % ver)
	f.close()
	print "set mpos/_version.py to '%s'" % ver

def get_version():
	try:
		f = open("mpos/_version.py")
	except EnvironmentError:
		print "Unable to read version file"
		return None
	for line in f.readlines():
		mo = re.match("__version__ = '([^']+)'", line)
		if mo:
			ver = mo.group(1)
			return ver
	return None

class Version(Command):
	description = "update _version.py from Git repo"
	user_options = []
	boolean_options = []
	def initialize_options(self):
		pass
	def finalize_options(self):
		pass
	def run(self):
		update_version_py()
		print "Version is now", get_version()

class sdist(_sdist):
	def run(self):
		update_version_py()
		# unless we update this, the sdist command will keep using the old
		# version
		self.distribution.metadata.version = get_version()
		return _sdist.run(self)

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
		long_description = f.read()

try:
		from setuptools.command.build_py import build_py
except ImportError:
		from distutils.command.build_py import build_py

import py_compile

class custom_build_pyc(build_py):
	def byte_compile(self, files):
		for file in files:
			if file.endswith('.py') and not file.endswith('_version.py'):
				py_compile.compile(file)
				os.unlink(file)

setup(
		cmdclass = { "build_py": custom_build_pyc, "version": Version, "sdist": sdist },
		name='mpos',
		version=get_version(),
		description='A Milk POS application',
		long_description=long_description,
		url='https://github.com/cackharot/ngen-milk-pos',

		# Author details
		author='cackharot',
		author_email='cackharot@gmail.com',

		license='Apache License',

		classifiers=[
				# How mature is this project? Common values are
				#   3 - Alpha
				#   4 - Beta
				#   5 - Production/Stable
				'Development Status :: 3 - Alpha',

				# Indicate who your project is intended for
				'Intended Audience :: Developers',
				'Topic :: Software Development :: Build Tools',

				# Pick your license as you wish (should match "license" above)
				'License :: OSI Approved :: Apache License',

				# Specify the Python versions you support here. In particular, ensure
				# that you indicate whether you support Python 2, Python 3 or both.
				'Programming Language :: Python :: 2.7',
		],

		# What does your project relate to?
		keywords='dairy, milk point of sales',

		# You can just specify the packages manually here if your project is
		# simple. Or you can use find_packages().
		packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

		install_requires=['flask'],

		extras_require={
				'dev': ['check-manifest'],
				'test': ['coverage'],
		},

		# If there are data files included in your packages that need to be
		# installed, specify them here.  If using Python 2.6 or less, then these
		# have to be included in MANIFEST.in as well.
		package_data={
				'mpos': ['config/.xinitrc','config/*'],
				'mpos.web': ['*.ini',
						'*.sh',
						'*.cfg',
						'*.pot',
						'*.po',
						'*.mo',
						'translations/*.*',
						'translations/ta/LC_MESSAGES/*.*',
						'templates/*.jinja2',
						'templates/reports/*.jinja2',
						'templates/thermal/*.jinja2',
						'templates/macros/*.jinja2',
						'static/css/*.*',
						'static/js/*.*',
						'static/js/vendor/*.*',
						'static/fonts/*.*',
						'static/images/*.*'
						],
		},

		include_package_data = True,

		# Although 'package_data' is the preferred approach, in some case you may
		# need to place data files outside of your packages. See:
		# http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
		# In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
		#data_files=[('my_data', ['data/data_file'])],

		# To provide executable scripts, use entry points in preference to the
		# "scripts" keyword. Entry points provide cross-platform support and allow
		# pip to create the appropriate form of executable for the target platform.
		entry_points={
				'console_scripts': [
						'mpos_initdb=web.initdb:create_db',
				],
		},
)
