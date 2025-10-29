# ripgrep 的帮助文本模板
app-description = 
    ripgrep (rg) 递归搜索当前目录以查找匹配正则表达式模式的行。
    默认情况下，ripgrep 会遵守 gitignore 规则，并自动跳过隐藏文件/目录和二进制文件。

help-hint = 使用 -h 查看简短描述，使用 --help 查看更多详情。

project-home = 项目主页: https://github.com/BurntSushi/ripgrep

usage-header = 用法:

# 简短帮助模板部分
positional-args-header = 位置参数:
pattern-arg-short = 用于搜索的正则表达式。
path-arg-short = 要搜索的文件或目录。

input-options-header = 输入选项:
search-options-header = 搜索选项:
filter-options-header = 过滤选项:
output-options-header = 输出选项:
output-modes-header = 输出模式:
logging-options-header = 日志选项:
other-behaviors-header = 其他行为:

# 详细帮助模板部分
pattern-arg-long = 
    用于搜索的正则表达式。要匹配以破折号开头的模式，
    请使用 -e/--regexp 标志。
    
    例如，要搜索字面量 '-foo'，您可以使用此标志:
    
        rg -e -foo
    
    您也可以使用特殊的 '--' 分隔符来表示不再提供标志。
    也就是说，以下命令与上面的命令等效:
    
        rg -- -foo

path-arg-long = 
    要搜索的文件或目录。目录将被递归搜索。
    在命令行上指定的文件路径将覆盖 glob 和 ignore 规则。
