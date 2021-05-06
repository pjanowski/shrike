# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Importer script
Can import a function from a given script from file path
"""
import sys
import traceback
import importlib.util


def dynamic_import_class(module_path, class_name):
    """Dynamically imports some class/function from a python file

    Args:
        module_path (str) : path to python file (ex: ./bla/foo.py)
        class_name (str) : name of class/function to import from it

    Returns:
        class_attr (class) : object imported from module
    """
    spec = importlib.util.spec_from_file_location("dynimportmodulename", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    class_attr = getattr(mod, class_name)
    return class_attr


def dynamic_import_module(module_path):
    """Dynamically imports some class/function from a python file

    Args:
        module_path (str) : path to python file (ex: ./bla/foo.py)

    Returns:
        mod, spec
    """
    spec = importlib.util.spec_from_file_location("dynimportmodulename", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return spec, mod


def import_and_test_class(module_path, class_name):
    """Tests importing some class/function from a python file

    Args:
        module_path (str) : path to python file (ex: ./bla/foo.py)
        class_name (str) : name of class/function to import from it

    Returns:
        class_attr (class) : object imported from module
    """
    # WORK IN PROGRESS
    # test if module_path can be found in path
    # test if class_name exists in module_path
    # test return attr if class
    import_success = True
    message = None
    try:
        imported_class = dynamic_import_class(module_path, class_name)
    except:
        import_success = False
        message = traceback.format_exc()

    assert import_success, """
        Importing class '{}' from module path '{}' did not succeed.
        Current python path is {}.
        Traceback from exception:
        {}
        """.format(
        class_name, module_path, sys.path, message
    )

    return imported_class
