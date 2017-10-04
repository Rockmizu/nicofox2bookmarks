# -*- coding: UTF-8 -*-
import configparser
import gettext
import itertools
import pathlib
import subprocess
import threading
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk

import firefox_helper
import nicofox2bookmarks

__title__ = 'NicoFox to Firefox Bookmarks'
__version__ = '0.1.0'

# Private constants.
_CONFIG_FILENAME = 'configs.ini'
_LOCALE_DIRNAME = 'locale'
_TRANSLATION_DOMAIN = 'nicofox2bookmarks_gui'
_PADX = 4 # Default X padding between widgets.
_PADY = 2 # Default Y padding between widgets.
_STARTUP_MIN_WIDTH = 480

def _load_configs(filename=_CONFIG_FILENAME):
    configs = configparser.ConfigParser()
    configs.read(filename)
    return configs

def _setup_i18n(configs):
    prefered_languages = configs.get('General', 'PreferredLanguages', fallback='')
    if prefered_languages:
        prefered_languages = [lang.strip() for lang in prefered_languages.split(',') if lang.strip()]
    else:
        prefered_languages = ['zh_TW']
    locale_dir = pathlib.Path(_LOCALE_DIRNAME).absolute()
    translation = gettext.translation(
        _TRANSLATION_DOMAIN,
        localedir=locale_dir,
        languages=prefered_languages,
        fallback=True)
    translation.install()

def _open_in_explorer(path):
    subprocess.Popen([r'explorer.exe', r'/select,', path])

def _make_open_in_explorer(get_path):
    def _do_open_in_explorer():
        path = get_path().strip().strip('"')
        if path:
            if pathlib.Path(path).exists():
                _open_in_explorer(path)
            else:
                tk.messagebox.showinfo(__title__, _('Target path does not exist.'))
    return _do_open_in_explorer

def _get_widget_geometry(widget):
    geometry = widget.geometry()
    size, x, y = geometry.split('+')
    width, height = size.split('x')
    return int(width), int(height), int(x), int(y)

def _set_widget_geometry(widget, width, height, x, y):
    new_geometry = '{}x{}+{}+{}'.format(width, height, x, y)
    widget.geometry(newGeometry=new_geometry)

def _create_section_title_label(parent, text):
    label = tk.ttk.Label(parent, text=text, anchor=tk.CENTER)
    label.config(background='black')
    label.config(foreground='white')
    return label

def _pad_widget_children_grid(widget, padx=_PADX, pady=_PADY):
    for child in widget.winfo_children():
        child.grid_configure(padx=padx, pady=pady)

def _pad_widget_children_pack(widget, padx=_PADX, pady=_PADY):
    for child in widget.winfo_children():
        child.pack_configure(padx=padx, pady=pady)

def _porting_task(param, on_exit):
    try:
        nicofox_path = param['nicofox_path']
        bookmark_path = param['bookmark_path']
        output_path = param['output_path']
        metadata = param['metadata']

        bookmarks = nicofox2bookmarks.import_nicofox_db(str(nicofox_path))
        if bookmarks:
            nicofox2bookmarks.export_bookmarks_to_json(str(output_path), str(bookmark_path), bookmarks, metadata)
            tk.messagebox.showinfo(__title__, _('Successful! {} bookmark(s) are ported.').format(len(bookmarks)))
        else:
            tk.messagebox.showinfo(__title__, _('No data to port.'))
    except Exception as ex:
        tk.messagebox.showerror(__title__, _('Exception occurred during porting data:\n{}').format(ex))
    finally:
        on_exit()

class TaskDialog:
    """Show the task status visually and start the worker thread."""

    def __init__(self, parent, task_param):
        # Setup GUI.
        self._top = tk.Toplevel(parent)
        self._top.resizable(width=True, height=False)
        self._top.protocol('WM_DELETE_WINDOW', self.on_user_close)
        self._label = tk.ttk.Label(self._top, text=_('Porting data, please wait.'), anchor=tk.CENTER)
        self._label.pack(fill=tk.BOTH)
        self._progress_bar = tk.ttk.Progressbar(self._top, orient=tk.HORIZONTAL, mode='indeterminate')
        self._progress_bar.start()
        self._progress_bar.pack(fill=tk.BOTH)
        _pad_widget_children_pack(self._top)
        # Move this window to the center of parent.
        parent_width, parent_height, parent_x, parent_y = _get_widget_geometry(parent)
        self._top.update_idletasks()
        my_width, my_height, my_x, my_y = _get_widget_geometry(self._top)
        my_x = int(parent_x + (parent_width - my_width) / 2)
        my_y = int(parent_y + (parent_height - my_height) / 2)
        _set_widget_geometry(self._top, my_width, my_height, my_x, my_y)
        # Start task
        self._done = False
        self._closed = False
        self._closing_lock = threading.Lock()
        self._worker = threading.Thread(target=_porting_task, args=(task_param, self.on_task_exit))
        self._worker.start()

    def close(self):
        try:
            self._closing_lock.acquire()
            if not self._closed:
                self._progress_bar.stop()
                self._top.destroy()
                self._closed = True
        finally:
            self._closing_lock.release()

    def on_task_exit(self):
        self.close()
        self._done = True

    def on_user_close(self):
        to_close = tk.messagebox.askyesno(
            __title__,
            _('Close this window will NOT stop the porting task.\nDo you still want to close it?'))
        if to_close == tk.YES:
            self.close()

    @property
    def done(self):
        return self._done

class ProfilesSelector(tk.Frame):
    """Panel for select Firefox profile."""

    def __init__(self, *args, **kwargs):
        super(ProfilesSelector, self).__init__(*args, **kwargs)
        # Setup attributes.
        self._profiles_loaded = False
        self._profiles_namelist = []
        self._profiles = []
        # Setup GUI.
        _create_section_title_label(self, text=_('Profiles')).pack(fill=tk.BOTH)
        self._profiles_combobox = tk.ttk.Combobox(self)
        self._profiles_combobox.config(state='readonly')
        self._profiles_combobox.pack(fill=tk.BOTH)
        _pad_widget_children_pack(self)

    def load_profiles(self, force_reload=False):
        if force_reload:
            self._profiles_namelist.clear()
            self._profiles.clear()
            self._profiles_loaded = False
        if not self._profiles_loaded:
            self._profiles = firefox_helper.get_firefox_profiles()
            if self._profiles:
                self._profiles_namelist = [profile.name for profile in self._profiles]
                try:
                    default_index = next(index for index, profile in enumerate(self._profiles) if profile.is_default)
                    self._profiles_namelist[default_index] += ' ({})'.format(_('default'))
                except StopIteration:
                    default_index = -1
            else:
                default_index = -1
            self._profiles.insert(0, None)
            self._profiles_namelist.insert(0, _('<Manual Settings>'))
            self._profiles_combobox['values'] = self._profiles_namelist
            self._profiles_combobox.current(1 + default_index)
            self._profiles_loaded = True

    @property
    def selected_profile(self):
        selection = self._profiles_combobox.current()
        return self._profiles[selection]

class PathField(tk.Frame):
    def __init__(self, *args, **kwargs):
        super(PathField, self).__init__(*args, **kwargs)
        self._label = tk.ttk.Label(self, text='Path:')
        self._label.grid(sticky=tk.W)
        self._entry = tk.ttk.Entry(self)
        self._entry.grid(row=1, columnspan=2, sticky=tk.W+tk.E)
        self._open_in_folder_btn = tk.ttk.Button(
            self,
            text=_('Open in Explorer'),
            command=_make_open_in_explorer(lambda: self._entry.get()))
        self._open_in_folder_btn.grid(row=0, column=1, sticky=tk.E)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        _pad_widget_children_grid(self)

    @property
    def label(self):
        return self._label.cget('text')

    @label.setter
    def label(self, text):
        self._label.config(text=text)

    @property
    def path(self):
        return self._entry.get().strip().strip('"')

    @path.setter
    def path(self, text):
        self._entry.delete(0, tk.END)
        self._entry.insert(0, text)

class PathPanel(tk.Frame):
    """Panel for input the files' path."""

    def __init__(self, *args, **kwargs):
        super(PathPanel, self).__init__(*args, **kwargs)
        title_label = _create_section_title_label(self, text=_('Pathes'))
        title_label.pack(fill=tk.BOTH)
        self._nicofox_field = PathField(self)
        self._nicofox_field.label = _('NicoFox Database:')
        self._nicofox_field.pack(fill=tk.BOTH)
        self._bookmark_field = PathField(self)
        self._bookmark_field.label = _('Bookmarks Backup:')
        self._bookmark_field.pack(fill=tk.BOTH)
        self._output_field = PathField(self)
        self._output_field.label = _('Output Bookmarks:')
        self._output_field.pack(fill=tk.BOTH)
        _pad_widget_children_pack(self, padx=0)
        title_label.pack_configure(padx=_PADX)

    @property
    def nicofox_path(self):
        return self._nicofox_field.path

    @nicofox_path.setter
    def nicofox_path(self, path):
        self._nicofox_field.path = path

    @property
    def bookmark_path(self):
        return self._bookmark_field.path

    @bookmark_path.setter
    def bookmark_path(self, path):
        self._bookmark_field.path = path

    @property
    def output_path(self):
        return self._output_field.path

    @output_path.setter
    def output_path(self, path):
        self._output_field.path = path

class MetaPanel(tk.Frame):
    """Panel for input metadata like container name, common tags, etc."""

    def __init__(self, *args, **kwargs):
        super(MetaPanel, self).__init__(*args, **kwargs)
        row_counter = itertools.count()
        _create_section_title_label(self, text=_('Metadata')).grid(
            row=next(row_counter), columnspan=2, sticky=tk.W+tk.E)
        self._container_entry = self._create_field(_('Container:'), next(row_counter))
        self._container_desc_entry = self._create_field(_('Container Description:'), next(row_counter))
        self._common_tags_entry = self._create_field(_('Common Tags:'), next(row_counter))
        self.columnconfigure(1, weight=1)
        _pad_widget_children_grid(self)

    def _create_field(self, label, row):
        tk.ttk.Label(self, text=label).grid(row=row, column=0, sticky=tk.E)
        entry = tk.ttk.Entry(self)
        entry.grid(row=row, column=1, sticky=tk.W+tk.E)
        return entry

    @property
    def container(self):
        return self._container_entry.get().strip()

    @container.setter
    def container(self, text):
        self._container_entry.delete(0, tk.END)
        self._container_entry.insert(0, text)

    @property
    def container_description(self):
        return self._container_desc_entry.get().strip()

    @container_description.setter
    def container_description(self, text):
        self._container_desc_entry.delete(0, tk.END)
        self._container_desc_entry.insert(0, text)

    @property
    def common_tags(self):
        tags_text = self._common_tags_entry.get().strip()
        return [tag.strip() for tag in tags_text.split(',') if tag.strip()]

    @common_tags.setter
    def common_tags(self, tags):
        tags_text = ', '.join(tag.strip() for tag in tags if tag.strip())
        self._common_tags_entry.delete(0, tk.END)
        self._common_tags_entry.insert(0, tags_text)

class Processor:
    """Collect data from UI and launch porting tasks."""

    def __init__(self):
        self._profile_getter = None
        self._path_source = None
        self._meta_source = None
        self._tasks = []
        self._on_all_tasks_complete = None

    @property
    def profile_getter(self):
        return self._profile_getter

    @profile_getter.setter
    def profile_getter(self, getter):
        self._profile_getter = getter

    @property
    def path_source(self):
        return self._path_source

    @path_source.setter
    def path_source(self, source):
        self._path_source = source

    @property
    def meta_source(self):
        return self._meta_source

    @meta_source.setter
    def meta_source(self, source):
        self._meta_source = source

    @property
    def has_running_task(self):
        self._clear_finished_tasks()
        return bool(self._tasks)

    @staticmethod
    def _lookup_nicofox_path(profile):
        """Find the path to the NicoFox database and return it.

        First, find the NicoFox database in current working directory.
        If doesn't exist, then find it in profile directory if there has one.
        Finally, if nowhere can find it, return None.
        """
        NICOFOX_DATABASE_NAME = 'smilefox.sqlite'
        # Find in current working directory.
        nicofox_path = pathlib.Path(NICOFOX_DATABASE_NAME)
        if nicofox_path.is_file():
            return nicofox_path.absolute()
        # Find in profile directory.
        if profile is not None:
            nicofox_path = pathlib.Path(profile.path, NICOFOX_DATABASE_NAME)
            if nicofox_path.is_file():
                return nicofox_path.absolute()
        # Nowhere can find it.
        return None

    @staticmethod
    def _lookup_bookmark_path(profile):
        """Find the path to the Firefox bookmarks backup and return it.

        First, find the Firefox bookmarks backup with today's date in current working directory.
        If doesn't exist and there has a profile, try to find the last automatic bookmarks backup.
        Finally, if nowhere can find it, return None.

        Note: it is highly recommended to use the manually backup.
        """
        # Find in current working directory.
        bookmarks_filename_today = firefox_helper.get_bookmarks_backup_filename()
        bookmark_path = pathlib.Path(bookmarks_filename_today)
        if bookmark_path.is_file():
            return bookmark_path.absolute()
        # Find the lastest one in profile directory.
        if profile is not None:
            bookmark_path = firefox_helper.get_last_firefox_bookmarks_backup_path(profile)
            if bookmark_path is not None:
                return bookmark_path.absolute()
        # Nowhere can find it.
        return None

    @staticmethod
    def _make_output_path():
        """Make the output filename and return it.

        The output filename will be bookmarks filename today suffix with "-with-nicofox".
            e.g. bookmarks-yyyy-mm-dd-with-nicofox.json
        This function also prevents the name which conflicts with existing files.
        It will try append "-number" to the end of file stem in order
        until the filename doesn't exist.
            e.g. bookmarks-yyyy-mm-dd-with-nicofox-2.json
        """
        bookmarks_filename_today = firefox_helper.get_bookmarks_backup_filename()
        output_path = pathlib.Path(bookmarks_filename_today)
        stem = output_path.stem + '-with-nicofox'
        ext = output_path.suffix
        output_path = pathlib.Path(stem + ext)
        if output_path.exists():
            for suffix_num in itertools.count(2):
                output_path = pathlib.Path(stem + '-' + str(suffix_num) + ext)
                if not output_path.exists():
                    break
        return output_path.absolute()

    def _clear_finished_tasks(self):
        self._tasks = [task for task in self._tasks if not task.done]

    def close_all_dialogs(self):
        """Close all task dialogs. (but does NOT stop the tasks.)"""
        for task in self._tasks:
            task.close()

    def start_port(self, root):
        """Collect information form UI and start porting task."""
        assert self._path_source is not None
        assert self._meta_source is not None
        # Get current referred profile.
        profile = self._profile_getter() if self._profile_getter is not None else None
        # Collect path arguments and correct them.
        nicofox_path = self._path_source.nicofox_path
        bookmark_path = self._path_source.bookmark_path
        output_path = self._path_source.output_path
        if not nicofox_path:
            nicofox_path = Processor._lookup_nicofox_path(profile)
            if nicofox_path is None:
                tk.messagebox.showwarning(__title__, _('NicoFox database path is required.'))
                return
        if not bookmark_path:
            bookmark_path = Processor._lookup_bookmark_path(profile)
            if bookmark_path is None:
                tk.messagebox.showwarning(__title__, _('Bookmarks backup path is required.'))
                return
        if not output_path:
            output_path = Processor._make_output_path()
        self._path_source.nicofox_path = nicofox_path
        self._path_source.bookmark_path = bookmark_path
        self._path_source.output_path = output_path
        # Collect metadata arguments and correct them.
        metadata = nicofox2bookmarks.create_metadata()
        metadata['container'] = self._meta_source.container or _('NicoFox')
        metadata['description'] = self._meta_source.container_description\
            or _('Bookmarks imported from NicoFox database using {}.').format(__title__)
        metadata['common_tags'] = self._meta_source.common_tags
        # Feedback the correct metadata to UI.
        self._meta_source.container = metadata['container']
        self._meta_source.container_description = metadata['description']
        self._meta_source.common_tags = metadata['common_tags']
        # Setup task parameters and start task.
        task_param = {
            'nicofox_path': nicofox_path,
            'bookmark_path': bookmark_path,
            'output_path': output_path,
            'metadata': metadata,
            }
        if len(self._tasks) >= 8:
            self._clear_finished_tasks()
        self._tasks.append(TaskDialog(root, task_param))

def _on_root_close(root, processor):
    if processor.has_running_task:
        to_close = tk.messagebox.askyesno(
            __title__,
            _('There are still running task(s). Close this window will NOT stop them.\n'
              'Do you want to close it?'))
        if to_close == tk.NO:
            return
        processor.close_all_dialogs()
    root.destroy()

def main():
    """Main function."""
    # Load configs and setup i18n.
    config = _load_configs()
    _setup_i18n(config)
    # Setup root window.
    root = tk.Tk()
    root.title(__title__ + ' ver.' + __version__)
    root.resizable(width=True, height=False)
    # Setup profiles selector.
    profiles_selector = ProfilesSelector(root)
    profiles_selector.load_profiles()
    profiles_selector.pack(fill=tk.BOTH)
    # Setup processor.
    processor = Processor()
    processor.profile_getter = lambda: profiles_selector.selected_profile
    # Setup path panel.
    path_panel = PathPanel(root)
    path_panel.pack(fill=tk.BOTH)
    processor.path_source = path_panel
    # Setup meta panel.
    meta_panel = MetaPanel(root)
    meta_panel.pack(fill=tk.BOTH)
    processor.meta_source = meta_panel
    # Setup OK button.
    ok_button = tk.ttk.Button(root, text=_('Start Port'), command=lambda: processor.start_port(root))
    ok_button.pack(fill=tk.BOTH)
    # Optimize the root window size.
    root.update_idletasks()
    width, height, x, y = _get_widget_geometry(root)
    if width < _STARTUP_MIN_WIDTH:
        width = _STARTUP_MIN_WIDTH
        _set_widget_geometry(root, width, height, x, y)
    # Start GUI.
    root.protocol('WM_DELETE_WINDOW', lambda: _on_root_close(root, processor))
    root.mainloop()

if __name__ == '__main__':
    main()
