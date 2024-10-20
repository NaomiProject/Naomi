import base64
import inspect
import logging
import hashlib
import os
import re
import shutil
import sys
import yaml
from cryptography.fernet import InvalidToken, Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from naomi.run_command import run_command
from naomi import paths


_profile = {}
_settings = {}
_profile_read = False
_test_profile = False
_args = {}
profile_file = ""


def set_arg(name, value):
    """Store an argument in a static location for all modules"""
    global _args
    _args.update({name: value})


def get_arg(name, default=None):
    """Retrieve an argument, return default if not set"""
    return _args.get(name, default)


def set_profile(custom_profile):
    """Set the profile to a custom value, useful for testing"""
    global _profile, _profile_read, _test_profile
    _profile = custom_profile
    _test_profile = True
    _profile_read = True


def get_profile(command=""):
    """Load the profile, reload if command is set to 'reload'"""
    global _profile, _profile_read, _test_profile, profile_file
    _logger = logging.getLogger(__name__)
    command = command.strip().lower()

    if command == "reload":
        _profile_read = False
    elif command:
        raise ValueError(f"Command '{command}' not understood")

    if not _profile_read:
        try:
            if not os.path.exists(paths.SUB_PATH):
                os.makedirs(paths.SUB_PATH)

            if not os.access(paths.SUB_PATH, os.W_OK):
                _logger.critical(f".config/naomi dir '{paths.SUB_PATH}' is not writable")

            if not os.path.exists(paths.CONFIG_PATH):
                os.makedirs(paths.CONFIG_PATH)

            if not os.access(paths.CONFIG_PATH, os.W_OK):
                _logger.critical(f".config/naomi/configs dir '{paths.CONFIG_PATH}' is not writable")

            new_configfile = paths.sub(os.path.join('configs', 'profile.yml'))
            old_configfile = paths.sub('profile.yml')

            if os.path.exists(old_configfile):
                if os.path.exists(new_configfile):
                    _logger.warning(f"Deprecated profile file found: '{old_configfile}'. Please remove it.")
                else:
                    shutil.move(old_configfile, new_configfile)

            profile_file = new_configfile

            config_read = False
            while not config_read:
                try:
                    with open(new_configfile, "r") as f:
                        _profile = yaml.safe_load(f) or {}
                        _profile_read = True
                        config_read = True
                except (FileNotFoundError, IOError):
                    _logger.info(f"{new_configfile} is missing")
                    set_arg("Profile_missing", True)
                    _profile = {'language': 'en-US'}
                    _profile_read = True
                    config_read = True
                except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
                    _logger.error(f"Unable to parse config file: {e.problem.strip()}, {str(e.problem_mark).strip()}")
                    raise
        except OSError as e:
            _logger.error(f"Error creating profile directories or accessing them: {str(e)}")
            raise

    return _profile


def save_profile():
    """Save the profile to disk, ensure test profiles aren't saved"""
    global _profile, _profile_read, _test_profile
    if _profile_read and not _test_profile:
        if not os.path.exists(paths.CONFIG_PATH):
            os.makedirs(paths.CONFIG_PATH)

        with open(paths.config("profile.yml"), "w") as output_file:
            yaml.dump(get_profile(), output_file, default_flow_style=False)


def get_profile_password(path, default=None):
    """Retrieve encrypted password from profile, if allowed"""
    _logger = logging.getLogger(__name__)
    allowed = [os.path.join(os.path.dirname(os.path.abspath(__file__)), fname) 
               for fname in ['app_utils.py', 'commandline.py', 'application.py']]
    filename = inspect.getframeinfo(sys._getframe(1)).filename

    if filename in allowed:
        path = [path] if isinstance(path, str) else path
        machine_id = run_command("cat /etc/machine-id".split(), capture=1).stdout
        first_id = hashlib.sha256(machine_id).hexdigest()

        second_id = hashlib.sha256(run_command("hostid".split(), capture=1).stdout).hexdigest()

        try:
            third_idb1 = run_command("blkid".split(), capture=1).stdout.decode().strip()
            third_id = hashlib.sha256(run_command(["grep", '-oP', 'UUID="\\K[^"]+'], capture=4, stdin=third_idb1).stdout).hexdigest()
        except FileNotFoundError:
            _logger.warning("Package 'blkid' not installed. Please install it manually.")
            third_id = ""

        salt = get_profile_key()
        kdf = PBKDF2HMAC(algorithm=hashes.SHA512(), length=32, salt=salt, iterations=100000, backend=default_backend())
        password = ''.join([first_id, second_id, third_id]).encode()
        key = base64.urlsafe_b64encode(kdf.derive(password))

        cipher_suite = Fernet(key)
        response = get_profile_var(path, None)
        try:
            if isinstance(response, str):
                response = cipher_suite.decrypt(response.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            _logger.error(f"Invalid encryption token for path {path}")
            response = None

        return response or default
    else:
        _logger.warning(f"Access to encrypted profile elements not allowed from {filename}")
        return None
