from grakn import duck
from nose.tools import *
import unittest


class TestDuckConstructor(unittest.TestCase):

    def test_duck_names_are_converted_into_strings(self):
        test_name = 123
        test_duck = duck.Duck(test_name)
        eq_(test_duck.name, str(test_name))

