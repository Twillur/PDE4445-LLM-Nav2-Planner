import os
from glob import glob

from setuptools import find_packages, setup

package_name = "nl_nav2_executor"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "maps"), glob("maps/*")),
        (os.path.join("share", package_name, "worlds"), glob("worlds/*")),
        (os.path.join("share", package_name, "params"), glob("params/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="William",
    maintainer_email="williamkoju@gmail.com",
    description="Executes an LLM waypoint plan on Nav2 in a Gazebo warehouse.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "execute_plan = nl_nav2_executor.executor_node:main",
        ],
    },
)
