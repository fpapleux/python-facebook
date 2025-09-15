from setuptools import setup, find_packages

setup(
    name='facebook',               # Project name (can have hyphens)
    version='0.1.0',
    description='A Python client for facebook',
    author='Fabien Papleux',
    author_email='fabien@papleux.com',
    url='https://github.com/fpapleux/<repository name>',  # Optional
    packages=find_packages(),           # Automatically finds all packages named strapi_client and submodules
    install_requires=[
        'requests>=2.0.0'
    ],
    python_requires='>=3.7',
    include_package_data=True,          # Includes files from MANIFEST.in (if present)
    license='MIT',                      # Or your license
    classifiers=[                       # These help PyPI and others categorize your package
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)