# Luluwaku (自用)

A semi-auto TRPG engine running on PyPy.

## Why Python?

This project is initially written in C\#, but serialization support quickly turns out to be a severe pain.

The Python library `dill` helps to serialize the whole game state. Such capability is not available in C\# or C++.
