# ----------------------------------------------------------------------------
# Copyright (c) 2013--, scikit-bio development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function
import unittest
import inspect
import warnings

from skbio.util import classproperty, overrides
from skbio.util._decorator import (stable, experimental, deprecated,
                                   _state_decorator)
from skbio.util._exception import OverrideError


class TestOverrides(unittest.TestCase):
    def test_raises_when_missing(self):
        class A(object):
            pass

        with self.assertRaises(OverrideError):
            class B(A):
                @overrides(A)
                def test(self):
                    pass

    def test_doc_inherited(self):
        class A(object):
            def test(self):
                """Docstring"""
                pass

        class B(A):
            @overrides(A)
            def test(self):
                pass

        self.assertEqual(B.test.__doc__, "Docstring")

    def test_doc_not_inherited(self):
        class A(object):
            def test(self):
                """Docstring"""
                pass

        class B(A):
            @overrides(A)
            def test(self):
                """Different"""
                pass

        self.assertEqual(B.test.__doc__, "Different")


class TestClassProperty(unittest.TestCase):
    def test_getter_only(self):
        class Foo(object):
            _foo = 42

            @classproperty
            def foo(cls):
                return cls._foo

        # class-level getter
        self.assertEqual(Foo.foo, 42)

        # instance-level getter
        f = Foo()
        self.assertEqual(f.foo, 42)

        with self.assertRaises(AttributeError):
            f.foo = 4242


class TestStabilityState(unittest.TestCase):
    # the indentation spacing gets weird, so I'm defining the
    # input doc string explicitly and adding it after function
    # defintion
    _test_docstring = (" Add 42, or something else, to x.\n"
                       "\n"
                       "    Parameters\n"
                       "    ----------\n"
                       "    x : int, x\n"
                       "    y : int, optional\n")


class TestBase(TestStabilityState):

    def test_get_indentation_level(self):

        c = _state_decorator()
        self.assertEqual(c._get_indentation_level([]), 0)
        self.assertEqual(
            c._get_indentation_level([], default_no_existing_docstring=3), 3)
        self.assertEqual(c._get_indentation_level([""]), 4)
        self.assertEqual(
            c._get_indentation_level([""], default_existing_docstring=3), 3)

        in_ = (["summary"])
        self.assertEqual(c._get_indentation_level(in_), 4)
        in_ = (["summary", "", "", "    ", "", " ", ""])
        self.assertEqual(c._get_indentation_level(in_), 4)

        in_ = (["summary", "     More indentation", " Less indentation"])
        self.assertEqual(c._get_indentation_level(in_), 5)

    def test_update_docstring(self):
        c = _state_decorator()
        in_ = None
        exp = ("""State: Test!!""")
        self.assertEqual(c._update_docstring(in_, "Test!!"), exp)

        in_ = """"""
        exp = ("""\n\n    State: Test!!""")
        self.assertEqual(c._update_docstring(in_, "Test!!"), exp)

        in_ = ("""Short summary\n\n    Parameters\n\n----------\n    """
               """x : int\n""")
        exp = ("""Short summary\n\n    State: Test!!\n\n"""
               """    Parameters\n\n----------\n    x : int\n""")
        self.assertEqual(c._update_docstring(in_, "Test!!"), exp)

        in_ = ("""Short summary\n\n      Parameters\n\n----------\n      """
               """x : int\n""")
        exp = ("""Short summary\n\n      State: Test!!\n\n"""
               """      Parameters\n\n----------\n      x : int\n""")
        self.assertEqual(c._update_docstring(in_, "Test!!"), exp)

        in_ = ("""Short summary\n\n    Parameters\n\n----------\n    """
               """x : int\n""")
        exp = ("""Short summary\n\n    State: Test!!Test!!Test!!Test!!Test!!"""
               """Test!!Test!!Test!!Test!!Test!!Test!!Te\n           st!!T"""
               """est!!Test!!Test!!Test!!Test!!Test!!Test!!Test!!\n\n"""
               """    Parameters\n\n----------\n    x : int\n""")
        self.assertEqual(c._update_docstring(in_, "Test!!"*20), exp)


class TestStable(TestStabilityState):

    def _get_f(self, as_of):
        def f(x, y=42):
            return x + y
        f.__doc__ = self._test_docstring
        f = stable(as_of=as_of)(f)
        return f

    def test_function_output(self):
        f = self._get_f('0.1.0')
        self.assertEqual(f(1), 43)

    def test_function_docstring(self):
        f = self._get_f('0.1.0')
        e1 = (" Add 42, or something else, to x.\n\n"
              "    State: Stable as of 0.1.0.\n\n"
              "    Parameters")
        self.assertTrue(f.__doc__.startswith(e1))
        f = self._get_f('0.1.1')
        e1 = (" Add 42, or something else, to x.\n\n"
              "    State: Stable as of 0.1.1.\n\n"
              "    Parameters")
        self.assertTrue(f.__doc__.startswith(e1))

    def test_function_signature(self):
        f = self._get_f('0.1.0')
        expected = inspect.ArgSpec(
            args=['x', 'y'], varargs=None, keywords=None, defaults=(42,))
        self.assertEqual(inspect.getargspec(f), expected)
        self.assertEqual(f.__name__, 'f')

    def test_missing_kwarg(self):
        self.assertRaises(ValueError, stable)
        self.assertRaises(ValueError, stable, '0.1.0')


class TestExperimental(TestStabilityState):

    def _get_f(self, as_of):
        def f(x, y=42):
            return x + y
        f.__doc__ = self._test_docstring
        f = experimental(as_of=as_of)(f)
        return f

    def test_function_output(self):
        f = self._get_f('0.1.0')
        self.assertEqual(f(1), 43)

    def test_function_docstring(self):
        f = self._get_f('0.1.0')
        e1 = (" Add 42, or something else, to x.\n\n"
              "    State: Experimental as of 0.1.0.\n\n"
              "    Parameters")
        self.assertTrue(f.__doc__.startswith(e1))
        f = self._get_f('0.1.1')
        e1 = (" Add 42, or something else, to x.\n\n"
              "    State: Experimental as of 0.1.1.\n\n"
              "    Parameters")
        self.assertTrue(f.__doc__.startswith(e1))

    def test_function_signature(self):
        f = self._get_f('0.1.0')
        expected = inspect.ArgSpec(
            args=['x', 'y'], varargs=None, keywords=None, defaults=(42,))
        self.assertEqual(inspect.getargspec(f), expected)
        self.assertEqual(f.__name__, 'f')

    def test_missing_kwarg(self):
        self.assertRaises(ValueError, experimental)
        self.assertRaises(ValueError, experimental, '0.1.0')


class TestDeprecated(TestStabilityState):

    def _get_f(self, as_of, until, reason):
        def f(x, y=42):
            return x + y
        f.__doc__ = self._test_docstring
        f = deprecated(as_of=as_of, until=until, reason=reason)(f)
        return f

    def test_function_output(self):
        f = self._get_f('0.1.0', until='0.1.4',
                        reason='You should now use skbio.g().')
        self.assertEqual(f(1), 43)

    def test_deprecation_warning(self):
        f = self._get_f('0.1.0', until='0.1.4',
                        reason='You should now use skbio.g().')
        # adapted from SO example here: http://stackoverflow.com/a/3892301
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            f(1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            expected_str = "is deprecated as of scikit-bio version 0.1.0"
            self.assertTrue(expected_str in str(w[-1].message))

    def test_function_docstring(self):
        f = self._get_f('0.1.0', until='0.1.4',
                        reason='You should now use skbio.g().')
        e1 = (" Add 42, or something else, to x.\n\n"
              "    .. note:: Deprecated as of 0.1.0 for "
              "removal in 0.1.4. You should now use\n"
              "              skbio.g().\n\n"
              "    Parameters")
        self.assertTrue(f.__doc__.startswith(e1))

        f = self._get_f('0.1.1', until='0.1.5',
                        reason='You should now use skbio.h().')
        e1 = (" Add 42, or something else, to x.\n\n"
              "    .. note:: Deprecated as of 0.1.1 for "
              "removal in 0.1.5. You should now use\n"
              "              skbio.h().\n\n"
              "    Parameters")
        self.assertTrue(f.__doc__.startswith(e1))

    def test_function_signature(self):
        f = self._get_f('0.1.0', until='0.1.4',
                        reason='You should now use skbio.g().')
        expected = inspect.ArgSpec(
            args=['x', 'y'], varargs=None, keywords=None, defaults=(42,))
        self.assertEqual(inspect.getargspec(f), expected)
        self.assertEqual(f.__name__, 'f')

    def test_missing_kwarg(self):
        self.assertRaises(ValueError, deprecated)
        self.assertRaises(ValueError, deprecated, '0.1.0')
        self.assertRaises(ValueError, deprecated, as_of='0.1.0')
        self.assertRaises(ValueError, deprecated, as_of='0.1.0', until='0.1.4')

if __name__ == '__main__':
    unittest.main()
