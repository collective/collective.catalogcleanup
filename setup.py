# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '1.11.1'

setup(name='collective.catalogcleanup',
      version=version,
      description="Remove outdated items from the catalog",
      long_description=(open("README.rst").read() + "\n" +
                        open("CHANGES.rst").read()),
      # Get more strings from https://pypi.org/classifiers/
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Framework :: Plone",
          "Framework :: Plone :: 4.3",
          "Framework :: Plone :: 5.1",
          "Framework :: Plone :: 5.2",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.7",
          "License :: OSI Approved :: GNU General Public License (GPL)",
      ],
      keywords='plone catalog cleanup',
      author='Maurits van Rees',
      author_email='m.van.rees@zestsoftware.nl',
      url='https://github.com/collective/collective.catalogcleanup',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
      ],
      extras_require={
          'test': [
              'collective.noindexing',
              'plone.app.robotframework',
              'plone.app.testing',
          ],
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
