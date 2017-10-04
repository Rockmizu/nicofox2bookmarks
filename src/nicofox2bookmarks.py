# -*- coding: UTF-8 -*-
import argparse
import json
import pathlib
import sqlite3
import time

import firefox_helper

__title__ = 'NicoFox to Firefox Bookmarks'
__version__ = '0.1.0'

def _create_bookmark_data():
    return {
        'title': '',
        'url': '',
        'description': '',
        'tags': None, # Seems NicoFox doesn't record tags.
        'add_time': 0,
        }

def create_metadata():
    """Create a default metadata dictionary."""
    return {
        'container': 'NicoFox',
        'description': '',
        'common_tags': None,
        }

def nicofox_time_to_bookmark_time(nicofox_time):
    return nicofox_time * 1000

def posix_time_to_bookmark_time(posix_time):
    return posix_time * 1000000

def import_nicofox_db(db_name):
    """Import data from NicoFox database and return it as bookmarks."""
    with sqlite3.connect(db_name) as smilefox:
        all_bookmarks = []
        for row in smilefox.execute('SELECT video_title, url, description, add_time FROM smilefox;'):
            bookmark = _create_bookmark_data()
            bookmark['title'] = row[0]
            bookmark['url'] = row[1]
            bookmark['description'] = row[2]
            bookmark['add_time'] = nicofox_time_to_bookmark_time(row[3])
            all_bookmarks.append(bookmark)
        return all_bookmarks

# bj = bookmarks json.
def bj_seek_in_children_by_guid(node, guid):
    """Search the child item with specific GUID and return it."""
    for item in node['children']:
        try:
            if item['guid'] == guid:
                return item
        except KeyError:
            pass # Simply ignore items without GUID.
    return None

def bj_create_bookmark_description(description):
    assert description is not None
    annos = []
    annos.append({
        'name': 'bookmarkProperties/description',
        'flags': 0,
        'expires': 4,
        'value': description,
        })
    return annos

def bj_create_child_container(node, container_data):
    """Create a directory (container) in the node."""
    try:
        children = node['children']
    except KeyError:
        children = []
        node['children'] = children
    now = posix_time_to_bookmark_time(time.time())
    new_container = {
        'title': container_data.get('title', 'untitled'),
        'index': len(children),
        'dateAdded': container_data.get('dateAdded', now),
        'lastModified': container_data.get('lastModified', now),
        'type': 'text/x-moz-place-container',
        'children': []
        }
    description = container_data.get('description')
    if description:
        new_container['annos'] = bj_create_bookmark_description(description)
    children.append(new_container)
    return children[-1]

def bj_get_menu_container(bookmarks_json):
    """Get the menu container from root element."""
    root = bookmarks_json
    if root['guid'] != 'root________':
        raise ValueError('Can not get menu container from nodes other than root.')
    return bj_seek_in_children_by_guid(root, 'menu________')

def bj_load(json_name):
    """Load the bookmarks JSON and parse it as a JSON object."""
    is_jsonlz4 = json_name.lower().endswith('.jsonlz4')
    if is_jsonlz4:
        with open(json_name, 'rb') as bookmarks_json_file:
            data = bookmarks_json_file.read()
        data = firefox_helper.decompress_jsonlz4(data).decode('UTF-8')
    else:
        with open(json_name, 'r', encoding='UTF-8') as bookmarks_json_file:
            data = bookmarks_json_file.read()
    return json.loads(data)

def export_bookmarks_to_json(output_name, json_name, bookmarks, meta_data):
    """Export the bookmarks imported from NicoFox database to Firefox bookmarks JSON file."""
    # Load bookmarks.
    bookmarks_json = bj_load(json_name)
    # Find the menu container and create a directory in it.
    menu = bj_get_menu_container(bookmarks_json)
    archive = bj_create_child_container(menu, {
        'title': meta_data['container'],
        'description': meta_data['description']})
    # Append imported bookmarks to the created directory.
    archive_children = archive['children']
    for bookmark in bookmarks:
        # Build new bookmark item from bookmark data and metadata.
        new_bookmark = {
            'title': bookmark['title'],
            'index': len(archive_children),
            'dateAdded': bookmark['add_time'],
            'lastModified': bookmark['add_time'],
            'type': 'text/x-moz-place',
            'uri': bookmark['url'],
            }
        # description
        if bookmark['description']:
            new_bookmark['annos'] = bj_create_bookmark_description(bookmark['description'])
        # tags
        all_tags = []
        if bookmark['tags']:
            all_tags.extend(bookmark['tags'])
        if meta_data['common_tags']:
            all_tags.extend(meta_data['common_tags'])
        if all_tags:
            all_tags = set(all_tags) # Ensure that each tag is unique.
            new_bookmark['tags'] = ','.join(all_tags)
        # Add new bookmark.
        archive_children.append(new_bookmark)
    # Save bookmarks.
    with open(output_name, 'w', encoding='UTF-8') as output_file:
        json.dump(bookmarks_json, output_file)

def parse_arguments(args=None):
    """Setup and parse program arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nicofox', help='The name of NicoFox database file, usually named "smilefox.sqlite". (input file)')
    parser.add_argument('-b', '--bookmarks', help='The name of Firefox bookmarks file, usually named "bookmarks-yyyy-mm-dd.json". (input file)')
    parser.add_argument('-o', '--output', help='The name of result bookmarks file with NicoFox\'s list in. (output file)')
    parser.add_argument('-c', '--container', help='The name of the folder which the new bookmarks contain.')
    parser.add_argument('-d', '--container-desc', help='The description of the folder which the new bookmarks contain.')
    parser.add_argument('-t', '--common-tags', help='The tag(s) added to all new bookmarks.')
    return parser.parse_args(args)

def main():
    """Main function."""
    arguments = parse_arguments()

    # Collect and setup metadata from program arguments.
    meta_data = create_metadata()
    meta_data['container'] = arguments.container or 'NicoFox'
    meta_data['description'] = arguments.container_desc if arguments.container_desc is not None\
        else 'Bookmarks imported from NicoFox database using {}.'.format(__title__)
    if arguments.common_tags:
        meta_data['common_tags'] = [tag.strip() for tag in arguments.common_tags.split(',') if tag.strip()]

    # Setup input and output filenames from program arguments.
    nicofox_database = arguments.nicofox or 'smilefox.sqlite'
    bookmarks_file = arguments.bookmarks or firefox_helper.get_bookmarks_backup_filename()
    output_file = arguments.output or 'bookmarks-output.json'

    # Display basic information.
    print(__title__)
    print('version', __version__)
    print()
    print('NicoFox database:', nicofox_database)
    print('Firefox bookmarks:', bookmarks_file)
    print('Output file:', output_file)
    print()

    # Check the input and output filenames.
    if not pathlib.Path(nicofox_database).is_file():
        print('Error: the NicoFox database file does not exist or not specified.')
        return
    if not pathlib.Path(bookmarks_file).is_file():
        print('Error: the Firefox bookmarks file does not exist or not specified.')
        return
    if pathlib.Path(output_file).is_file():
        overwrite = input('The output file seems have already exist. Overwrite it? ')
        if overwrite.lower() not in ('y', 'yes'):
            print('Operation canceled.')
            return
        print('')

    # Port data.
    try:
        print('Importing data from NicoFox database...')
        bookmarks = import_nicofox_db(nicofox_database)
        if bookmarks:
            print('Exporting data to bookmarks...')
            export_bookmarks_to_json(output_file, bookmarks_file, bookmarks, meta_data)
            print('Successful! {} bookmark(s) are ported.'.format(len(bookmarks)))
        else:
            print('No data to port.')
    except Exception:
        print('Exception occurred during porting data.')
        raise
    finally:
        print('All done.')

if __name__ == '__main__':
    main()
