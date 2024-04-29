from setuptools import setup, find_packages

setup(
    name='gpt_wss_api',
    version='0.1.0',
    author='Yuanzhang Hu',
    author_email='huyuanzhang@gmail.com',
    packages=find_packages(),
    url='http://pypi.python.org/pypi/gpt_wss_api/',
    license='LICENSE.txt',
    description='An awesome package for chatGPT WebSocket communication.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
       'Brotli==1.1.0',
       'certifi==2024.2.2',
       'cffi==1.16.0',
       'charset-normalizer==3.3.2',
       'cryptography==36.0.1',
       'hpack==4.0.0',
       'idna==3.7',
       'pyasn1==0.6.0',
       'pycparser==2.22',
       'pyhttpx==2.10.12',
       'pyOpenSSL==21.0.0',
       'PySocks==1.7.1',
       'requests==2.31.0',
       'rsa==4.8',
       'six==1.16.0',
       'urllib3==2.2.1'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)