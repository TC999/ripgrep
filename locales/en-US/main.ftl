# Help text templates for ripgrep
app-description = 
    ripgrep (rg) recursively searches the current directory for lines matching
    a regex pattern. By default, ripgrep will respect gitignore rules and
    automatically skip hidden files/directories and binary files.

help-hint = Use -h for short descriptions and --help for more details.

project-home = Project home page: https://github.com/BurntSushi/ripgrep

usage-header = USAGE:

# Short help template sections
positional-args-header = POSITIONAL ARGUMENTS:
pattern-arg-short = A regular expression used for searching.
path-arg-short = A file or directory to search.

input-options-header = INPUT OPTIONS:
search-options-header = SEARCH OPTIONS:
filter-options-header = FILTER OPTIONS:
output-options-header = OUTPUT OPTIONS:
output-modes-header = OUTPUT MODES:
logging-options-header = LOGGING OPTIONS:
other-behaviors-header = OTHER BEHAVIORS:

# Long help template sections
pattern-arg-long = 
    A regular expression used for searching. To match a pattern beginning
    with a dash, use the -e/--regexp flag.
    
    For example, to search for the literal '-foo', you can use this flag:
    
        rg -e -foo
    
    You can also use the special '--' delimiter to indicate that no more
    flags will be provided. Namely, the following is equivalent to the
    above:
    
        rg -- -foo

path-arg-long = 
    A file or directory to search. Directories are searched recursively.
    File paths specified on the command line override glob and ignore
    rules.
