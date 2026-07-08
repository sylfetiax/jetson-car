from setuptools import find_packages, setup
import os 
import glob

package_name = 'jetson_car_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            [f for f in glob.glob(os.path.join('launch', '*launch.py'))]),
        (os.path.join('share', package_name, 'worlds'),
            [f for f in glob.glob(os.path.join('worlds', '*.sdf'))]),
        (os.path.join('share', package_name, 'config'),
            [f for f in glob.glob(os.path.join('config', '*'))]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='maksym',
    maintainer_email='chernmakc@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
