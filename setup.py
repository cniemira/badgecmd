import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = """Badge commander
"""

requires = [
    'PyQt5',
    'pyserial'
    ]

setup(name='badgecmd',
      author='CJ Niemira',
      author_email='siege@siege.org',
      version='0.1',
      description='Badge commander',
      long_description=README,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python'
      ],
      url='https://github.com/cniemira/badgecmd',
      keywords='badge',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points="""\
      [console_scripts]
      badgebyte = badgecmd.badgebus:cli
      badgegui = badgecmd.gui:main
      """,
      )
