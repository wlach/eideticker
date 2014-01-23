from setuptools import setup, find_packages
setup(
    name="eideticker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'mozdevice>=0.31', 'mozlog>=1.5', 'mozprofile>=0.19',
        'moznetwork>=0.24', 'mozhttpd>=0.7', 'BeautifulSoup',
        'gaiatest>=0.21.3', 'httplib2', 'b2gpopulate>=0.12'])

# FIXME: Compile decklink-capture script automatically
