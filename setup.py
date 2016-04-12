from setuptools import setup

try:
    import multiprocessing  # noqa
except ImportError:
    pass

setup(
    setup_requires=["pbr"],
    pbr=True,
)
