"""Tkinter tiruan untuk autograder: tanpa jendela, tanpa layar.

Dipakai agar kode Tkinter praktikan bisa dijalankan dan "diklik" otomatis di
browser (Pyodide), tempat Tkinter asli tidak ada. Yang ditiru adalah perilaku
yang relevan untuk tugas: widget dan opsinya, layout manager (termasuk error
mencampur pack dan grid), variabel Tkinter, bind, command, messagebox.
Kesalahan yang di Tkinter asli menimbulkan error (opsi salah ketik, StringVar
dibuat sebelum Tk(), command yang error di dalam callback) di sini juga begitu.

Pemakaian dari grader:

    import faketk
    faketk.reset(); faketk.install()      # sebelum menjalankan kode praktikan
    ... exec(kode praktikan) ...
    faketk.STATE.widgets                  # semua widget yang dibuat
"""

import importlib.abc
import importlib.machinery
import re
import sys
import traceback
import types

# __META__ diisi oleh build_meta.py: daftar opsi widget, konstanta, dan nama method
# dari Tkinter asli (Tk 8.6). Jangan diubah manual.
_META = {'konstanta': {'ACTIVE': 'active',
               'ALL': 'all',
               'ANCHOR': 'anchor',
               'ARC': 'arc',
               'BASELINE': 'baseline',
               'BEVEL': 'bevel',
               'BOTH': 'both',
               'BOTTOM': 'bottom',
               'BROWSE': 'browse',
               'BUTT': 'butt',
               'CASCADE': 'cascade',
               'CENTER': 'center',
               'CHAR': 'char',
               'CHECKBUTTON': 'checkbutton',
               'CHORD': 'chord',
               'COMMAND': 'command',
               'CURRENT': 'current',
               'DISABLED': 'disabled',
               'DOTBOX': 'dotbox',
               'E': 'e',
               'END': 'end',
               'EW': 'ew',
               'EXTENDED': 'extended',
               'FALSE': 0,
               'FIRST': 'first',
               'FLAT': 'flat',
               'GROOVE': 'groove',
               'HIDDEN': 'hidden',
               'HORIZONTAL': 'horizontal',
               'INSERT': 'insert',
               'INSIDE': 'inside',
               'LAST': 'last',
               'LEFT': 'left',
               'MITER': 'miter',
               'MOVETO': 'moveto',
               'MULTIPLE': 'multiple',
               'N': 'n',
               'NE': 'ne',
               'NO': 0,
               'NONE': 'none',
               'NORMAL': 'normal',
               'NS': 'ns',
               'NSEW': 'nsew',
               'NUMERIC': 'numeric',
               'NW': 'nw',
               'OFF': 0,
               'ON': 1,
               'OUTSIDE': 'outside',
               'PAGES': 'pages',
               'PIESLICE': 'pieslice',
               'PROJECTING': 'projecting',
               'RADIOBUTTON': 'radiobutton',
               'RAISED': 'raised',
               'RIDGE': 'ridge',
               'RIGHT': 'right',
               'ROUND': 'round',
               'S': 's',
               'SCROLL': 'scroll',
               'SE': 'se',
               'SEL': 'sel',
               'SEL_FIRST': 'sel.first',
               'SEL_LAST': 'sel.last',
               'SEPARATOR': 'separator',
               'SINGLE': 'single',
               'SOLID': 'solid',
               'SUNKEN': 'sunken',
               'SW': 'sw',
               'TOP': 'top',
               'TRUE': 1,
               'UNDERLINE': 'underline',
               'UNITS': 'units',
               'VERTICAL': 'vertical',
               'W': 'w',
               'WORD': 'word',
               'X': 'x',
               'Y': 'y',
               'YES': 1},
 'method': ['activate', 'add', 'add_cascade', 'add_checkbutton', 'add_command', 'add_radiobutton',
            'add_separator', 'addtag', 'addtag_above', 'addtag_all', 'addtag_below', 'addtag_closest',
            'addtag_enclosed', 'addtag_overlapping', 'addtag_withtag', 'after', 'after_cancel', 'after_idle',
            'after_info', 'anchor', 'aspect', 'attributes', 'bbox', 'bell', 'bind', 'bind_all', 'bind_class',
            'bindtags', 'busy', 'busy_cget', 'busy_config', 'busy_configure', 'busy_current', 'busy_forget',
            'busy_hold', 'busy_status', 'canvasx', 'canvasy', 'cget', 'client', 'clipboard_append',
            'clipboard_clear', 'clipboard_get', 'colormapwindows', 'columnconfigure', 'command', 'compare',
            'config', 'configure', 'coords', 'count', 'create_arc', 'create_bitmap', 'create_image',
            'create_line', 'create_oval', 'create_polygon', 'create_rectangle', 'create_text',
            'create_window', 'curselection', 'dchars', 'debug', 'deiconify', 'delete', 'deletecommand',
            'deselect', 'destroy', 'dlineinfo', 'dtag', 'dump', 'edit', 'edit_modified', 'edit_redo',
            'edit_reset', 'edit_separator', 'edit_undo', 'entrycget', 'entryconfig', 'entryconfigure',
            'event_add', 'event_delete', 'event_generate', 'event_info', 'find', 'find_above', 'find_all',
            'find_below', 'find_closest', 'find_enclosed', 'find_overlapping', 'find_withtag', 'flash',
            'focus', 'focus_displayof', 'focus_force', 'focus_get', 'focus_lastfor', 'focus_set',
            'focusmodel', 'forget', 'frame', 'geometry', 'get', 'getboolean', 'getdouble', 'getint',
            'gettags', 'getvar', 'grab_current', 'grab_release', 'grab_set', 'grab_set_global', 'grab_status',
            'grid', 'grid_anchor', 'grid_bbox', 'grid_columnconfigure', 'grid_configure', 'grid_forget',
            'grid_info', 'grid_location', 'grid_propagate', 'grid_remove', 'grid_rowconfigure', 'grid_size',
            'grid_slaves', 'group', 'iconbitmap', 'iconify', 'iconmask', 'iconname', 'iconphoto',
            'iconposition', 'iconwindow', 'icursor', 'identify', 'image_cget', 'image_configure',
            'image_create', 'image_names', 'image_types', 'index', 'info', 'info_patchlevel', 'insert',
            'insert_cascade', 'insert_checkbutton', 'insert_command', 'insert_radiobutton',
            'insert_separator', 'invoke', 'itemcget', 'itemconfig', 'itemconfigure', 'keys', 'lift', 'loadtk',
            'location', 'lower', 'mainloop', 'manage', 'mark_gravity', 'mark_names', 'mark_next',
            'mark_previous', 'mark_set', 'mark_unset', 'maxsize', 'minsize', 'move', 'moveto', 'nametowidget',
            'nearest', 'option_add', 'option_clear', 'option_get', 'option_readfile', 'overrideredirect',
            'pack', 'pack_configure', 'pack_forget', 'pack_info', 'pack_propagate', 'pack_slaves',
            'peer_create', 'peer_names', 'place', 'place_configure', 'place_forget', 'place_info',
            'place_slaves', 'positionfrom', 'post', 'postscript', 'propagate', 'protocol', 'quit',
            'readprofile', 'register', 'replace', 'report_callback_exception', 'resizable', 'rowconfigure',
            'scale', 'scan', 'scan_dragto', 'scan_mark', 'search', 'see', 'select', 'select_adjust',
            'select_anchor', 'select_clear', 'select_from', 'select_includes', 'select_item',
            'select_present', 'select_range', 'select_set', 'select_to', 'selection', 'selection_adjust',
            'selection_anchor', 'selection_clear', 'selection_element', 'selection_from', 'selection_get',
            'selection_handle', 'selection_includes', 'selection_own', 'selection_own_get',
            'selection_present', 'selection_range', 'selection_set', 'selection_to', 'send', 'set', 'setvar',
            'size', 'sizefrom', 'slaves', 'state', 'tag_add', 'tag_bind', 'tag_cget', 'tag_config',
            'tag_configure', 'tag_delete', 'tag_lower', 'tag_names', 'tag_nextrange', 'tag_prevrange',
            'tag_raise', 'tag_ranges', 'tag_remove', 'tag_unbind', 'title', 'tk_bisque', 'tk_busy',
            'tk_busy_cget', 'tk_busy_config', 'tk_busy_configure', 'tk_busy_current', 'tk_busy_forget',
            'tk_busy_hold', 'tk_busy_status', 'tk_focusFollowsMouse', 'tk_focusNext', 'tk_focusPrev',
            'tk_popup', 'tk_setPalette', 'tk_strictMotif', 'tkraise', 'toggle', 'transient', 'type', 'unbind',
            'unbind_all', 'unbind_class', 'unpost', 'update', 'update_idletasks', 'wait_variable',
            'wait_visibility', 'wait_window', 'waitvar', 'window_cget', 'window_config', 'window_configure',
            'window_create', 'window_names', 'winfo_atom', 'winfo_atomname', 'winfo_cells', 'winfo_children',
            'winfo_class', 'winfo_colormapfull', 'winfo_containing', 'winfo_depth', 'winfo_exists',
            'winfo_fpixels', 'winfo_geometry', 'winfo_height', 'winfo_id', 'winfo_interps', 'winfo_ismapped',
            'winfo_manager', 'winfo_name', 'winfo_parent', 'winfo_pathname', 'winfo_pixels', 'winfo_pointerx',
            'winfo_pointerxy', 'winfo_pointery', 'winfo_reqheight', 'winfo_reqwidth', 'winfo_rgb',
            'winfo_rootx', 'winfo_rooty', 'winfo_screen', 'winfo_screencells', 'winfo_screendepth',
            'winfo_screenheight', 'winfo_screenmmheight', 'winfo_screenmmwidth', 'winfo_screenvisual',
            'winfo_screenwidth', 'winfo_server', 'winfo_toplevel', 'winfo_viewable', 'winfo_visual',
            'winfo_visualid', 'winfo_visualsavailable', 'winfo_vrootheight', 'winfo_vrootwidth',
            'winfo_vrootx', 'winfo_vrooty', 'winfo_width', 'winfo_x', 'winfo_y', 'withdraw', 'wm_aspect',
            'wm_attributes', 'wm_client', 'wm_colormapwindows', 'wm_command', 'wm_deiconify', 'wm_focusmodel',
            'wm_forget', 'wm_frame', 'wm_geometry', 'wm_grid', 'wm_group', 'wm_iconbitmap', 'wm_iconify',
            'wm_iconmask', 'wm_iconname', 'wm_iconphoto', 'wm_iconposition', 'wm_iconwindow', 'wm_manage',
            'wm_maxsize', 'wm_minsize', 'wm_overrideredirect', 'wm_positionfrom', 'wm_protocol',
            'wm_resizable', 'wm_sizefrom', 'wm_state', 'wm_title', 'wm_transient', 'wm_withdraw', 'xposition',
            'xview', 'xview_moveto', 'xview_scroll', 'yposition', 'yview', 'yview_moveto', 'yview_pickplace',
            'yview_scroll'],
 'opsi': {'Button': ['activebackground', 'activeforeground', 'anchor', 'background', 'bd', 'bg', 'bitmap',
                     'borderwidth', 'command', 'compound', 'cursor', 'default', 'disabledforeground', 'fg',
                     'font', 'foreground', 'height', 'highlightbackground', 'highlightcolor',
                     'highlightthickness', 'image', 'justify', 'overrelief', 'padx', 'pady', 'relief',
                     'repeatdelay', 'repeatinterval', 'state', 'takefocus', 'text', 'textvariable',
                     'underline', 'width', 'wraplength'],
          'Canvas': ['background', 'bd', 'bg', 'borderWidth', 'borderwidth', 'closeenough', 'confine',
                     'cursor', 'height', 'highlightbackground', 'highlightcolor', 'highlightthickness',
                     'insertbackground', 'insertborderwidth', 'insertofftime', 'insertontime', 'insertwidth',
                     'offset', 'relief', 'scrollregion', 'selectbackground', 'selectborderwidth',
                     'selectforeground', 'state', 'takefocus', 'width', 'xscrollcommand', 'xscrollincrement',
                     'yscrollcommand', 'yscrollincrement'],
          'Checkbutton': ['activebackground', 'activeforeground', 'anchor', 'background', 'bd', 'bg',
                          'bitmap', 'borderwidth', 'command', 'compound', 'cursor', 'disabledforeground',
                          'fg', 'font', 'foreground', 'height', 'highlightbackground', 'highlightcolor',
                          'highlightthickness', 'image', 'indicatoron', 'justify', 'offrelief', 'offvalue',
                          'onvalue', 'overrelief', 'padx', 'pady', 'relief', 'selectcolor', 'selectimage',
                          'state', 'takefocus', 'text', 'textvariable', 'tristateimage', 'tristatevalue',
                          'underline', 'variable', 'width', 'wraplength'],
          'Entry': ['background', 'bd', 'bg', 'borderwidth', 'cursor', 'disabledbackground',
                    'disabledforeground', 'exportselection', 'fg', 'font', 'foreground',
                    'highlightbackground', 'highlightcolor', 'highlightthickness', 'insertbackground',
                    'insertborderwidth', 'insertofftime', 'insertontime', 'insertwidth', 'invalidcommand',
                    'invcmd', 'justify', 'readonlybackground', 'relief', 'selectbackground',
                    'selectborderwidth', 'selectforeground', 'show', 'state', 'takefocus', 'textvariable',
                    'validate', 'validatecommand', 'vcmd', 'width', 'xscrollcommand'],
          'Frame': ['background', 'bd', 'bg', 'borderwidth', 'class', 'colormap', 'container', 'cursor',
                    'height', 'highlightbackground', 'highlightcolor', 'highlightthickness', 'padx', 'pady',
                    'relief', 'takefocus', 'visual', 'width'],
          'Label': ['activebackground', 'activeforeground', 'anchor', 'background', 'bd', 'bg', 'bitmap',
                    'borderwidth', 'compound', 'cursor', 'disabledforeground', 'fg', 'font', 'foreground',
                    'height', 'highlightbackground', 'highlightcolor', 'highlightthickness', 'image',
                    'justify', 'padx', 'pady', 'relief', 'state', 'takefocus', 'text', 'textvariable',
                    'underline', 'width', 'wraplength'],
          'LabelFrame': ['background', 'bd', 'bg', 'borderwidth', 'class', 'colormap', 'container', 'cursor',
                         'fg', 'font', 'foreground', 'height', 'highlightbackground', 'highlightcolor',
                         'highlightthickness', 'labelanchor', 'labelwidget', 'padx', 'pady', 'relief',
                         'takefocus', 'text', 'visual', 'width'],
          'Listbox': ['activestyle', 'background', 'bd', 'bg', 'borderwidth', 'cursor', 'disabledforeground',
                      'exportselection', 'fg', 'font', 'foreground', 'height', 'highlightbackground',
                      'highlightcolor', 'highlightthickness', 'justify', 'listvariable', 'relief',
                      'selectbackground', 'selectborderwidth', 'selectforeground', 'selectmode', 'setgrid',
                      'state', 'takefocus', 'width', 'xscrollcommand', 'yscrollcommand'],
          'Menu': ['activebackground', 'activeborderwidth', 'activeforeground', 'background', 'bd', 'bg',
                   'borderwidth', 'cursor', 'disabledforeground', 'fg', 'font', 'foreground', 'postcommand',
                   'relief', 'selectcolor', 'takefocus', 'tearoff', 'tearoffcommand', 'title', 'type'],
          'Menubutton': ['activebackground', 'activeforeground', 'anchor', 'background', 'bd', 'bg', 'bitmap',
                         'borderwidth', 'compound', 'cursor', 'direction', 'disabledforeground', 'fg', 'font',
                         'foreground', 'height', 'highlightbackground', 'highlightcolor',
                         'highlightthickness', 'image', 'indicatoron', 'justify', 'menu', 'padx', 'pady',
                         'relief', 'state', 'takefocus', 'text', 'textvariable', 'underline', 'width',
                         'wraplength'],
          'Message': ['anchor', 'aspect', 'background', 'bd', 'bg', 'borderwidth', 'cursor', 'fg', 'font',
                      'foreground', 'highlightbackground', 'highlightcolor', 'highlightthickness', 'justify',
                      'padx', 'pady', 'relief', 'takefocus', 'text', 'textvariable', 'width'],
          'PanedWindow': ['background', 'bd', 'bg', 'borderwidth', 'cursor', 'handlepad', 'handlesize',
                          'height', 'opaqueresize', 'orient', 'proxybackground', 'proxyborderwidth',
                          'proxyrelief', 'relief', 'sashcursor', 'sashpad', 'sashrelief', 'sashwidth',
                          'showhandle', 'width'],
          'Radiobutton': ['activebackground', 'activeforeground', 'anchor', 'background', 'bd', 'bg',
                          'bitmap', 'borderwidth', 'command', 'compound', 'cursor', 'disabledforeground',
                          'fg', 'font', 'foreground', 'height', 'highlightbackground', 'highlightcolor',
                          'highlightthickness', 'image', 'indicatoron', 'justify', 'offrelief', 'overrelief',
                          'padx', 'pady', 'relief', 'selectcolor', 'selectimage', 'state', 'takefocus',
                          'text', 'textvariable', 'tristateimage', 'tristatevalue', 'underline', 'value',
                          'variable', 'width', 'wraplength'],
          'Scale': ['activebackground', 'background', 'bd', 'bg', 'bigincrement', 'borderwidth', 'command',
                    'cursor', 'digits', 'fg', 'font', 'foreground', 'from', 'highlightbackground',
                    'highlightcolor', 'highlightthickness', 'label', 'length', 'orient', 'relief',
                    'repeatdelay', 'repeatinterval', 'resolution', 'showvalue', 'sliderlength',
                    'sliderrelief', 'state', 'takefocus', 'tickinterval', 'to', 'troughcolor', 'variable',
                    'width'],
          'Scrollbar': ['activebackground', 'activerelief', 'background', 'bd', 'bg', 'borderWidth',
                        'borderwidth', 'command', 'cursor', 'elementborderwidth', 'highlightbackground',
                        'highlightcolor', 'highlightthickness', 'jump', 'orient', 'relief', 'repeatdelay',
                        'repeatinterval', 'takefocus', 'troughcolor', 'width'],
          'Spinbox': ['activebackground', 'background', 'bd', 'bg', 'borderwidth', 'buttonbackground',
                      'buttoncursor', 'buttondownrelief', 'buttonuprelief', 'command', 'cursor',
                      'disabledbackground', 'disabledforeground', 'exportselection', 'fg', 'font',
                      'foreground', 'format', 'from', 'highlightbackground', 'highlightcolor',
                      'highlightthickness', 'increment', 'insertbackground', 'insertborderwidth',
                      'insertofftime', 'insertontime', 'insertwidth', 'invalidcommand', 'invcmd', 'justify',
                      'readonlybackground', 'relief', 'repeatdelay', 'repeatinterval', 'selectbackground',
                      'selectborderwidth', 'selectforeground', 'state', 'takefocus', 'textvariable', 'to',
                      'validate', 'validatecommand', 'values', 'vcmd', 'width', 'wrap', 'xscrollcommand'],
          'Text': ['autoseparators', 'background', 'bd', 'bg', 'blockcursor', 'borderwidth', 'cursor',
                   'endline', 'exportselection', 'fg', 'font', 'foreground', 'height', 'highlightbackground',
                   'highlightcolor', 'highlightthickness', 'inactiveselectbackground', 'insertbackground',
                   'insertborderwidth', 'insertofftime', 'insertontime', 'insertunfocussed', 'insertwidth',
                   'maxundo', 'padx', 'pady', 'relief', 'selectbackground', 'selectborderwidth',
                   'selectforeground', 'setgrid', 'spacing1', 'spacing2', 'spacing3', 'startline', 'state',
                   'tabs', 'tabstyle', 'takefocus', 'undo', 'width', 'wrap', 'xscrollcommand',
                   'yscrollcommand'],
          'Tk': ['background', 'bd', 'bg', 'borderwidth', 'class', 'colormap', 'container', 'cursor',
                 'height', 'highlightbackground', 'highlightcolor', 'highlightthickness', 'menu', 'padx',
                 'pady', 'relief', 'screen', 'takefocus', 'use', 'visual', 'width'],
          'Toplevel': ['background', 'bd', 'bg', 'borderwidth', 'class', 'colormap', 'container', 'cursor',
                       'height', 'highlightbackground', 'highlightcolor', 'highlightthickness', 'menu',
                       'padx', 'pady', 'relief', 'screen', 'takefocus', 'use', 'visual', 'width']}}


class TclError(Exception):
    pass


# ====================================================================== keadaan
class _Keadaan:
    def __init__(self):
        self.roots = []
        self.widgets = []
        self.dialogs = []             # dict(jenis, judul, pesan)
        self.callback_errors = []     # teks error dari dalam command / bind
        self.default_root = None
        self.mainloop = 0
        self.after_calls = []
        self.protocols = {}
        self.global_bindings = {}
        self.jawaban = {}             # jenis dialog -> jawaban yang dikembalikan
        self.var_n = 0
        self.canvas_id = 0


STATE = _Keadaan()


def reset():
    STATE.__init__()


def _ringkas_error(e):
    baris = None
    for fr in traceback.extract_tb(e.__traceback__):
        if fr.filename.endswith("main.py"):
            baris = fr.lineno
    teks = f"{type(e).__name__}: {e}"
    return teks + (f" (baris {baris})" if baris else "")


def jalankan_callback(fungsi, *args):
    """Seperti CallWrapper Tkinter asli: error di callback dilaporkan, program lanjut."""
    try:
        return fungsi(*args)
    except SystemExit:
        raise
    except Exception as e:        # BaseException milik grader (_Stop) tidak ikut tertangkap
        STATE.callback_errors.append(_ringkas_error(e))
        return None


def _akar_bawaan():
    if STATE.default_root is None:
        Tk()                      # Tkinter asli membuat root otomatis untuk widget
    return STATE.default_root


def _noop(*args, **kwargs):
    return None


_SINONIM = {"bg": "background", "fg": "foreground", "bd": "borderwidth"}


def _canon(nama):
    nama = str(nama).lstrip("-")
    return _SINONIM.get(nama, nama)


def _norm_seq(seq):
    s = str(seq).strip()
    if s.startswith("<") and s.endswith(">") and not s.startswith("<<"):
        s = s[1:-1]
    return re.sub(r"^(Key|KeyPress)-", "", s)


# ====================================================================== event
class Event:
    def __init__(self, **kw):
        self.serial = 0
        self.num = "??"
        self.focus = False
        self.height = "??"
        self.width = "??"
        self.keycode = 0
        self.state = 0
        self.time = 0
        self.x = 0
        self.y = 0
        self.x_root = 0
        self.y_root = 0
        self.char = ""
        self.send_event = False
        self.keysym = ""
        self.keysym_num = 0
        self.type = "2"
        self.widget = None
        self.delta = 0
        self.__dict__.update(kw)

    def __repr__(self):
        return f"<Event keysym={self.keysym!r} widget={self.widget!r}>"


def fire(widget, sequence, **kw):
    """Memicu event pada widget: handler pada widget, induknya, lalu bind_all. Mengembalikan jumlah handler."""
    seq = _norm_seq(sequence)
    ev = Event(widget=widget, **kw)
    jumlah = 0
    rantai = []
    w = widget
    while w is not None:
        rantai.append(w._bindings)
        w = getattr(w, "master", None)
    rantai.append(STATE.global_bindings)
    for tabel in rantai:
        for fn in list(tabel.get(seq, [])):
            jumlah += 1
            if jalankan_callback(fn, ev) == "break":
                return jumlah
    return jumlah


# ====================================================================== variabel
class Variable:
    _default = ""

    def __init__(self, master=None, value=None, name=None):
        if master is None and STATE.default_root is None:
            raise RuntimeError("Too early to create variable: no default root window")
        self._master = master if master is not None else STATE.default_root
        self._name = name or f"PY_VAR{STATE.var_n}"
        STATE.var_n += 1
        self._value = self._default if value is None else value
        self._traces = []

    def set(self, value):
        self._value = value
        for mode, cb in list(self._traces):
            if "w" in mode or "write" in mode:
                jalankan_callback(cb, self._name, "", "write")

    initialize = set

    def get(self):
        return self._value

    def trace_add(self, mode, callback):
        mode = mode if isinstance(mode, str) else " ".join(mode)
        self._traces.append((mode, callback))
        return f"trace{len(self._traces)}"

    def trace_variable(self, mode, callback):
        return self.trace_add(mode, callback)

    trace = trace_variable

    def trace_remove(self, mode, cbname):
        pass

    def __str__(self):
        return self._name


class StringVar(Variable):
    _default = ""

    def get(self):
        return str(self._value)


class IntVar(Variable):
    _default = 0

    def get(self):
        v = self._value
        try:
            return int(v)
        except (TypeError, ValueError):
            try:
                return int(float(v))
            except (TypeError, ValueError):
                raise TclError(f'expected floating-point number but got "{v}"')


class DoubleVar(Variable):
    _default = 0.0

    def get(self):
        try:
            return float(self._value)
        except (TypeError, ValueError):
            raise TclError(f'expected floating-point number but got "{self._value}"')


class BooleanVar(Variable):
    _default = False

    def set(self, value):
        super().set(self._ke_bool(value))

    initialize = set

    @staticmethod
    def _ke_bool(v):
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("1", "true", "yes", "on"):
                return True
            if s in ("0", "false", "no", "off"):
                return False
            raise TclError(f'expected boolean value but got "{v}"')
        return bool(v)

    def get(self):
        return self._ke_bool(self._value)


# ====================================================================== dasar
class Misc:
    _wclass = "Misc"
    _is_window = False
    _estricto = True

    def _init_misc(self):
        self._children = []
        self._bindings = {}
        self._destroyed = False
        self._last_ids = {}
        self._manager = None
        self._mgr_opts = {}
        self._name = ""
        self._opts = {}

    # ---- opsi
    def _valid(self):
        return set(_META["opsi"].get(self._wclass, ()))

    def _set_options(self, kw):
        valid = self._valid() if self._estricto else None
        for k, v in kw.items():
            key = _canon(k)
            if valid is not None and str(k).lstrip("-") not in valid and key not in valid:
                raise TclError(f'unknown option "-{str(k).lstrip("-")}"')
            self._opts[key] = v
        self._setelah_opsi()

    def _setelah_opsi(self):
        pass

    def configure(self, cnf=None, **kw):
        if cnf is not None and not isinstance(cnf, dict):
            return self.cget(cnf)
        merged = dict(cnf or {})
        merged.update(kw)
        if not merged:
            return {k: ("", "", "", "", self._opts.get(k, "")) for k in sorted(self._valid())}
        self._set_options(merged)
        return None

    config = configure

    def cget(self, key):
        k = _canon(key)
        if k == "text":
            return str(self._opts.get("text", ""))
        return self._opts.get(k, "")

    __getitem__ = cget

    def __setitem__(self, key, value):
        self.configure(**{str(key).lstrip("-"): value})

    def keys(self):
        return sorted(self._valid())

    # ---- event
    def bind(self, sequence=None, func=None, add=None):
        if sequence is None:
            return list(self._bindings)
        seq = _norm_seq(sequence)
        if func is None:
            return ""
        if add in ("+", True) and seq in self._bindings:
            self._bindings[seq].append(func)
        else:
            self._bindings[seq] = [func]
        return f"funcid{len(self._bindings[seq])}"

    def unbind(self, sequence, funcid=None):
        self._bindings.pop(_norm_seq(sequence), None)

    def bind_all(self, sequence=None, func=None, add=None):
        if sequence is None or func is None:
            return ""
        seq = _norm_seq(sequence)
        if add in ("+", True) and seq in STATE.global_bindings:
            STATE.global_bindings[seq].append(func)
        else:
            STATE.global_bindings[seq] = [func]
        return "funcid"

    def unbind_all(self, sequence):
        STATE.global_bindings.pop(_norm_seq(sequence), None)

    def bind_class(self, className, sequence=None, func=None, add=None):
        return ""

    def event_generate(self, sequence, **kw):
        fire(self, sequence, **kw)

    # ---- waktu
    def after(self, ms, func=None, *args):
        STATE.after_calls.append((ms, func, args))
        return f"after#{len(STATE.after_calls)}"

    def after_idle(self, func, *args):
        STATE.after_calls.append((0, func, args))
        return f"after#{len(STATE.after_calls)}"

    def after_cancel(self, id):
        pass

    # ---- info
    def winfo_children(self):
        return [c for c in self._children if not c._destroyed]

    def winfo_toplevel(self):
        w = self
        while getattr(w, "master", None) is not None and not w._is_window:
            w = w.master
        return w

    def winfo_exists(self):
        return 0 if self._destroyed else 1

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080

    def winfo_width(self):
        return 200

    def winfo_height(self):
        return 100

    winfo_reqwidth = winfo_width
    winfo_reqheight = winfo_height

    def winfo_x(self):
        return 0

    winfo_y = winfo_rootx = winfo_rooty = winfo_x

    def winfo_ismapped(self):
        return 1

    def winfo_class(self):
        return self._wclass

    def winfo_name(self):
        return self._name or "tk"

    def _path(self):
        if getattr(self, "master", None) is None:
            return "."
        p = self.master._path()
        return ("" if p == "." else p) + "." + self._name

    __str__ = _path

    # ---- siklus hidup
    def destroy(self):
        for c in list(self._children):
            c.destroy()
        self._destroyed = True

    def quit(self):
        STATE.mainloop = max(STATE.mainloop, 1)

    def mainloop(self, n=0):
        STATE.mainloop += 1

    def update(self):
        pass

    update_idletasks = update

    def __getattr__(self, name):
        if name in _NOOP:
            return _noop
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # ---- layout manager
    def _cek_manager(self, nama):
        master = getattr(self, "master", None)
        if master is None:
            raise TclError(f'can\'t use {nama} on a toplevel window')
        for w in master._children:
            if w is not self and not w._destroyed and w._manager in ("pack", "grid") and w._manager != nama:
                raise TclError(
                    f"cannot use geometry manager {nama} inside {master._path()} "
                    f"which already has slaves managed by {w._manager}"
                )

    def pack(self, cnf=None, **kw):
        self._cek_manager("pack")
        self._manager = "pack"
        self._mgr_opts = dict(cnf or {}, **kw)

    pack_configure = pack

    def grid(self, cnf=None, **kw):
        self._cek_manager("grid")
        self._manager = "grid"
        self._mgr_opts = dict(cnf or {}, **kw)

    grid_configure = grid

    def place(self, cnf=None, **kw):
        self._manager = "place"
        self._mgr_opts = dict(cnf or {}, **kw)

    place_configure = place

    def pack_forget(self):
        if self._manager == "pack":
            self._manager = None

    def grid_forget(self):
        if self._manager == "grid":
            self._manager = None

    grid_remove = grid_forget

    def place_forget(self):
        if self._manager == "place":
            self._manager = None

    def forget(self):
        self._manager = None

    def pack_slaves(self):
        return [c for c in self._children if c._manager == "pack" and not c._destroyed]

    def grid_slaves(self, row=None, column=None):
        return [c for c in self._children if c._manager == "grid" and not c._destroyed]

    slaves = pack_slaves

    def grid_info(self):
        return dict(self._mgr_opts) if self._manager == "grid" else {}

    def pack_info(self):
        return dict(self._mgr_opts) if self._manager == "pack" else {}

    def place_info(self):
        return dict(self._mgr_opts) if self._manager == "place" else {}


class _Wm:
    """Method jendela yang dipakai Tk dan Toplevel."""

    def title(self, string=None):
        if string is None:
            return self._title
        self._title = str(string)
        self._title_set = True

    wm_title = title

    def geometry(self, newGeometry=None):
        if newGeometry is None:
            return self._geometry or "200x200+0+0"
        self._geometry = str(newGeometry)
        self._geometry_set = True

    wm_geometry = geometry

    def protocol(self, name=None, func=None):
        if func is not None:
            STATE.protocols[name] = func

    wm_protocol = protocol

    def state(self, newstate=None):
        return "normal"

    wm_state = state

    def resizable(self, width=None, height=None):
        if width is None and height is None:
            return (1, 1)
        self._resizable = (width, height)


# ====================================================================== window
class Tk(Misc, _Wm):
    _wclass = "Tk"
    _is_window = True

    def __init__(self, screenName=None, baseName=None, className="Tk", useTk=True, sync=False, use=None):
        self._init_misc()
        self.master = None
        self._title = "tk"
        self._title_set = False
        self._geometry = None
        self._geometry_set = False
        STATE.roots.append(self)
        if STATE.default_root is None:
            STATE.default_root = self

    def destroy(self):
        super().destroy()
        if self in STATE.roots:
            STATE.roots.remove(self)
        if STATE.default_root is self:
            STATE.default_root = STATE.roots[0] if STATE.roots else None

    def report_callback_exception(self, exc, val, tb):
        STATE.callback_errors.append(f"{exc.__name__}: {val}")


class Widget(Misc):
    _wclass = "Widget"

    def __init__(self, master=None, cnf=None, **kw):
        self._init_misc()
        if master is None:
            master = _akar_bawaan()
        self.master = master
        nama = "!" + type(self).__name__.lower()
        n = master._last_ids.get(nama, 0) + 1
        master._last_ids[nama] = n
        self._name = nama if n == 1 else f"{nama}{n}"
        master._children.append(self)
        STATE.widgets.append(self)
        self._init_state()
        merged = dict(cnf or {})
        merged.update(kw)
        self._set_options(merged)
        self._setelah_dibuat()

    def _init_state(self):
        pass

    def _setelah_dibuat(self):
        pass

    def _teks_opsi(self):
        tv = self._opts.get("textvariable")
        if isinstance(tv, Variable):
            try:
                return str(tv.get())
            except TclError:
                return ""
        return str(self._opts.get("text", ""))

    def teks(self):
        """Teks yang tampil di widget (None kalau widget tidak menampilkan teks)."""
        return self._teks_opsi()

    def __repr__(self):
        return f"<{type(self).__name__} {self._path()}>"

    def destroy(self):
        super().destroy()
        if self in self.master._children:
            self.master._children.remove(self)

    def focus(self):
        pass

    focus_set = focus_force = focus


class Toplevel(Widget, _Wm):
    _wclass = "Toplevel"
    _is_window = True

    def _init_state(self):
        self._title = "tk"
        self._title_set = False
        self._geometry = None
        self._geometry_set = False

    def teks(self):
        return None


class Frame(Widget):
    _wclass = "Frame"

    def teks(self):
        return None


class LabelFrame(Widget):
    _wclass = "LabelFrame"


class Label(Widget):
    _wclass = "Label"


class Message(Widget):
    _wclass = "Message"


class Button(Widget):
    _wclass = "Button"

    def invoke(self):
        if str(self._opts.get("state", "normal")) == "disabled":
            return None
        cmd = self._opts.get("command")
        if callable(cmd):
            return jalankan_callback(cmd)
        return None

    def flash(self):
        pass


class Radiobutton(Widget):
    _wclass = "Radiobutton"

    def _setelah_dibuat(self):
        self._var_bawaan = not isinstance(self._opts.get("variable"), Variable)
        if self._var_bawaan:
            self._opts["variable"] = _var_radio_bawaan()

    def select(self):
        v = self._opts.get("variable")
        if isinstance(v, Variable):
            v.set(self._opts.get("value", ""))

    def deselect(self):
        v = self._opts.get("variable")
        if isinstance(v, Variable) and str(v._value) == str(self._opts.get("value", "")):
            v.set("")

    def terpilih(self):
        v = self._opts.get("variable")
        return isinstance(v, Variable) and str(v._value) == str(self._opts.get("value", ""))

    def invoke(self):
        if str(self._opts.get("state", "normal")) == "disabled":
            return None
        self.select()
        cmd = self._opts.get("command")
        if callable(cmd):
            return jalankan_callback(cmd)
        return None

    def flash(self):
        pass


_radio_bawaan = []


def _var_radio_bawaan():
    if not _radio_bawaan or _radio_bawaan[0]._master is not STATE.default_root:
        _radio_bawaan[:] = [StringVar(STATE.default_root or _akar_bawaan())]
    return _radio_bawaan[0]


class Checkbutton(Widget):
    _wclass = "Checkbutton"

    def _setelah_dibuat(self):
        if not isinstance(self._opts.get("variable"), Variable):
            self._opts["variable"] = IntVar(self.master)

    def _on(self):
        return self._opts.get("onvalue", 1)

    def _off(self):
        return self._opts.get("offvalue", 0)

    def select(self):
        self._opts["variable"].set(self._on())

    def deselect(self):
        self._opts["variable"].set(self._off())

    def toggle(self):
        if str(self._opts["variable"]._value) == str(self._on()):
            self.deselect()
        else:
            self.select()

    def terpilih(self):
        return str(self._opts["variable"]._value) == str(self._on())

    def invoke(self):
        if str(self._opts.get("state", "normal")) == "disabled":
            return None
        self.toggle()
        cmd = self._opts.get("command")
        if callable(cmd):
            return jalankan_callback(cmd)
        return None

    def flash(self):
        pass


class Entry(Widget):
    _wclass = "Entry"

    def _init_state(self):
        self._sendiri = ""
        self._kursor = 0

    def _var(self):
        v = self._opts.get("textvariable")
        return v if isinstance(v, Variable) else None

    def get(self):
        v = self._var()
        return str(v.get()) if v is not None else self._sendiri

    def teks(self):
        return self.get()

    def _isi(self, baru):
        v = self._var()
        if v is not None:
            v.set(baru)
        else:
            self._sendiri = baru

    def _idx(self, index, teks):
        if index in ("end", "END"):
            return len(teks)
        if index == "insert":
            return min(self._kursor, len(teks))
        try:
            i = int(index)
        except (TypeError, ValueError):
            raise TclError(f'bad entry index "{index}"')
        return max(0, min(i, len(teks)))

    def _bisa_edit(self):
        return str(self._opts.get("state", "normal")) == "normal"

    def insert(self, index, string):
        if not self._bisa_edit():
            return
        teks = self.get()
        a = self._idx(index, teks)
        self._isi(teks[:a] + str(string) + teks[a:])
        self._kursor = a + len(str(string))

    def delete(self, first, last=None):
        if not self._bisa_edit():
            return
        teks = self.get()
        a = self._idx(first, teks)
        b = self._idx(last, teks) if last is not None else a + 1
        self._isi(teks[:a] + teks[b:])
        self._kursor = a

    def icursor(self, index):
        self._kursor = self._idx(index, self.get())

    def index(self, index):
        return self._idx(index, self.get())

    def selection_range(self, start, end):
        pass

    select_range = selection_range


class Spinbox(Entry):
    _wclass = "Spinbox"


class Text(Widget):
    _wclass = "Text"

    def _init_state(self):
        self._isi = ""
        self._ins = 0

    def teks(self):
        return self._isi

    def _off(self, index):
        full = len(self._isi) + 1
        s = str(index).strip()
        m = re.fullmatch(r"(.*?)((?:\s*[+-]\s*\d+\s*c(?:hars?)?)*)", s)
        base, mods = m.group(1).strip(), m.group(2)
        if base == "end":
            off = full
        elif base in ("insert", "current", "sel.first", "sel.last"):
            off = self._ins
        else:
            mm = re.fullmatch(r"(\d+)\.(\d+|end)", base)
            if not mm:
                raise TclError(f'bad text index "{index}"')
            baris = int(mm.group(1))
            lines = (self._isi + "\n").split("\n")
            baris = max(1, min(baris, len(lines)))
            awal = sum(len(lines[i]) + 1 for i in range(baris - 1))
            kol = len(lines[baris - 1]) if mm.group(2) == "end" else min(int(mm.group(2)), len(lines[baris - 1]))
            off = awal + kol
        for tanda, n in re.findall(r"([+-])\s*(\d+)", mods):
            off += int(n) if tanda == "+" else -int(n)
        return max(0, min(off, full))

    def _bisa_edit(self):
        return str(self._opts.get("state", "normal")) == "normal"

    def get(self, index1, index2=None):
        full = self._isi + "\n"
        a = self._off(index1)
        b = self._off(index2) if index2 is not None else a + 1
        return full[a:b]

    def insert(self, index, chars, *args):
        if not self._bisa_edit():
            return
        a = min(self._off(index), len(self._isi))
        self._isi = self._isi[:a] + str(chars) + self._isi[a:]
        self._ins = a + len(str(chars))

    def delete(self, index1, index2=None):
        if not self._bisa_edit():
            return
        a = self._off(index1)
        b = self._off(index2) if index2 is not None else a + 1
        b = min(b, len(self._isi))
        if a < b:
            self._isi = self._isi[:a] + self._isi[b:]

    def index(self, index):
        return str(index)


class Listbox(Widget):
    _wclass = "Listbox"

    def _init_state(self):
        self._items = []
        self._sel = set()

    def teks(self):
        return "\n".join(self._items)

    def _i(self, i):
        if i in ("end", "END"):
            return len(self._items)
        if i in ("active", "anchor"):
            return 0
        return int(i)

    def insert(self, index, *elements):
        a = self._i(index)
        self._items[a:a] = [str(e) for e in elements]

    def delete(self, first, last=None):
        a = self._i(first)
        b = (self._i(last) + 1) if last is not None else a + 1
        del self._items[a:b]
        self._sel = {i for i in self._sel if i < len(self._items)}

    def get(self, first, last=None):
        a = self._i(first)
        if last is None:
            return self._items[a] if 0 <= a < len(self._items) else ""
        return tuple(self._items[a:self._i(last) + 1])

    def size(self):
        return len(self._items)

    def curselection(self):
        return tuple(sorted(self._sel))

    def selection_set(self, first, last=None):
        a = self._i(first)
        b = self._i(last) if last is not None else a
        self._sel.update(range(a, b + 1))

    select_set = selection_set

    def selection_clear(self, first, last=None):
        self._sel.clear()

    select_clear = selection_clear

    def index(self, index):
        return self._i(index)

    def see(self, index):
        pass

    def activate(self, index):
        pass


class Scrollbar(Widget):
    _wclass = "Scrollbar"

    def teks(self):
        return None


class Scale(Widget):
    _wclass = "Scale"

    def _setelah_dibuat(self):
        self._nilai = self._opts.get("from", 0)

    def get(self):
        return self._nilai

    def set(self, value):
        self._nilai = value

    def teks(self):
        return None


class Canvas(Widget):
    _wclass = "Canvas"

    def teks(self):
        return None

    def __getattr__(self, name):
        if name.startswith("create_"):
            def buat(*a, **k):
                STATE.canvas_id += 1
                return STATE.canvas_id
            return buat
        return Misc.__getattr__(self, name)


class Menu(Widget):
    _wclass = "Menu"

    def _init_state(self):
        self._entri = []

    def teks(self):
        return None

    def _tambah(self, jenis, kw):
        self._entri.append((jenis, kw))

    def add_command(self, cnf=None, **kw):
        self._tambah("command", dict(cnf or {}, **kw))

    def add_cascade(self, cnf=None, **kw):
        self._tambah("cascade", dict(cnf or {}, **kw))

    def add_separator(self, cnf=None, **kw):
        self._tambah("separator", {})

    def add_checkbutton(self, cnf=None, **kw):
        self._tambah("checkbutton", dict(cnf or {}, **kw))

    def add_radiobutton(self, cnf=None, **kw):
        self._tambah("radiobutton", dict(cnf or {}, **kw))

    def add(self, itemType, cnf=None, **kw):
        self._tambah(itemType, dict(cnf or {}, **kw))

    def entryconfigure(self, index, cnf=None, **kw):
        pass

    entryconfig = entryconfigure

    def delete(self, index1, index2=None):
        pass

    def tk_popup(self, x, y, entry=""):
        pass


class Menubutton(Widget):
    _wclass = "Menubutton"


class PanedWindow(Widget):
    _wclass = "PanedWindow"

    def add(self, child, **kw):
        pass

    def teks(self):
        return None


class OptionMenu(Widget):
    _wclass = "Menubutton"

    def __init__(self, master, variable, value, *values, **kwargs):
        super().__init__(master)
        self._variabel = variable
        self._pilihan = (value,) + values
        if isinstance(variable, Variable) and str(variable._value) == "":
            variable.set(value)

    def teks(self):
        return str(self._variabel.get()) if isinstance(self._variabel, Variable) else ""


class PhotoImage:
    def __init__(self, name=None, cnf=None, master=None, **kw):
        self._kw = kw

    def width(self):
        return 1

    def height(self):
        return 1

    def subsample(self, x, y=""):
        return self

    def zoom(self, x, y=""):
        return self

    def configure(self, **kw):
        pass

    config = configure


BitmapImage = PhotoImage


# ====================================================================== sub-modul
def _modul(nama, isi):
    m = types.ModuleType(nama)
    m.__dict__.update(isi)
    return m


def _buat_messagebox():
    def dialog(jenis, jawaban):
        def f(title=None, message=None, **options):
            STATE.dialogs.append({"jenis": jenis, "judul": title, "pesan": message})
            return STATE.jawaban.get(jenis, jawaban)
        f.__name__ = jenis
        return f

    isi = {
        "showinfo": dialog("showinfo", "ok"),
        "showwarning": dialog("showwarning", "ok"),
        "showerror": dialog("showerror", "ok"),
        "askyesno": dialog("askyesno", True),
        "askokcancel": dialog("askokcancel", True),
        "askretrycancel": dialog("askretrycancel", False),
        "askquestion": dialog("askquestion", "yes"),
        "askyesnocancel": dialog("askyesnocancel", True),
        "ERROR": "error", "INFO": "info", "QUESTION": "question", "WARNING": "warning",
        "ABORTRETRYIGNORE": "abortretryignore", "OK": "ok", "OKCANCEL": "okcancel",
        "RETRYCANCEL": "retrycancel", "YESNO": "yesno", "YESNOCANCEL": "yesnocancel",
        "ABORT": "abort", "RETRY": "retry", "IGNORE": "ignore", "CANCEL": "cancel",
        "YES": "yes", "NO": "no",
    }
    return _modul("tkinter.messagebox", isi)


def _buat_filedialog():
    def dialog(jenis, kosong):
        def f(*args, **options):
            STATE.dialogs.append({"jenis": jenis, "judul": options.get("title"), "pesan": None})
            return STATE.jawaban.get(jenis, kosong)
        f.__name__ = jenis
        return f

    isi = {
        "askopenfilename": dialog("askopenfilename", ""),
        "askopenfilenames": dialog("askopenfilenames", ()),
        "asksaveasfilename": dialog("asksaveasfilename", ""),
        "askdirectory": dialog("askdirectory", ""),
        "askopenfile": dialog("askopenfile", None),
        "askopenfiles": dialog("askopenfiles", ()),
        "asksaveasfile": dialog("asksaveasfile", None),
    }
    return _modul("tkinter.filedialog", isi)


def _buat_simpledialog():
    def dialog(jenis):
        def f(title=None, prompt=None, **options):
            STATE.dialogs.append({"jenis": jenis, "judul": title, "pesan": prompt})
            return STATE.jawaban.get(jenis)
        f.__name__ = jenis
        return f

    return _modul("tkinter.simpledialog", {
        "askstring": dialog("askstring"), "askinteger": dialog("askinteger"), "askfloat": dialog("askfloat"),
    })


def _buat_colorchooser():
    def askcolor(color=None, **options):
        STATE.dialogs.append({"jenis": "askcolor", "judul": options.get("title"), "pesan": None})
        return (None, None)

    return _modul("tkinter.colorchooser", {"askcolor": askcolor})


def _buat_font():
    class Font:
        def __init__(self, root=None, font=None, name=None, exists=False, **options):
            self._opts = dict(options)

        def configure(self, **kw):
            self._opts.update(kw)

        config = configure

        def cget(self, key):
            return self._opts.get(key)

        __getitem__ = cget

        def actual(self, option=None, displayof=None):
            return self._opts if option is None else self._opts.get(option)

        def measure(self, text, displayof=None):
            return 8 * len(str(text))

        def metrics(self, *options, **kw):
            return 16 if options else {"ascent": 12, "descent": 4, "linespace": 16, "fixed": 0}

        def copy(self):
            return Font(**self._opts)

    return _modul("tkinter.font", {
        "Font": Font,
        "families": lambda root=None, displayof=None: ("Arial", "Courier", "Helvetica", "Times"),
        "nametofont": lambda name, root=None: Font(),
        "NORMAL": "normal", "ROMAN": "roman", "BOLD": "bold", "ITALIC": "italic",
    })


def _buat_scrolledtext():
    class ScrolledText(Text):
        pass

    return _modul("tkinter.scrolledtext", {"ScrolledText": ScrolledText})


def _buat_ttk():
    def kelas(nama, dasar, **extra):
        ns = {"_estricto": False}
        ns.update(extra)
        return type(nama, (dasar,), ns)

    class Combobox(Entry):
        _estricto = False

        def _setelah_dibuat(self):
            if "values" not in self._opts:
                self._opts["values"] = ()

        def set(self, value):
            self._isi(str(value))

        def current(self, newindex=None):
            vals = [str(v) for v in self._opts.get("values", ())]
            if newindex is None:
                return vals.index(self.get()) if self.get() in vals else -1
            self._isi(vals[newindex])

    class Progressbar(Widget):
        _estricto = False

        def teks(self):
            return None

        def start(self, interval=None):
            pass

        def stop(self):
            pass

        def step(self, amount=None):
            self._opts["value"] = self._opts.get("value", 0) + (amount if amount is not None else 1)

    class Notebook(Widget):
        _estricto = False

        def teks(self):
            return None

        def add(self, child, **kw):
            pass

    class Treeview(Widget):
        _estricto = False

        def _init_state(self):
            self._baris = {}
            self._urut = []

        def teks(self):
            return "\n".join(str(self._baris[i].get("values", ())) for i in self._urut)

        def insert(self, parent, index, iid=None, **kw):
            iid = iid or f"I{len(self._urut) + 1:03d}"
            self._baris[iid] = kw
            self._urut.append(iid)
            return iid

        def delete(self, *items):
            for i in items:
                if i in self._baris:
                    del self._baris[i]
                    self._urut.remove(i)

        def get_children(self, item=None):
            return tuple(self._urut)

        def item(self, item, option=None, **kw):
            if kw:
                self._baris[item].update(kw)
                return None
            return self._baris[item] if option is None else self._baris[item].get(option)

        def heading(self, column, option=None, **kw):
            pass

        def column(self, column, option=None, **kw):
            pass

        def selection(self, *a):
            return ()

        def focus(self, item=None):
            return ""

        def set(self, item, column=None, value=None):
            pass

    class Style:
        def __init__(self, master=None):
            pass

        def __getattr__(self, name):
            return _noop

    return _modul("tkinter.ttk", {
        "Label": kelas("Label", Label), "Button": kelas("Button", Button),
        "Entry": kelas("Entry", Entry), "Frame": kelas("Frame", Frame),
        "LabelFrame": kelas("LabelFrame", LabelFrame), "Labelframe": kelas("LabelFrame", LabelFrame),
        "Checkbutton": kelas("Checkbutton", Checkbutton), "Radiobutton": kelas("Radiobutton", Radiobutton),
        "Scale": kelas("Scale", Scale), "Spinbox": kelas("Spinbox", Spinbox),
        "Scrollbar": kelas("Scrollbar", Scrollbar), "Separator": kelas("Separator", Frame),
        "Combobox": Combobox, "Progressbar": Progressbar, "Notebook": Notebook,
        "Treeview": Treeview, "Style": Style,
    })


# ====================================================================== pemasangan
class _Pencari(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, moduls):
        self.moduls = moduls

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.moduls:
            return importlib.machinery.ModuleSpec(fullname, self)
        return None

    def create_module(self, spec):
        return self.moduls[spec.name]

    def exec_module(self, module):
        pass


_pencari_aktif = []


def install():
    """Pasang modul `tkinter` tiruan ke sys.modules (dan pasang ulang tiap tes)."""
    for nama in [n for n in sys.modules if n == "tkinter" or n.startswith("tkinter.")]:
        del sys.modules[nama]
    for p in _pencari_aktif:
        if p in sys.meta_path:
            sys.meta_path.remove(p)
    _pencari_aktif.clear()

    tk = types.ModuleType("tkinter")
    tk.__path__ = []
    kelas = {
        "Tk": Tk, "Toplevel": Toplevel, "Frame": Frame, "LabelFrame": LabelFrame, "Label": Label,
        "Message": Message, "Button": Button, "Radiobutton": Radiobutton, "Checkbutton": Checkbutton,
        "Entry": Entry, "Spinbox": Spinbox, "Text": Text, "Listbox": Listbox, "Scrollbar": Scrollbar,
        "Scale": Scale, "Canvas": Canvas, "Menu": Menu, "Menubutton": Menubutton,
        "PanedWindow": PanedWindow, "OptionMenu": OptionMenu, "PhotoImage": PhotoImage,
        "BitmapImage": BitmapImage, "Variable": Variable, "StringVar": StringVar, "IntVar": IntVar,
        "DoubleVar": DoubleVar, "BooleanVar": BooleanVar, "Event": Event, "TclError": TclError,
        "Misc": Misc, "Widget": Widget, "Wm": _Wm,
    }
    tk.__dict__.update(kelas)
    tk.__dict__.update(_META["konstanta"])
    tk.TkVersion = 8.6
    tk.TclVersion = 8.6
    tk.mainloop = lambda n=0: STATE.__setattr__("mainloop", STATE.mainloop + 1)
    tk.NoDefaultRoot = _noop
    tk.getint = int
    tk.getdouble = float
    tk.getboolean = BooleanVar._ke_bool
    tk.__all__ = [n for n in tk.__dict__ if not n.startswith("_")]

    moduls = {
        "tkinter.messagebox": _buat_messagebox(), "tkinter.filedialog": _buat_filedialog(),
        "tkinter.simpledialog": _buat_simpledialog(), "tkinter.colorchooser": _buat_colorchooser(),
        "tkinter.font": _buat_font(), "tkinter.scrolledtext": _buat_scrolledtext(),
        "tkinter.ttk": _buat_ttk(),
        "tkinter.constants": _modul("tkinter.constants", _META["konstanta"]),
    }
    pencari = _Pencari(moduls)
    sys.meta_path.insert(0, pencari)
    _pencari_aktif.append(pencari)
    sys.modules["tkinter"] = tk


_NOOP = frozenset(_META["method"]) if _META else frozenset()


# ====================================================================== bantuan untuk grader
def semua_widget():
    return [w for w in STATE.widgets if not w._destroyed]


def terlihat(w):
    """Widget tampil di jendela kalau dirinya dan semua induknya sudah di-pack/grid/place."""
    while w is not None and not w._is_window:
        if w._manager is None or w._destroyed:
            return False
        w = w.master
    return True


def ketik(entry, teks):
    """Meniru user mengetik di Entry. Mengembalikan (berhasil, catatan)."""
    if not entry._bisa_edit():
        return False, f"Entry tidak bisa diketik (state={entry._opts.get('state')})"
    entry.delete(0, "end")
    entry.insert(0, teks)
    return True, ""


def _ringkas_layout(w):
    if w._manager is None:
        return "BELUM di-pack/grid/place"
    kunci = ("row", "column", "rowspan", "columnspan", "sticky", "side", "fill", "expand", "x", "y")
    isi = ", ".join(f"{k}={w._mgr_opts[k]!r}" for k in kunci if k in w._mgr_opts)
    return f"{w._manager}({isi})"


def pohon():
    """Ringkasan susunan widget (untuk ditampilkan ke praktikan)."""
    baris = []

    def tulis(w, dalam):
        kelas = type(w).__name__
        if w._is_window:
            ket = f'"{w._title}"' + (f" {w._geometry}" if w._geometry else "")
        else:
            t = w.teks()
            ket = f'"{t[:28]}"' if t else ""
            if isinstance(w, Radiobutton):
                v = w._opts.get("variable")
                ket += f" variabel={v._name if isinstance(v, Variable) else '?'} value={w._opts.get('value', '')!r}"
        pad = "  " * dalam
        tambah = "" if w._is_window else "   " + _ringkas_layout(w)
        baris.append(f"{pad}{kelas} {ket}{tambah}".rstrip())
        for c in w._children:
            if not c._destroyed:
                tulis(c, dalam + 1)

    for r in STATE.roots:
        tulis(r, 0)
    return "\n".join(baris)
