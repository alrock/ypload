from setuptools import setup

setup(name='ypload',
    version='1.2.3',
    description='Simple script to upload and publish files to Yandex.Disk',
    author='Grigory Bakunov',
    author_email='thebobuk@ya.ru',
    url='http://github.com/bobuk/ypload',
    py_modules=['ydisk'],
    scripts=['ypload'],
    install_requires=['requests>=0.12.0', ],
    license      = 'MIT',
)
