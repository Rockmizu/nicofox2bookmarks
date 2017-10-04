# -*- coding: UTF-8 -*-
"""Firefox Helpers"""
import configparser
import datetime
import os
import pathlib
import re

from jsonlz4_decoder import decompress_jsonlz4

def get_firefox_appdata_path():
    """Return the Firefox settings (appdata) directory path."""
    return pathlib.Path(os.getenv('APPDATA'), 'Mozilla', 'Firefox')

def get_firefox_profiles_path():
    """Return the Firefox profiles directory path."""
    return pathlib.Path(get_firefox_appdata_path(), 'Profiles')

def get_last_firefox_bookmarks_backup_path(profile):
    """Given a Firefox profile, get the path to it's last automatic bookmark backup file."""
    backup_dir = pathlib.Path(profile.path, 'bookmarkbackups')
    last_backup = (0, None)
    for dirpath, dirnames, filenames in os.walk(backup_dir):
        for filename in filenames:
            if not any(filename.endswith(ext) for ext in ('.json', '.jsonlz4')):
                continue # Skip files which are not a bookmark backup.
            full_path = pathlib.Path(dirpath, filename)
            mtime = os.path.getmtime(full_path)
            if mtime > last_backup[0]:
                last_backup = (mtime, full_path)
        dirnames.clear() # Don't look into sub-directories.
    return last_backup[1]

class FirefoxProfile:
    """Basic (shallow) information about a Firefox profile."""

    def __init__(self, name, path, is_relative, default):
        self._is_default = default
        self._name = name
        path = (get_firefox_appdata_path(), path) if is_relative else (path,)
        self._full_path = pathlib.Path(*path).absolute()

    @property
    def is_default(self):
        """Is this profile launched by defualt."""
        return self._is_default

    @property
    def name(self):
        """The profile name."""
        return self._name

    @property
    def path(self):
        """The profile (root) directory path."""
        return self._full_path

def get_firefox_profiles():
    """Return basic information (profile name, profile path, etc.) of Firefox profiles."""
    all_profiles = []
    section_regex = get_firefox_profiles.PROFILE_SECTION_RE
    # Get the path to the profile config file. (usually be profiles.ini)
    firefox_appdata_dir = get_firefox_appdata_path()
    profiles_config_path = os.path.join(firefox_appdata_dir, 'profiles.ini')
    # Parse the content of profiles config file.
    profiles_config = configparser.ConfigParser()
    profiles_config.read(profiles_config_path)
    for section in profiles_config.sections():
        if section_regex.match(section):
            section_data = profiles_config[section]
            name = section_data.get('Name')
            is_relative = section_data.get('IsRelative')
            path = section_data.get('Path')
            default = bool(int(section_data.get('Default', 0)))
            all_profiles.append(FirefoxProfile(
                name=name,
                path=path,
                is_relative=is_relative,
                default=default))
    return all_profiles
get_firefox_profiles.PROFILE_SECTION_RE = re.compile(r'^Profile\d+$')

def get_bookmarks_backup_filename(date=None):
    """Return the default bookmarks filename as it is exported by Firefox at specific date."""
    if date is None:
        date = datetime.datetime.today()
    return 'bookmarks-{year:0>4}-{month:0>2}-{day:0>2}.json'.format(
        year=date.year, month=date.month, day=date.day)

if __name__ == '__main__':
    print('Profiles reading test.')
    profiles = get_firefox_profiles()
    print('Profiles:')
    for profile in profiles:
        print(profile.name + (' (default)' if profile.is_default else ''))
        print(profile.path)
        nicofox_database_path = pathlib.Path(profile.path, 'smilefox.sqlite')
        print(nicofox_database_path)
        last_bookmark_backup_path = get_last_firefox_bookmarks_backup_path(profile)
        print(last_bookmark_backup_path)
