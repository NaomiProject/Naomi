# -*- coding: utf-8 -*-
"""
These functions "walk" the profile, and return either a boolean variable to
tell whether an option is configured or not, or the actual value
"""

def get_profile_var(profile, path, default=None):
    """
    Get a value from the profile, whether it exists or not
    If the value does not exist in the profile, returns None
    """
    response = _walk_profile(profile, path, True)
    if response is None:
        response = default
    return response


def check_profile_var_exists(profile, path):
    """
    Checks if an option exists in the test_profile it is using.
    Option is passed in as a list so that if we need to check
    if a suboption exists, we can pass the full path to it.
    """
    return _walk_profile(profile, path, False)


def _walk_profile(profile, path, returnValue):
    """
    Function to walk the profile
    """
    found = True
    for branch in path:
        try:
            profile = profile[branch]
        except KeyError:
            found = False
            profile = None
            break
    if(returnValue):
        response=profile
    else:
        response=found
    return response


def set_profile_var(profile, path, value):
    temp = profile
    if len(path) > 0:
        last = path[0]
        if len(path) > 1:
            for branch in path[1:]:
                try:
                    if not isinstance(temp[last], dict):
                        temp[last] = {}
                except KeyError:
                    temp[last] = {}
                temp = temp[last]
                last = branch
        temp[last] = value
    else:
        raise KeyError("Can't write to profile root")


