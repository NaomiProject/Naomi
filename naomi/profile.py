# -*- coding: utf-8 -*-
"""
These functions "walk" the profile, and return either a boolean variable to
tell whether an option is configured or not, or the actual value
"""
import logging
from naomi import paths
import os
from . import populate
import re
import shutil
import yaml

_profile = {}
_profile_read = False
_test_profile = False


def set_profile(custom_profile):
    """
    Set the profile to a custom value. This is especially helpful when testing
    """
    global _profile, _profile_read, _test_profile
    _profile = custom_profile
    _test_profile = True
    _profile_read = True


def get_profile(command=""):
    global _profile, _profile_read, _test_profile
    _logger = logging.getLogger(__name__)
    command = command.strip().lower()
    if command == "reload":
        _profile_read = False
    elif command != "":
        raise ValueError("command '{}' not understood".format(command))
    if not _profile_read:
        # Open and read the profile
        # Create .naomi dir if it does not exist yet
        if not os.path.exists(paths.SUB_PATH):
            try:
                os.makedirs(paths.SUB_PATH)
            except OSError:
                _logger.error(
                    "Could not create .naomi dir: '{}'".format(
                        paths.SUB_PATH
                    ),
                    exc_info=True
                )
                raise

        # Check if .naomi dir is writable
        if not os.access(paths.SUB_PATH, os.W_OK):
            _logger.critical(
                " ".join([
                    ".naomi dir {:s} is not writable. Naomi",
                    "won't work correctly."
                ]).format(
                    paths.SUB_PATH
                )
            )
        # Create .naomi/configs dir if it does not exist yet
        if not os.path.exists(paths.CONFIG_PATH):
            try:
                os.makedirs(paths.CONFIG_PATH)
            except OSError:
                _logger.error(
                    "Could not create .naomi/configs dir: '{}'".format(
                        paths.CONFIG_PATH
                    ),
                    exc_info=True
                )
                raise

        # Check if .naomi/configs dir is writable
        if not os.access(paths.CONFIG_PATH, os.W_OK):
            _logger.critical(
                " ".join([
                    ".naomi/configs dir {:s} is not writable. Naomi",
                    "won't work correctly."
                ]).format(
                    paths.CONFIG_PATH
                )
            )
        # For backwards compatibility, move old profile.yml to newly
        # created config dir
        old_configfile = paths.sub('profile.yml')
        new_configfile = paths.sub(os.path.join('configs', 'profile.yml'))
        if os.path.exists(old_configfile):
            if os.path.exists(new_configfile):
                _logger.warning(
                    " ".join([
                        "Deprecated profile file found: '{:s}'. ",
                        "Please remove it."
                    ]).format(old_configfile)
                )
            else:
                _logger.warning(
                    " ".join([
                        "Deprecated profile file found: '{:s}'.",
                        "Trying to move it to new location '{:s}'."
                    ]).format(
                        old_configfile,
                        new_configfile
                    )
                )
                try:
                    shutil.move(old_configfile, new_configfile)
                except shutil.Error:
                    _logger.error(
                        " ".join([
                            "Unable to move config file.",
                            "Please move it manually.",
                            "“{} → {}”".format(old_configfile, new_configfile)
                        ]),
                        exc_info=True
                    )
                    raise

        # Read config
        # set a loop so we can keep looping back until the config file exists
        config_read = False
        while(not config_read):
            try:
                with open(new_configfile, "r") as f:
                    _profile = yaml.safe_load(f)
                    _profile_read = True
                    config_read = True
            except IOError:
                print("Your config file does not exist.")
                text_input = input(
                    " ".join([
                        "Would you like to answer a few ",
                        "questions to create a new one? "
                    ])
                )
                if(re.match(r'\s*[Yy]', text_input)):
                    _profile_read = True
                    populate.run()
                    config_read = True
                else:
                    print("Cannot continue. Exiting.")
                    quit()
            except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
                _logger.error(
                    "Unable to parse config file: {} {}".format(
                        e.problem.strip(),
                        str(e.problem_mark).strip()
                    )
                )
                raise
        configfile = paths.config('profile.yml')
        with open(configfile, "r") as f:
            _profile = yaml.safe_load(f)
        _profile_read = True
        _test_profile = False
    return _profile


def save_profile():
    global _profile, _profile_read, _test_profile
    # I want to make sure the user's profile is never accidentally overwritten
    # with a test profile.
    if not _test_profile:
        # Save the profile
        if not os.path.exists(paths.CONFIG_PATH):
            os.makedirs(paths.CONFIG_PATH)
        outputFile = open(paths.config("profile.yml"), "w")
        yaml.dump(get_profile(), outputFile, default_flow_style=False)


def get_profile_var(path, default=None):
    """
    Get a value from the profile, whether it exists or not
    If the value does not exist in the profile, returns
    either the default value (if there is one) or None.
    """
    response = _walk_profile(path, True)
    if response is None:
        response = default
    return response


def get_profile_flag(path, default=None):
    """
    Get a boolean value from the profile, whether it exists
    or not. If the value does not exist, returns default or
    None
    """
    # Get the variable value
    temp = str(_walk_profile(path, True))
    if(temp is None):
        # the variable is not defined
        temp = default
    response = False
    if str(temp).strip().lower() in ('true', 'yes', 'on'):
        response = True
    return response


def check_profile_var_exists(path):
    """
    Checks if an option exists in the test_profile it is using.
    Option is passed in as a list so that if we need to check
    if a suboption exists, we can pass the full path to it.
    """
    return _walk_profile(path, False)


def _walk_profile(path, returnValue):
    """
    Function to walk the profile
    """
    profile = get_profile()
    found = True
    for branch in path:
        try:
            profile = profile[branch]
        except KeyError:
            found = False
            profile = None
            break
    if(returnValue):
        response = profile
    else:
        response = found
    return response


def set_profile_var(path, value):
    global _profile
    temp = _profile
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
