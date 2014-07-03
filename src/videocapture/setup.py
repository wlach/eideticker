from setuptools import setup, find_packages
setup(
    name="videocapture",
    version="0.1.0",
    packages=find_packages(),
    install_requires=['numpy', 'pillow', 'scipy', 'futures >= 2.1.6']
)

# FIXME: Compile decklink-capture script automatically
