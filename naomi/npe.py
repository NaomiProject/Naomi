# -*- coding: utf-8 -*-
# Naomi Plugin Exchange
import csv
import io
import logging
import os
import re
import shutil
import urllib
from . import paths
from . import pluginstore
from . import profile
from .run_command import run_command
from .strcmpci import strcmpci


DEFAULT_PLUGIN_URL = "/".join([
    "https://raw.githubusercontent.com",
    "NaomiProject",
    "naomi-plugins",
    "master",
    "plugins.csv"
])


class npe:
    def __init__(self, application):
        global _
        self._logger = logging.getLogger(__name__)
        self._application = application
        _ = application.gettext

    # This is a standardized function for getting all the plugins available
    # from all the repositories the user has enabled in their profile
    def get_remote_plugin_repositories(self, plugins=None):
        csvfile = []
        repositories = profile.get(
            ['plugin_repositories'],
            {DEFAULT_PLUGIN_URL: "Enabled"}
        )
        for url in repositories:
            if repositories[url] == 'Enabled':
                self._logger.info("Reading {}".format(url))
                # It would be good if we could actually read the csv file line
                # by line rather than reading it all into memory, but that
                # might require some custom code. For right now, we'll use the
                # python tools.
                # I should set up a context manager for this anyway, since I
                # am processing multiple urls.
                # The nosec comment on the next line has to be there to say
                # "Yes, I know I'm doing something unsecure" or codacy has a
                # fit
                with urllib.request.urlopen(urllib.request.Request(url)) as f:  # nosec
                    file_contents = f.read().decode('utf-8')
                for line in csv.DictReader(
                    io.StringIO(file_contents),
                    delimiter=',',
                    quotechar='"'
                ):
                    if line not in csvfile:
                        csvfile.append(line)
        # Because the plugin information can be coming from multiple sources,
        # we are now in a situation where different versions of a plugin can
        # be listed in multiple repositories, and there is definitely the
        # possibility of two different repositories having different plugins
        # with the same name, or different versions of the same plugin.
        return csvfile

    # Functions for plugin management
    # This returns a dictionary of the active plugins using the lower case
    # plugin name as the key, with the plugin object itself as the value.
    # {'plugin1': <naomi.pluginstore.PluginInfo object>, 'plugin2': ...}
    # This does not include plugins that have been installed but disabled.
    def list_active_plugins(self):
        plugins = self._application.plugins.get_plugins()
        # Sort these alphabetically by name
        plugins_sorted = {}
        for info in plugins:
            plugins_sorted[info.name.lower()] = info
        return plugins_sorted

    # This returns a dictionary of plugins that are available to be
    # installed.
    def list_available_plugins(self, categories):
        installed_plugins = {}
        for category in self._application.plugins._categories_map:
            # Get a list of installed plugins in each category
            superclass = self._application.plugins._categories_map[category]
            for info in self._application.plugins._plugins.values():
                if issubclass(info.plugin_class, superclass):
                    if(category not in installed_plugins):
                        installed_plugins[category] = {}
                    installed_plugins[category][info.name] = info.version
        # Get the list of available plugins:
        csvfile = self.get_remote_plugin_repositories()
        print_plugins = {}
        flat_cat = [y for x in categories for y in x]
        for row in csvfile:
            if len(flat_cat):
                if(row["Category"] in [y for x in categories for y in x]):
                    print_plugins[row["Name"].lower()] = pluginstore.printplugin(row, installed_plugins)
            else:
                print_plugins[row["Name"].lower()] = pluginstore.printplugin(row, installed_plugins)
        return print_plugins

    # Right now what install_plugins does is git clone the plugin into the
    # user's plugin dir (~/.config/naomi/plugins) and then run install.py if there
    # is one, or python_requirements.txt if there is one.
    def install_plugins(self, plugins):
        flat_plugins = [" ".join(x) for x in plugins]
        # flat_plugins = [y for x in plugins for y in x]
        print(flat_plugins)
        csvfile = self.get_remote_plugin_repositories(flat_plugins)
        for row in csvfile:
            # Keeps track of any failure inside the naming while loop
            fail = False
            if(row['Name'] in flat_plugins):
                print(_('Installing {}...').format(row['Name']))
                # install it to the user's plugin directory
                install_dir = paths.sub(
                    os.path.join(
                        'plugins',
                        row['Category']
                    )
                )
                # Make sure the install dir exists
                if not os.path.isdir(install_dir):
                    os.makedirs(install_dir)
                # We aren't capturing the actual name of the directory.
                # The name of the directory does not matter, so we should just
                # create one. Replace any spaces in the plugin name with
                # underscores.
                install_name = re.sub('\W', '', re.sub('\s', '_', row['Name']))
                install_to_base = os.path.join(install_dir, install_name)
                install_to = install_to_base
                rev = 0
                installed_url = ""
                while(os.path.isdir(install_to)):
                    # Check if the git fetch url is the same. If so, then
                    # this is the same plugin and just needs to be updated.
                    # If not, then this is a different plugin, so rename the
                    # install_to directory.
                    installed_url = ""
                    cmd = [
                        "git",
                        '-C', install_to,
                        "remote", "-v"
                    ]
                    completed_process = run_command(cmd, 1)
                    # # This is how you can get the URL from the info file
                    # # instead of git:
                    # installed_url = self._application.plugins.parse_plugin(install_to)

                    # This could easily fail, if this directory is not
                    # actually a git directory
                    if(completed_process.returncode == 0):
                        installed_url = completed_process.stdout.decode(
                            "UTF-8"
                        ).split("\n")[0].split("\t")[1].split()[0]
                    if(strcmpci(
                        installed_url,
                        row['Repository']
                    )):
                        # It's the same plugin
                        # Just go ahead and reset the head and do
                        # a git pull origin.
                        # The following assumes there is a master branch:
                        cmd = [
                            'git',
                            '-C', install_to,
                            'checkout',
                            'master'
                        ]
                        completed_process = run_command(cmd, 2)
                        if(completed_process.returncode == 0):
                            # break out of the loop
                            break
                        else:
                            print(_('Unable to reset plugin "{}": {}').format(
                                row['Name'],
                                completed_process.stderr.decode("UTF-8")
                            ))
                            fail = True  # next line from csv
                            break
                        cmd = [
                            'git',
                            '-C', install_to,
                            'pull',
                            'origin'
                        ]
                        completed_process = run_command(cmd, 2)
                        if(completed_process.returncode == 0):
                            # break out of the while loop
                            break
                        else:
                            print(_('Unable to update plugin "{}": {}').format(
                                row['Name'],
                                completed_process.stderr.decode("UTF-8")
                            ))
                            fail = True  # next line from csv
                            break
                    else:
                        rev += 1
                        install_to = "_".join([install_to_base, str(rev)])
                if(fail):
                    continue
                if(not os.path.isdir(install_to)):
                    cmd = [
                        'git',
                        'clone',
                        row['Repository'],
                        install_to
                    ]
                    completed_process = run_command(cmd, 2)
                    if(completed_process.returncode != 0):
                        print(completed_process.stderr.decode("UTF-8"))
                if(os.path.isdir(install_to)):
                    # checkout the specific commit
                    cmd = [
                        'git',
                        '--git-dir={}/.git'.format(install_to),
                        '--work-tree={}'.format(install_to),
                        'checkout',
                        row['Commit']
                    ]
                    completed_process = run_command(cmd, 2)
                    if(completed_process.returncode != 0):
                        print(completed_process.stderr.decode("UTF-8"))
                        # At this point, we have a potentially rogue
                        # copy of the plugin, with code that has not
                        # been vetted.
                        # A developer could easily force this condition
                        # by simply deleting the vetted commit from their
                        # repository. At that point, anyone who installed
                        # the plugin would get whatever the current state
                        # is.
                        print(_("Failed to set head to the vetted commit"))
                        print(_("Deleting {}".format(install_to)))
                        shutil.rmtree(install_to)
                    else:
                        # check and see if there is an install.py file
                        install_file = os.path.join(install_to, "install.py")
                        if os.path.isfile(install_file):
                            # run that
                            run_command(install_file)
                        else:
                            required_file = os.path.join(
                                install_dir,
                                "python_requirements.txt"
                            )
                            if os.path.isfile(required_file):
                                # Install any python packages required
                                cmd = [
                                    'pip3',
                                    'install',
                                    '--user',
                                    '--requirement',
                                    required_file
                                ]
                                run_command(cmd)
                        # Since the plugin will request its own settings each
                        # time it is run with settings missing, no need to set
                        # that up now.
                        self._application.plugins.detect_plugins()
                        self.enable_plugins([[row['Name']]])
                        print(_('Plugin "{}" installed to {}').format(
                            row['Name'],
                            install_to
                        ))

    def update_plugins(self, plugins):
        returnMessage = ""
        flat_plugins = [" ".join(x) for x in plugins]
        csvfile = self.get_remote_plugin_repositories()
        for row in csvfile:
            if(row['Name'] in flat_plugins):
                # Find the plugin
                found_plugin = False
                for info in self._application.plugins._plugins.values():
                    if(info.name == row["Name"]):
                        found_plugin = True
                        plugin_dir = info._path
                        # FIXME check if the urls are the same, if not, then
                        # this is probably a different plugin with the same
                        # name.
                        # It probably makes the most sense to check the
                        # git remote -v origin url, since that is the one
                        # actually used, and the url in info may be unreliable
                        returnMessage += _("Updating {}\n").format(row["Name"])
                        if(info.version == row['Version']):
                            returnMessage += _(
                                "{} versions identical ({}), updating anyway\n"
                            ).format(
                                row['Name'],
                                info.version
                            )
                        else:
                            returnMessage += _(
                                "Updating {} from {} to {}\n"
                            ).format(
                                row["Name"],
                                info.version,
                                row["Version"]
                            )
                        # checkout the specific commit
                        cmd = [
                            'git',
                            '--git-dir={}/.git'.format(plugin_dir),
                            '--work-tree={}'.format(plugin_dir),
                            'checkout',
                            row['Commit']
                        ]
                        completed_process = run_command(cmd, 2)
                        if(completed_process.returncode != 0):
                            returnMessage += "{}\n".format(
                                completed_process.stderr.decode("UTF-8")
                            )
                            returnMessage += _("Failed to set head to the vetted commit")
                        else:
                            # check and see if there is an install.py file
                            install_file = os.path.join(
                                plugin_dir,
                                "install.py"
                            )
                            if os.path.isfile(install_file):
                                # run that
                                run_command(install_file)
                            else:
                                required_file = os.path.join(
                                    plugin_dir,
                                    "python_required.txt"
                                )
                                if os.path.isfile(required_file):
                                    # Install any python packages required
                                    cmd = [
                                        'pip3',
                                        'install',
                                        '--user',
                                        '--requirement',
                                        required_file
                                    ]
                                    run_command(cmd)
                            # Since the plugin will request its own settings
                            # each time it is run with settings missing, no
                            # need to set that up now.
                            self._application.plugins.detect_plugins()
                            self.enable_plugins([[row['Name']]])
                            returnMessage += _('Plugin "{}" Updated\n').format(row['Name'])
                if not found_plugin:
                    returnMessage += _("Plugin {} was not found.").format(row["Name"])
                    returnMessage += _("Are you sure it is installed?")

    # I don't know what we want this to do. If this is a plugin in the user's
    # directory, then delete it. If it is a directory in the main naomi dir,
    # then disable it.
    # If silent is set to True, then do not prompt the user. This allows
    # this function to be used from a script.
    def remove_plugins(self, plugins, silent=False):
        flat_plugins = [" ".join(x) for x in plugins]
        returnMessage = ""
        for plugin in flat_plugins:
            plugin_found = False
            for info in self._application.plugins._plugins.values():
                if(info.name == plugin):
                    plugin_found = True
                    if(paths.sub() == info._path[:len(paths.sub())]):
                        returnMessage += _('Removing plugin "{}"\n').format(info.name)
                        if(silent or self._application._interface.simple_yes_no("Are you sure?")):
                            # FIXME Remove the plugin line from profile.yml
                            # This would require using del or pop to remove
                            # the key, but would have to traverse the tree
                            # until we reach the key first.
                            returnMessage += _("Removing directory: {}").format(info._path)
                            shutil.rmtree(info._path)
                            plugin_category = info._path.split(os.path.sep)[
                                len(info._path.split(os.path.sep)) - 2
                            ]
                            profile.remove_profile_var([
                                'plugins',
                                plugin_category,
                                info.name
                            ])
                            profile.save_profile()
                    else:
                        self.disable_plugins([[info.name]])
            if(not plugin_found):
                returnMessage += _('Could not locate plugin "{}" ({})').format(
                    plugin,
                    _("has it been disabled?\n")
                )
        return returnMessage

    @staticmethod
    def enable_plugins(plugins):
        returnMessage = ""
        flat_plugins = [" ".join(x) for x in plugins]
        plugins_enabled = 0
        for plugin in flat_plugins:
            plugin_enabled = False
            # Being disabled, the plugin won't be in self._application.plugins
            # We need to search every plugin category in profile.plugins
            for category in profile.get_profile_var(['plugins']):
                if(plugin in profile.get_profile_var(['plugins', category])):
                    if(profile.get_profile_var([
                        'plugins',
                        category,
                        plugin
                    ]) == 'Enabled'):
                        returnMessage += _('Plugin "{}" is enabled').format(plugin)
                        plugin_enabled = True
                    else:
                        profile.set_profile_var(
                            [
                                'plugins',
                                category,
                                plugin
                            ],
                            'Enabled'
                        )
                        returnMessage += _('Enabled plugin "{}"\n').format(plugin)
                        plugin_enabled = True
                        plugins_enabled += 1
            if(not plugin_enabled):
                returnMessage += _('Unable to enable plugin "{}"\n').format(plugin)
        if(plugins_enabled > 0):
            profile.save_profile()
        return returnMessage

    def disable_plugins(self, plugins):
        returnMessage = ""
        flat_plugins = [" ".join(x) for x in plugins]
        plugins_disabled = 0
        # We don't know what category the plugin is in from just the name
        # so the first thing we have to do is figure out the category
        plugin_category = None
        # Being enabled, the plugin should appear in self._application.plugins
        for plugin in flat_plugins:
            plugin_disabled = False
            for info in self._application.plugins._plugins.values():
                if(info.name == plugin):
                    plugin_category = info._path.split(os.path.sep)[
                        len(info._path.split(os.path.sep)) - 2
                    ]
            if(not plugin_category):
                # If we were not able to find the plugin in self._application.plugins
                # check the profile directly. The plugin may have been skipped
                # due to a syntax error or missing depenency.
                for category in profile.get_profile_var(['plugins']):
                    if(plugin in profile.get_profile_var([
                        'plugins',
                        category
                    ])):
                        plugin_category = category
            if(plugin_category):
                if(profile.get_profile_var([
                    'plugins',
                    plugin_category,
                    plugin
                ]) == 'Disabled'):
                    returnMessage += _('Plugin "{}" is disabled\n').format(plugin)
                    plugin_disabled = True
                else:
                    profile.set_profile_var(
                        [
                            'plugins',
                            plugin_category,
                            plugin
                        ],
                        'Disabled'
                    )
                    returnMessage += _('Disabled plugin "{}"\n').format(plugin)
                    plugin_disabled = True
                    plugins_disabled += 1
            if(not plugin_disabled):
                returnMessage += _('Unable to disable plugin "{}"\n').format(plugin)
        if(plugins_disabled > 0):
            profile.save_profile()
        return returnMessage
