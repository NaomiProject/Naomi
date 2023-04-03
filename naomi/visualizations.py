# -*- coding: utf-8 -*-
import logging
from . import profile
_visualizations = []


def load_visualizations(self):
    # Inititalize Visualizations
    global _visualizations
    # Clear visualizations so visualizations are not doubled if this function is called more than once
    _visualizations = []
    for info in profile.get_arg('plugins').get_plugins_by_category(
        'visualizations'
    ):
        try:
            _visualizations.append(info.plugin_class(info))
        except Exception as e:
            self._logger.warning(
                "Plugin '%s' skipped! (Reason: %s)", info.name,
                e.message if hasattr(e, 'message') else 'Unknown',
                exc_info=(
                    self._logger.getEffectiveLevel() == logging.DEBUG
                )
            )


def run_visualization(visualization_name, *args, **kwargs):
    # the name of the visualization being run will be the first parameter,
    # followed by any parameters for the visualization
    for plugin in _visualizations:
        if visualization_name in dir(plugin):
            visualization = getattr(plugin, visualization_name)
            visualization(*args, **kwargs)
