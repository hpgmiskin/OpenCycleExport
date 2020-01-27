import unittest

import json
import os.path


def get_data_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)


def load_test_data(filename):
    with open(get_data_path(filename)) as test_data_file:
        return json.load(test_data_file)
