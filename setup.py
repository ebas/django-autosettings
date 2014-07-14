import setuptools

setuptools.setup(
    name='django-autosettings',
    version='0.1.0',
    description='Configure Django based on environment variables',
    author='Erik Bas',
    author_email='mail@erikbas.nl',
    py_modules=['autosettings'],
    install_requires=['dj_database_url'],
    zip_safe=False,
    keywords='django settings environment automatic',
)
