#
# AustinC; Colored Formatting is broken down into different blockes
# based off of use cases (i.e. format, foreground color,
# background color & log defaults)
# To use both colors & logd use:
# from coloredformatting import colors, logd
#



#
# How to use
#    from coloredformatting import colors
#
#    Reset all colors with colors.reset
#    Two subclasses fg for foreground and bg for background.
#    Use as colors.subclass.colorname.
#    i.e. colors.fg.red or colors.bg.green
#    Also, the generic bold, disable, underline, reverse, strikethrough,
#    and invisible work with the main class
#    i.e. colors.bold
#


class colors:
    ################################
    #                              #
    #          FORMATTING          #
    #                              #
    ################################
    reset='\033[0m'
    bold='\033[01m'
    disable='\033[02m'
    underline='\033[04m'
    reverse='\033[07m'
    strikethrough='\033[09m'
    invisible='\033[08m'
    ################################
    #                              #
    #       FOREGROUND COLOR       #
    #                              #
    ################################
    class fg:
        black='\033[30m'
        red='\033[31m'
        green='\033[32m'
        yellow='\033[33m'
        blue='\033[34m'
        magenta='\033[35m'
        cyan='\033[36m'
        white='\033[37m'
        brightblack='\033[90m'
        brightred='\033[91m'
        brightgreen='\033[92m'
        brightyellow='\033[93m'
        brightblue='\033[94m'
        brightmagenta='\033[95m'
        brightcyan='\033[96m'
        brightwhite='\033[97m'
    ################################
    #                              #
    #       BACKGROUND COLOR       #
    #                              #
    ################################
    class bg:
        black='\033[40m'
        red='\033[41m'
        green='\033[42m'
        yellow='\033[43m'
        blue='\033[44m'
        magenta='\033[45m'
        cyan='\033[46m'
        white='\033[47m'
        brightblack='\033[100m'
        brightred='\033[101m'
        brightgreen='\033[102m'
        brightyellow='\033[103m'
        brightblue='\033[104m'
        brightmagenta='\033[105m'
        brightcyan='\033[106m'
        brightwhite='\033[107m'
        
        
# How to use
#    from coloredformatting import logd
#
#    Log defaults are used slightly differnet then above.
#    Nine variables spam, debug, verbose, info, notice, warning, success, error, critical.
#    Setup your print with an argument specifier prepending your message and
#    follow your string with class.variable.
#    i.e. print("%s message with spam text" % logd.spam)
#        
class logd:
    spam="\033[1;90m SPAM \033[0;32m"
    debug="\033[1;90m DEBUG \033[0;32m"
    verbose="\033[1;90m VERBOSE \033[0;36m"
    info="\033[1;90m INFO \033[0;97m"
    notice="\033[1;90m NOTICE \033[0;35m"
    warning="\033[1;90m WARNING \033[0;93m"
    success="\033[1;90m SUCCESS \033[1;32m"
    error="\033[1;90m ERROR \033[0;31m"
    critical="\033[1;90m CRITICAL \033[1;31m"
        