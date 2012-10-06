from distutils.core import setup
setup(name='ypload',
    version='1.1',
    description='Simple script to upload and publish files to Yandex.Disk',
    author='Grigory Bakunov',
    author_email='thebobuk@ya.ru',
    url='http://github.com/bobuk/ypload',
    py_modules=['ydisk'],
    scripts=['ypload'],
    requires     = [ 'requests'],
    license      = 'MIT',
)
