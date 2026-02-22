"""StylesMixin — TTK theme and color palette configuration."""
from tkinter import ttk


class StylesMixin:
    def configure_styles(self):
        """Configure clean light theme (white background, black text)"""
        style = ttk.Style()
        style.theme_use('clam')

        # ── Color palette (clean light) ──────────────────────────────────
        self.colors = {
            'bg':          '#ffffff',   # root background (white)
            'panel':       '#f5f7fa',   # panel / card background (very light gray)
            'sidebar':     '#eef1f6',   # sidebar background
            'input_bg':    '#ffffff',   # entry/text widget background
            'border':      '#d0d7de',   # borders
            'accent':      '#0969da',   # primary blue (GitHub blue)
            'accent_hover':'#0550ae',   # hover state
            'success':     '#1a7f37',   # green
            'warning':     '#9a6700',   # amber
            'error':       '#cf222e',   # red
            'fg':          '#1f2328',   # primary text (near-black)
            'fg_muted':    '#656d76',   # secondary text (medium gray)
            'topbar':      '#24292f',   # header bar (dark)
            'topbar_fg':   '#ffffff',   # header text (white)
            # Chat message colours (agent log panel has dark bg for readability)
            'log_bg':      '#1e1e2e',   # log panel background (dark)
            'user_msg':    '#56d2ba',   # teal — user messages
            'agent_msg':   '#e8eaf0',   # light — agent replies
            'thinking':    '#888ea8',   # gray italic — thinking
            'success_msg': '#4ade80',   # bright green
            'error_msg':   '#f87171',   # bright red
            'question':    '#fb923c',   # orange
            'info':        '#60a5fa',   # light blue
            'action':      '#c084fc',   # purple
        }
        C = self.colors

        # ── Root background ──────────────────────────────────────────────
        self.root.configure(bg=C['bg'])

        # ── ttk global ──────────────────────────────────────────────────
        style.configure('.',
            background=C['panel'],
            foreground=C['fg'],
            fieldbackground=C['input_bg'],
            troughcolor=C['border'],
            selectbackground=C['accent'],
            selectforeground='#ffffff',
            font=('Segoe UI', 10),
        )
        style.configure('TFrame',      background=C['panel'])
        style.configure('TLabelframe', background=C['panel'], foreground=C['fg'],
                        bordercolor=C['border'])
        style.configure('TLabelframe.Label',
                        background=C['panel'], foreground=C['accent'],
                        font=('Segoe UI', 9, 'bold'))
        style.configure('TLabel',      background=C['panel'], foreground=C['fg'])
        style.configure('TEntry',      fieldbackground=C['input_bg'],
                        foreground=C['fg'], insertcolor=C['fg'],
                        bordercolor=C['border'])
        style.configure('TCombobox',   fieldbackground=C['input_bg'],
                        foreground=C['fg'], selectbackground=C['accent'],
                        background=C['input_bg'])
        style.configure('TScrollbar',  background=C['border'], troughcolor=C['panel'],
                        arrowcolor=C['fg_muted'])
        style.configure('TNotebook',   background=C['bg'], bordercolor=C['border'])
        style.configure('TNotebook.Tab',
                        background=C['panel'], foreground=C['fg_muted'],
                        padding=(12, 6), font=('Segoe UI', 10))
        style.map('TNotebook.Tab',
                  background=[('selected', C['bg'])],
                  foreground=[('selected', C['fg'])])
        style.configure('Horizontal.TProgressbar',
                        troughcolor=C['border'], background=C['accent'])
        style.configure('TPanedwindow', background=C['border'])
        style.configure('Sash', sashrelief='flat', sashpad=3, background=C['border'])

        # ── Buttons ──────────────────────────────────────────────────────
        _btn = dict(font=('Segoe UI', 10), padding=(10, 6), borderwidth=1, relief='solid')
        style.configure('TButton',
                        background=C['panel'], foreground=C['fg'],
                        bordercolor=C['border'], **_btn)
        style.map('TButton',
                  background=[('active', C['border']), ('pressed', '#c8d0da')])

        style.configure('Accent.TButton',
                        background=C['accent'], foreground='#ffffff',
                        bordercolor=C['accent'], **_btn)
        style.map('Accent.TButton',
                  background=[('active', C['accent_hover']), ('pressed', '#044289')])

        style.configure('Approve.TButton',
                        background=C['success'], foreground='#ffffff',
                        bordercolor=C['success'], **_btn)
        style.map('Approve.TButton',
                  background=[('active', '#15652c'), ('pressed', '#104d22')])

        style.configure('Reject.TButton',
                        background=C['error'], foreground='#ffffff',
                        bordercolor=C['error'], **_btn)
        style.map('Reject.TButton',
                  background=[('active', '#a8001a'), ('pressed', '#82001a')])

        style.configure('Warn.TButton',
                        background='#9a6700', foreground='#ffffff',
                        bordercolor='#9a6700', **_btn)

        # ── Checkbutton ──────────────────────────────────────────────────
        style.configure('TCheckbutton',
                        background=C['panel'], foreground=C['fg'],
                        focuscolor=C['panel'])
        style.map('TCheckbutton',
                  background=[('active', C['panel'])],
                  foreground=[('active', C['fg'])])

        # ── Labels ───────────────────────────────────────────────────────
        style.configure('Title.TLabel',
                        font=('Segoe UI', 16, 'bold'),
                        foreground=C['fg'], background=C['panel'])
        style.configure('Header.TLabel',
                        font=('Segoe UI', 11, 'bold'),
                        foreground=C['fg'], background=C['panel'])
        style.configure('Sidebar.TLabel',
                        font=('Segoe UI', 9, 'bold'),
                        foreground=C['fg_muted'], background=C['sidebar'])
        style.configure('Muted.TLabel',
                        font=('Segoe UI', 8),
                        foreground=C['fg_muted'], background=C['panel'])
        style.configure('Task.TLabel',
                        font=('Segoe UI', 10), background=C['panel'], foreground=C['fg'])
        style.configure('TaskPending.TLabel',
                        font=('Segoe UI', 10), background=C['panel'], foreground=C['fg_muted'])
        style.configure('TaskActive.TLabel',
                        font=('Segoe UI', 10, 'bold'), background=C['panel'],
                        foreground=C['accent'])
        style.configure('TaskDone.TLabel',
                        font=('Segoe UI', 10), background=C['panel'],
                        foreground=C['success'])
        style.configure('Status.TLabel',
                        font=('Segoe UI', 9), background=C['panel'],
                        foreground=C['fg_muted'])
        style.configure('TopBar.TLabel',
                        font=('Segoe UI', 12, 'bold'),
                        foreground=C['topbar_fg'], background=C['topbar'])
        style.configure('TopBarRepo.TLabel',
                        font=('Segoe UI', 10),
                        foreground='#adbac7', background=C['topbar'])
        style.configure('SectionHead.TLabel',
                        font=('Segoe UI', 8, 'bold'),
                        foreground=C['fg_muted'], background=C['sidebar'])
        
