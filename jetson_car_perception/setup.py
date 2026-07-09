import os
from glob import glob
from setuptools import setup


package_name = 'jetson_car_perception'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
         glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='maksym',
    maintainer_email='chernmakc@gmail.com',
    description='Perception stack for jetson car',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'fake_depth_publisher = jetson_car_perception.fake_depth_publisher:main',
            'mono_vo = jetson_car_perception.mono_vo:main',
            'odom_to_path = jetson_car_perception.odom_to_path:main',
            'tf_relay = jetson_car_perception.tf_relay:main',
        ],
    },
)