<p align="center">
    <img width="128px" src="img/logo_plain.svg">
</p>

# Store And Fetch Operator or Code Snippets with Houclip

Have you ever wished you could keep handy copies of your favorite Houdini network setups or cool code snippets, but felt that creating HDAs for this purpose was overkill?

Well, wish no more, because **Houclip** makes it easy to store them in a plain-text-driven file repository, from where you can fetch your snippets at any time.

Got a nice network setup that you know you will want to use one day?
Found an interesting Python or VEX code on the Internet?
Snip it into your local repository for later use.
All of this with a sleek keyboard interaction with the program via the venerable [dmenu](https://tools.suckless.org/dmenu/) or [rofi's](https://github.com/davatorium/rofi) powerful fuzzy search.

https://github.com/ajz3d/houclip/assets/34176570/3cdc64bd-514c-4db6-b970-a44588b22d42

## Usage Instructions

The program comes with a shelf tab named _Houclip_, which supplies a tool for storing operator snippets.
It is labelled _Store OpSnippet_ and is the only way of storing operator snippets.

The remainder of the program's commands is available by running `houclip_run.py`.

Here's their full list:

- `opfetch`: fetches operator snippet from repository,
- `opdel`: deletes operator snippet from repository,
- `codeadd`: adds clipboard contents to repository,
- `codefetch`: fetches saved code snippet from repository,
- `codedel`: deletes code snippet from repository.


There are three things to keep in mind when adding snippets of any kind:

1. _Description_ is mandatory, while _tags_ are optional.
   To skip entering tags, press `Enter` without providing an input.
2. Keep _descriptions_ unique for each snippet of the same category, as they are _de facto_ unique identifiers of snippets.
   Enforcement of unique descriptions is planned for the future.
   Currently, if two records of the same description exist within the same category, you will only be able to fetch the first one.
3. Tags are comma-separated.
4. Try not to use spaces when inputting tags, because all whitespace from this field will be stripped.
   Use underscores or dashes instead, for example: `foo,bar,faz_baz`.
   
Also note, that Houdini license restrictions do apply to stored snippets.
This means that if you have stored an Apprentice or Indie network, if it's fetched from repository, it will change your running Houdini instance to this exact license.

### First run

On its first run, when started either from Houdini shelf tool or with `houclip_run.py`, the program will create a config file in houclip package's root directory:

```
$HOUDINI_USER_PREF_DIR/packages/houclip/houclip.conf
```

You can read more information about each configuration option [later on](#Configuring Houclip) in this document.

The program will also initialize file hierarchy of its snippet repository.
This location defaults to `$HOME/.local/share/houclip`, but can be changed in the config file to any directory.

### Store operator snippet (opadd)

To save a network setup in Houdini, simply select nodes that you want to store and either click the _Store OpSnippet_ tool on Houclip shelf, or press a designated hotkey if you have configured it earlier.
A menu will prompt you to enter a mandatory snippet description.
It can be a string of any length.
Then, the program will ask for a list of optional comma-separated tags.
With that done, your snippet will be automatically stored in Houclip repository and will be available for the `opfetch` command.

**Note:** This command is available from Houdini only.

### Fetch an operator snippet (opfetch)

This command presents you with a list of Houdini node type categories.
Search for a category you want to browse, then search for a snippet which you want to fetch.
Once confirmed, the snippet will be available for pasting into appropriate Houdini context using the standard hotkey (`CTRL+V`).

### Delete an operator snippet (opdel)

Select Houdini node type category you want to delete snippet from.
Then, select an operator snippet to delete.
Be advised that the snippet will be removed immediately, without any confirmation.

### Store a code snippet (codeadd)

With text to store copied to system clipboard, select language category that you want to save copied text into, then input snippet's description and (optionally) tags.

### Store a code snippet (codefetch)

Select language you want to browse and then select a snippet you want to fetch.
The snippet will be copied to clipboard and will be ready for pasting at any time (`CTRL+V`).

### Delete a code snippet (codedel)
Select a language, then a snippet to delete.
Remember, that the program will not ask you for confirmation, so once you hit `Enter`, the snippet is gone.

### Edit a snippet

Because information about snippets is stored in plain-text files, editing a snippet is as easy as opening a CSV file with a text editor and searching for its description.
Each line of the CSV file contains full definition of a snippet, with each field separated by a semicolon:

``` csv
description;tags;category;prefix;uuid1
```

Here's a brief description of those fields:

- `description` --- Snippet description. Nothing more, nothing less.
- `tags` --- Comma-separated tags (no whitespace allowed).
- `category` --- Houdini [node type category name](https://www.sidefx.com/docs/houdini/hom/hou/NodeTypeCategory.html). **Don't modify!**
- `prefix` --- Original prefix of Houdini `.cpio` file. Empty for code snippets. **Don't modify!**
- `uuid1` --- hexadecimal representation of [uuid.uuid1](https://docs.python.org/3/library/uuid.html#uuid.uuid1).

Actual snippets are stored in subdirectories corresponding to snippet's _category_, with _uuid_ as file names.
Operator snippets are `.cpio` files stored in _gzip_ compressed format.

### Record sorting

By default, snippets appear on the list in the order of their creation.
Currently, Houclip doesn't offer any type of sorting, though it is loosely planned for the future.
If you wish to sort snippet CSV lists, for the time being you can accomplish this by periodically using the standard `sort` tool, which is available on all GNU/Linux distributions.

The following example presents various ways of sorting this kind of file:

``` sh
# Choose one of sorting options.
cat Sop.csv | sort > Sop.csv.tmp  # Sorts by description
cat Sop.csv | sort -t ';' -k 2,2 > Sop.csv.tmp  # Sorts by tags
cat Sop.csv | sort -t ';' -k 5,5 > Sop.csv.tmp  # Sorts by time (uuid includes time)
# Then replace the original .csv file.
mv Sop.csv.tmp Sop.csv
```

Some GNU/Linux users might want to automate this process with `entr` or a similar tool, in order to sort those files whenever they change.

## Prerequisites

- GNU/Linux --- tested on Debian Bookworm,
- X11 --- currently no Wayland support, but I can implement `wl-clipboard`, if someone is willing to test it,
- Python 3 --- tested on Hython 3.9.10 and Python 3.11.2,
- Houdini 19.5 --- might work on older versions, just make sure to use Py3 builds,
- dmenu or rofi --- supported user interfaces,
- xsel --- handles X11 clipboard operations,
- libnotify4 --- used to send notifications.

### Other operating systems

For the time being, the only supported operating system is GNU/Linux.
The main reason behind this is simple: all of my machines are running on GNU/Linux, so I don't have capability (nor desire, to be frank) to test it on proprietary systems.

However, with some modifications, notably by replacing `/dev/shm`, `xsel`, `notify-send` (and other GNU/Linux-specific commands and paths used by the package) with your operating system's counterparts, but also if you can find a Dmenu clone for your OS, Houclip should work just fine.

I found a [dmenu-mac](https://github.com/oNaiPs/dmenu-mac) project, which seems to be a port of dmenu for Apple computers, so you might want to start from there, if you're MacOS user.
Adding a new menu interface to the package is just a matter of creating a new `menu.Menu` subclass, and then updating `menu.MENUS` dictionary.

As of [free](https://www.gnu.org/philosophy/free-sw.html) Dmenu clone for Windows, I found [the wmenu project](https://github.com/LinArcX/wmenu).

## Installation

The program comes in a form of a Houdini package.

Simply clone the repository into `packages` directory inside your Houdini user preferences path.
Then symlink `houclip/houclip.json` file to `packages` path.

If you have a `$HOUDINI_USER_PREF_DIR` envar present, the installation process would be as follows:

``` sh
cd $HOUDINI_USER_PREF_DIR/packages
git clone https://github.com/ajz3d/houclip.git
ln -sf $HOUDINI_USER_PREF_DIR/packages/houclip/houclip.json ./houclip.json
```

You can check if the program was installed correctly, by running Houdini and adding _Houclip_ shelf tab to your shelf pane.
If it's not there, then something went wrong.

## Configuring Houclip

### Houdini

Houclip comes with its own shelf tab named _Houclip_.
It contains only one tool, which allows for adding operator snippets to repository.
For ease of access, it is recommended to add Houdini's _global hotkey_ to this tool.
I suggest `ALT+`` as one of the very few free hotkeys available in Houdini.

### Shell
The rest of Houclip's functionality can be reached by running `houclip_run.py` and I strongly suggest to symlink this file to `$HOME/.local/bin/houclip`, or some other path where you store executables and which is included in your `$PATH`.

For example:

``` sh
ln -sf $HOUDINI_USER_PREF_DIR/packages/houclip/scripts/python/houclip_run.py
$HOME/.local/bin/houclip
```

However you decide to run the program, I recommend assigning it a system-wide hotkey, like `SUPER+\``, for instance.

### Configuration File
Config file named `houclip.conf` is created in houclip package's directory on the first run of the program.
You can also create it yourself by copy-pasting contents of the listing below:

``` ini
# $HOUDINI_USER_PREF_DIR/packages/houclip/houclip.conf
[PATHS]
# Path to repository.
repo = /home/user/.local/share/houclip

[CSV]
# Don't touch this, unless you know what you're doing.
# If those parameters are modified when snippet repository
# already contains saved items, things might and will break.
delimiter = ;
dialect = unix
quoting = 0

[MENU]
# Selected user interface. "Dmenu" or "Rofi".
# With "Rofi" you get fuzzy search and easier theming.
menu = Dmenu
# Menu theme, if supported. E.g. my-theme.
theme =
# Maximum length of snippet description and tags to be displayed in menus.
# Anything beyond these numbers will be truncated. For example:
#
# This is a very long description                |foo,faz,bar,baz,hou,b
# Well, I am an even longer description, so sto  |abc,def,ghi
#                                             ^                       ^
#                                        max_desc_len            max_tags_len
#
# These values should be tweaked to one's liking.
max_desc_len = 128
max_tags_len = 32
```
