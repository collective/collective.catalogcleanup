from setuptools import find_packages
from setuptools import setup


version = "2.0.0"

setup(
    name="collective.catalogcleanup",
    version=version,
    description="Remove outdated items from the catalog",
    long_description=(open("README.rst").read() + "\n" + open("CHANGES.rst").read()),
    # Get more strings from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    keywords="plone catalog cleanup",
    author="Maurits van Rees",
    author_email="m.van.rees@zestsoftware.nl",
    url="https://github.com/collective/collective.catalogcleanup",
    license="GPL",
    packages=find_packages(exclude=["ez_setup"]),
    namespace_packages=["collective"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "plone.protect",
        "plone.uuid",
        "Products.CMFCore",
        "Products.CMFPlone",
        "setuptools",
    ],
    extras_require={
        "test": [
            "collective.noindexing",
            "plone.app.testing",
        ],
    },
    entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
)
