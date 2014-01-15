from setuptools import setup, find_packages
setup(
    name = "eideticker",
    version = "0.1.0",
    packages = find_packages(),
    install_requires = [ 'mozdevice', 'BeautifulSoup', 'gaiatest>=0.21.3', 'httplib2', 'b2gpopulate>=0.12' ]
)

# FIXME: Compile decklink-capture script automatically
