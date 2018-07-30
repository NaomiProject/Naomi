# Contributing to Jasper

Want to contribute to Naomi ? Great ! :tada: We're always happy to have more contributors. Before you start developing, though, we ask that you read through this document in-full. It's full of tips and guidelines--if you skip it, you'll likely miss something important (and your pull request will probably be rejected as a result).

Throughout the process of contributing, there's one thing we'd like you to remember: Naomi, and previously Jasper, was developed (and is maintained) by what might be described as "volunteers". They earn no money for their work here and give their time solely for the advancement of the software and the enjoyment of its users. While they will do their best to get back to you regarding issues and pull requests, **your patience is appreciated**.

## Reporting Bugs

The [bug tracker](https://github.com/NaomiProject/Naomi/issues) at Github is for reporting bugs in Naomi. If encounter problems during installation or compliation of one of Naomi's dependencies for example, do not create a new issue here. Also, make sure that it's not a usage issue.

If you think that you found a bug and that you're using the most recent version of Jasper, please include a detailed description what you did and how to reproduce the bug. If Jasper crashes, run it with `--debug` as command line argument and also include the full stacktrace (not just the last line). If you post output, put it into a [fenced code block](https://help.github.com/articles/github-flavored-markdown/#fenced-code-blocks). Last but not least: have a look at [Simon Tatham's "How to Report Bugs Effectively"](http://www.chiark.greenend.org.uk/~sgtatham/bugs.html) to learn how to write a good bug report.

## Opening Pull Requests

### Philosophies

There are a few key philosophies to preserve while designing features for Naomi:

1. **The core Naomi software (`in ~/Naomi/jasper/`) must remain decoupled from any third-party web services.** For example, the Naomi core should never depend on Google Translate in any way. This is to avoid unnecessary dependences on web services that might change or become paid over time.
2. **The core Naomi software (`in ~/Naomi/jasper/`) must remain decoupled from any paid software or services.** Of course, you're free to use whatever you'd like when running Naomi locally or in a fork, but the main branch needs to remain _free_ and _open-source_.
3. **Naomi should be _usable_ by both beginner and expert programmers.** If you make a radical change, in particular one that requires some sort of setup, try to offer an easy-to-run alternative or tutorial. See, for example, the profile populator ([`Naomi/jasper/populate.py`](https://github.com/NaomiProject/Naomi/blob/master/jasper/populate.py)), which abstracts away the difficulty of correctly formatting and populating the user profile.

### DOs and DON'Ts

#### Before coding

You **_should**:

1. **Watch the [project roadmap](https://github.com/NaomiProject/Naomi/projects) 
and [milestone](https://github.com/NaomiProject/Naomi/milestones)** in order to find something to work on.

2.**Make sure the stuff you want to do is not already done** it would be awful to reivent the wheel 

3. **In case you want to implement your own ideas**, submit it first [here](https://github.com/NaomiProject/Naomi/issues), we'll have a conversation if this idea respect the project philosophy or explore others options to improve your idea, then may add it to the next milestone and project planning. _Any pull-request that don't follow this rule will be rejected_


#### While developing:

you **_should_**:

1. **Ensure that the existing unit tests pass.** They can be run via `python2 -m unittest discover` for Naomi's main folder.
2. **Test _every commit_ on a Raspberry Pi**. Testing locally (i.e., on OS X or Windows or whatnot) is insufficient, as you'll often run into semi-unpredictable issues when you port over to the Pi. You should both run the unit tests described above and do some anecdotal testing (i.e., run Naomi, trigger at least one module).
3. **Ensure that your code conforms to [PEP8](http://legacy.python.org/dev/peps/pep-0008/) and our existing code standards.** For example, we used camel case in a few places (this could be changed--send in a pull request!). In general, however, defer to PEP8. We also really like Jeff Knupp's [_Writing Idiomatic Python_](http://www.jeffknupp.com/writing-idiomatic-python-ebook/). We use `flake8` to check this, so run it from Naomi's main folder before committing.
4. Related to the above: **Include docstrings that follow our existing format!** Good documentation is a good thing.
4. **Add any new Python dependencies to python_requirements.txt.** Make sure that your additional dependencies are dependencies of `Naomi` and not existing packages on your disk image!
5. **Explain _why_ your change is necessary.** What does it accomplish? Is this something that others will want as well?
6. Once your pull request has received some positive feedback: **Don't forget to update the [Wiki](https://github.com/NaomiProject/Naomi/wiki)** to keep the docs in sync.

On the other hand, you **_should not_**:

1. **Commit _any_ modules to the _jasper-client_ repository.** The modules included in _Naomi/modules_ are meant as illustrative examples. Any new modules that you'd like to share should be done so through other means. If you'd like us to [List your module]() on the web site, [submit a pull request here](https://github.com/NaomiProject/Naomi/pulls).
2. **_Not_ do any of the DOs!**

### TODOs

If you're looking for something to do, here are some suggestions:
1. Improve unit-testing for `jasper-client`. The Naomi modules and `brain.py` have ample testing, but other Python modules (`conversation.py`, `mic.py`, etc.) do not.
2. Come up with a better way to automate testing on the Pi. This might include spinning up some sort of VM with [Docker](http://docs.docker.io), or take a completely different approach.
3. Buff up the text-refinement functions in [`alteration.py`](https://github.com/NaomiProject/Naomi/blob/master/jasper/alteration.py). These are meant to convert text to a form that will sound more human-friendly when spoken by your TTS software, but are quite minimal at the moment.
4. Make Naomi more platform-independent. Currently, Naomi is only supported on Linux (Debian based and Raspberry Pi) and OS X.

### Thanks for reading :grin: :tada:
