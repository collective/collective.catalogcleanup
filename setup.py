# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '1.7.1'

setup(name='collective.catalogcleanup',
      version=version,
      description="Remove outdated items from the catalog",
      long_description=(open("README.rst").read() + "\n" +
                        open("CHANGES.rst").read()),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Framework :: Plone :: 3.3",
          "Framework :: Plone :: 4.0",
          "Framework :: Plone :: 4.1",
          "Framework :: Plone :: 4.2",
          "Framework :: Plone :: 4.3",
          "Framework :: Plone :: 5.0",
          "Framework :: Plone :: 5.1",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.4",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
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
              'plone.app.testing',
          ],
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
