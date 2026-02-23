"""LayoutMixin — all widget creation and panel layout methods."""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


class LayoutMixin:
    def build_ui(self):
        """Build main UI: dark top bar + 3-panel split (sidebar | center | agent log)"""
        C = self.colors

        # ── Top bar ────────────────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg=C['topbar'], height=40)
        topbar.pack(fill=tk.X, side=tk.TOP)
        topbar.pack_propagate(False)

        tk.Label(topbar, text="GitIntel", font=('Segoe UI', 13, 'bold'),
                 fg=C['topbar_fg'], bg=C['topbar']).pack(side=tk.LEFT, padx=12, pady=8)

        tk.Label(topbar, text="|", fg='#555d66', bg=C['topbar']).pack(side=tk.LEFT)

        tk.Label(topbar, text="Agentic Dataset Generator",
                 font=('Segoe UI', 10), fg='#adbac7',
                 bg=C['topbar']).pack(side=tk.LEFT, padx=8)

        tk.Label(topbar, text="|", fg='#555d66', bg=C['topbar']).pack(side=tk.LEFT)

        self.topbar_repo_var = tk.StringVar(value="No repository set")
        tk.Label(topbar, textvariable=self.topbar_repo_var,
                 font=('Segoe UI', 10, 'bold'), fg='#79c0ff',
                 bg=C['topbar']).pack(side=tk.LEFT, padx=8)

        # Status indicator on right
        self.topbar_status_var = tk.StringVar(value="Ready")
        tk.Label(topbar, textvariable=self.topbar_status_var,
                 font=('Segoe UI', 9), fg='#57ab5a',
                 bg=C['topbar']).pack(side=tk.RIGHT, padx=12)

        # ── Resizable 3-panel body (PanedWindow) ──────────────────────────
        body_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL,
                                   sashwidth=5, sashrelief='flat',
                                   bg=C['border'])
        body_pane.pack(fill=tk.BOTH, expand=True)

        # Sidebar (left, resizable min 160px)
        self.sidebar_frame = tk.Frame(body_pane, bg=C['sidebar'])
        body_pane.add(self.sidebar_frame, minsize=160, width=240)

        # Center panel (fills remaining space)
        self.center_frame = tk.Frame(body_pane, bg=C['bg'])
        body_pane.add(self.center_frame, minsize=280)

        # Right agent log (resizable min 260px)
        self.right_frame = tk.Frame(body_pane, bg=C['panel'])
        body_pane.add(self.right_frame, minsize=260, width=400)

        # Also alias left_frame to center for legacy code compatibility
        self.left_frame = self.center_frame

        self.build_sidebar()
        self.build_center_panel()
        self.build_agent_panel()

        # ── Bottom status bar ─────────────────────────────────────────────
        statusbar = tk.Frame(self.root, bg=C['border'], height=24)
        statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        statusbar.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(statusbar, textvariable=self.status_var,
                 font=('Segoe UI', 8), fg=C['fg_muted'],
                 bg=C['border']).pack(side=tk.LEFT, padx=8, pady=3)

        self.output_path_var = tk.StringVar(value="")
        tk.Label(statusbar, textvariable=self.output_path_var,
                 font=('Segoe UI', 8, 'italic'), fg='#0969da',
                 bg=C['border']).pack(side=tk.RIGHT, padx=8, pady=3)

    # ── backward-compat shim: notebooks / tabs not used now ───────────

    def build_dataset_tab(self):
        pass

    def _section_header(self, parent, text):
        """Thin uppercase section label for sidebar"""
        tk.Label(parent, text=text.upper(),
                 font=('Segoe UI', 7, 'bold'),
                 fg=self.colors['fg_muted'], bg=self.colors['sidebar']).pack(
            anchor=tk.W, padx=10, pady=(10, 2))

    def build_sidebar(self):
        """Left sidebar: repo, benchmarks (checkboxes), metrics, limit, generate"""
        C = self.colors
        sb = self.sidebar_frame

        # ── REPOSITORY ────────────────────────────────────────────────────
        self._section_header(sb, "Repository")
        repo_card = tk.Frame(sb, bg=C['panel'], relief='flat', bd=1)
        repo_card.pack(fill=tk.X, padx=8, pady=(0, 4))

        self.repo_var = tk.StringVar()
        self.repo_entry = tk.Entry(repo_card, textvariable=self.repo_var,
                                   font=('Segoe UI', 9),
                                   bg=C['input_bg'], fg=C['fg'],
                                   relief='solid', bd=1,
                                   insertbackground=C['fg'])
        self.repo_entry.pack(fill=tk.X, padx=6, pady=(6, 0))
        self.repo_entry.insert(0, "Path or GitHub URL...")
        self.repo_entry.bind('<FocusIn>', self.on_repo_focus)

        btn_row = tk.Frame(repo_card, bg=C['panel'])
        btn_row.pack(fill=tk.X, padx=6, pady=4)

        for txt, cmd in [("Browse", self.browse_folder),
                         ("Clone", self.clone_repository),
                         ("Set", self.set_repository)]:
            tk.Button(btn_row, text=txt,
                      font=('Segoe UI', 8), bg=C['input_bg'], fg=C['fg'],
                      relief='solid', bd=1, cursor='hand2',
                      activebackground=C['border'],
                      command=cmd).pack(side=tk.LEFT, padx=2, pady=1, fill=tk.X, expand=True)

        self.repo_status = tk.Label(repo_card, text="",
                                    font=('Segoe UI', 8), bg=C['panel'], fg=C['fg_muted'],
                                    wraplength=200, justify=tk.LEFT)
        self.repo_status.pack(anchor=tk.W, padx=6, pady=(0, 4))

        # ── BENCHMARKS ───────────────────────────────────────────────────
        self._section_header(sb, "Benchmarks")
        bench_card = tk.Frame(sb, bg=C['panel'], relief='flat', bd=1)
        bench_card.pack(fill=tk.X, padx=8, pady=(0, 4))

        bench_btn_row = tk.Frame(bench_card, bg=C['panel'])
        bench_btn_row.pack(fill=tk.X, padx=4, pady=(4, 2))

        tk.Button(bench_btn_row, text="All", font=('Segoe UI', 7),
                  bg=C['accent'], fg='white', relief='flat', cursor='hand2',
                  activebackground=C['accent_hover'],
                  command=lambda: self._set_all_benchmarks(True)).pack(
            side=tk.LEFT, padx=2)
        tk.Button(bench_btn_row, text="None", font=('Segoe UI', 7),
                  bg=C['input_bg'], fg=C['fg'], relief='solid', bd=1, cursor='hand2',
                  activebackground=C['border'],
                  command=lambda: self._set_all_benchmarks(False)).pack(
            side=tk.LEFT, padx=2)

        self.benchmark_vars: dict[str, tk.BooleanVar] = {}
        BENCHMARKS = ["Defects4J", "Bugs.jar", "PROMISE",
                      "CodeXGLUE", "CodeSearchNet", "ManySStuBs4J", "Sourcerer"]
        for bname in BENCHMARKS:
            var = tk.BooleanVar(value=False)
            self.benchmark_vars[bname] = var
            cb = tk.Checkbutton(bench_card, text=bname,
                                font=('Segoe UI', 9), variable=var,
                                bg=C['panel'], fg=C['fg'],
                                activebackground=C['panel'],
                                selectcolor=C['input_bg'],
                                cursor='hand2',
                                command=self._update_bench_count)
            cb.pack(anchor=tk.W, padx=8, pady=1)

        self.bench_count_var = tk.StringVar(value="0 selected")
        tk.Label(bench_card, textvariable=self.bench_count_var,
                 font=('Segoe UI', 8), bg=C['panel'],
                 fg=C['fg_muted']).pack(anchor=tk.W, padx=8, pady=(0, 4))

        # Keep backward-compat: benchmark_var (old single-select) defaults to None
        self.benchmark_var = tk.StringVar(value="None")

        # ── METRICS ───────────────────────────────────────────────────────
        self._section_header(sb, "Metrics")
        met_card = tk.Frame(sb, bg=C['panel'], relief='flat', bd=1)
        met_card.pack(fill=tk.X, padx=8, pady=(0, 4))

        met_row = tk.Frame(met_card, bg=C['panel'])
        met_row.pack(fill=tk.X, padx=6, pady=6)

        tk.Button(met_row, text="Select Metrics",
                  font=('Segoe UI', 9), bg=C['accent'], fg='white',
                  relief='flat', cursor='hand2', activebackground=C['accent_hover'],
                  command=self.show_metrics_selector).pack(side=tk.LEFT, padx=(0, 6))

        self.selected_metrics_count = tk.StringVar(value="0/65")
        tk.Label(met_row, textvariable=self.selected_metrics_count,
                 font=('Segoe UI', 9), bg=C['panel'], fg=C['fg_muted']).pack(side=tk.LEFT)

        self.combine_var = tk.BooleanVar(value=False)
        tk.Checkbutton(met_card, text="Combine with Benchmark",
                       font=('Segoe UI', 8), variable=self.combine_var,
                       bg=C['panel'], fg=C['fg'], activebackground=C['panel'],
                       selectcolor=C['input_bg']).pack(anchor=tk.W, padx=8, pady=(0, 4))

        # ── DATA LIMIT ────────────────────────────────────────────────────
        self._section_header(sb, "Data Limit")
        lim_card = tk.Frame(sb, bg=C['panel'], relief='flat', bd=1)
        lim_card.pack(fill=tk.X, padx=8, pady=(0, 4))

        lim_row = tk.Frame(lim_card, bg=C['panel'])
        lim_row.pack(fill=tk.X, padx=6, pady=6)

        self.file_limit_var = tk.StringVar(value="500")
        tk.Entry(lim_row, textvariable=self.file_limit_var, width=8,
                 font=('Segoe UI', 10), bg=C['input_bg'], fg=C['fg'],
                 relief='solid', bd=1,
                 insertbackground=C['fg']).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(lim_row, text="commits  (or 'all')",
                 font=('Segoe UI', 8), bg=C['panel'],
                 fg=C['fg_muted']).pack(side=tk.LEFT)

        # ── GENERATE DATASET ──────────────────────────────────────────────
        self._section_header(sb, "")
        tk.Button(sb, text="Generate Dataset",
                  font=('Segoe UI', 10, 'bold'),
                  bg=C['accent'], fg='white',
                  relief='flat', bd=0,
                  cursor='hand2',
                  activebackground=C['accent_hover'],
                  command=self.generate_from_selection).pack(
            fill=tk.X, padx=8, pady=(2, 4), ipady=6)

        tk.Button(sb, text="Clear Selection",
                  font=('Segoe UI', 9),
                  bg=C['input_bg'], fg=C['fg'],
                  relief='solid', bd=1, cursor='hand2',
                  activebackground=C['border'],
                  command=self.clear_selection).pack(
            fill=tk.X, padx=8, pady=(0, 4))

    def _update_bench_count(self):
        n = sum(1 for v in self.benchmark_vars.values() if v.get())
        self.bench_count_var.set(f"{n} selected")

    def _set_all_benchmarks(self, state: bool):
        for v in self.benchmark_vars.values():
            v.set(state)
        self._update_bench_count()

    def get_selected_benchmarks(self) -> list:
        """Return list of checked benchmark names"""
        return [k for k, v in self.benchmark_vars.items() if v.get()]

    def build_center_panel(self):
        """Center panel: task plan + chat input"""
        C = self.colors
        cp = self.center_frame

        # ── TASK PLAN ─────────────────────────────────────────────────────
        plan_outer = tk.Frame(cp, bg=C['bg'])
        plan_outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        plan_header = tk.Frame(plan_outer, bg=C['bg'])
        plan_header.pack(fill=tk.X, pady=(0, 6))

        tk.Label(plan_header, text="Task Plan",
                 font=('Segoe UI', 11, 'bold'),
                 fg=C['fg'], bg=C['bg']).pack(side=tk.LEFT)

        self.task_progress_var = tk.StringVar(value="0/0 tasks")
        tk.Label(plan_header, textvariable=self.task_progress_var,
                 font=('Segoe UI', 9), fg=C['fg_muted'],
                 bg=C['bg']).pack(side=tk.LEFT, padx=10)

        ctrl_row = tk.Frame(plan_header, bg=C['bg'])
        ctrl_row.pack(side=tk.RIGHT)

        self.start_btn = tk.Button(ctrl_row, text="Start",
                                   font=('Segoe UI', 9, 'bold'),
                                   bg=C['success'], fg='white',
                                   relief='flat', cursor='hand2',
                                   state=tk.DISABLED,
                                   activebackground='#15652c',
                                   command=self.start_execution)
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.pause_btn = tk.Button(ctrl_row, text="Pause",
                                   font=('Segoe UI', 9),
                                   bg=C['input_bg'], fg=C['fg'],
                                   relief='solid', bd=1, cursor='hand2',
                                   state=tk.DISABLED,
                                   command=self.pause_execution)
        self.pause_btn.pack(side=tk.LEFT, padx=2)

        tk.Button(ctrl_row, text="Clear",
                  font=('Segoe UI', 9),
                  bg=C['input_bg'], fg=C['fg'],
                  relief='solid', bd=1, cursor='hand2',
                  command=self.clear_plan).pack(side=tk.LEFT, padx=2)

        self.open_output_btn = tk.Button(
            ctrl_row, text="Open Output",
            font=('Segoe UI', 9),
            bg=C['accent'], fg='white',
            relief='flat', bd=0, cursor='hand2',
            state=tk.DISABLED,
            activebackground='#1a5276',
            command=self._open_output_folder)
        self.open_output_btn.pack(side=tk.LEFT, padx=2)

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(plan_outer,
                                            variable=self.progress_var,
                                            mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 6))

        # Scrollable task list
        task_scroll_frame = tk.Frame(plan_outer, bg=C['bg'])
        task_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.task_canvas = tk.Canvas(task_scroll_frame,
                                     bg=C['bg'], highlightthickness=0)
        task_sb = ttk.Scrollbar(task_scroll_frame, orient=tk.VERTICAL,
                                command=self.task_canvas.yview)
        self.task_list_frame = tk.Frame(self.task_canvas, bg=C['bg'])

        self.task_canvas.configure(yscrollcommand=task_sb.set)
        task_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.task_canvas_window = self.task_canvas.create_window(
            (0, 0), window=self.task_list_frame, anchor=tk.NW)

        self.task_list_frame.bind('<Configure>',
            lambda e: self.task_canvas.configure(
                scrollregion=self.task_canvas.bbox("all")))
        self.task_canvas.bind('<Configure>',
            lambda e: self.task_canvas.itemconfig(
                self.task_canvas_window, width=e.width))

        tk.Label(task_scroll_frame, bg=C['bg'])  # spacer

        # ── CHAT INPUT ────────────────────────────────────────────────────
        chat_outer = tk.Frame(cp, bg=C['border'], height=1)
        chat_outer.pack(fill=tk.X)
        chat_area = tk.Frame(cp, bg=C['panel'])
        chat_area.pack(fill=tk.X, padx=0, pady=0)

        chat_top = tk.Frame(chat_area, bg=C['panel'])
        chat_top.pack(fill=tk.X, padx=10, pady=(8, 4))

        tk.Label(chat_top, text="Tell me what dataset you need:",
                 font=('Segoe UI', 9, 'bold'),
                 fg=C['fg'], bg=C['panel']).pack(side=tk.LEFT)

        self.agent_mode_var = tk.StringVar(value="agent")
        tk.Label(chat_top, text="Mode:",
                 font=('Segoe UI', 8), fg=C['fg_muted'],
                 bg=C['panel']).pack(side=tk.RIGHT, padx=(0, 4))
        ttk.Combobox(chat_top, textvariable=self.agent_mode_var,
                     values=["agent", "ask"], state="readonly",
                     width=8, font=('Segoe UI', 8)).pack(side=tk.RIGHT)

        input_row = tk.Frame(chat_area, bg=C['panel'])
        input_row.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.unified_input_var = tk.StringVar()
        self.unified_input = tk.Entry(input_row, textvariable=self.unified_input_var,
                                      font=('Segoe UI', 11),
                                      bg=C['input_bg'], fg=C['fg'],
                                      relief='solid', bd=1,
                                      insertbackground=C['fg'])
        self.unified_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.unified_input.insert(0, "e.g. 'PROMISE dataset with cyclomatic complexity'")
        self.unified_input.bind('<FocusIn>',
            lambda e: self.unified_input.delete(0, tk.END)
            if "e.g." in self.unified_input.get() else None)
        self.unified_input.bind('<Return>', lambda e: self.process_chat_input())

        self.send_btn = tk.Button(input_row, text="Send",
                                  font=('Segoe UI', 10, 'bold'),
                                  bg=C['accent'], fg='white',
                                  relief='flat', cursor='hand2',
                                  activebackground=C['accent_hover'],
                                  command=self.process_chat_input)
        self.send_btn.pack(side=tk.LEFT, ipady=4, ipadx=8)


    def build_agent_panel(self):
        """Right panel: agent log (dark) + confirmation area + feedback input"""
        C = self.colors
        rp = self.right_frame

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(rp, bg=C['topbar'])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Agent Log",
                 font=('Segoe UI', 11, 'bold'),
                 fg=C['topbar_fg'], bg=C['topbar']).pack(
            side=tk.LEFT, padx=10, pady=8)

        clr_btn = tk.Button(hdr, text="Clear",
                            font=('Segoe UI', 8),
                            bg='#373e47', fg='#adbac7',
                            relief='flat', cursor='hand2',
                            activebackground='#444c56',
                            command=lambda: (
                                self.message_text.config(state=tk.NORMAL),
                                self.message_text.delete('1.0', tk.END),
                                self.message_text.config(state=tk.DISABLED)
                            ))
        clr_btn.pack(side=tk.RIGHT, padx=6, pady=6)

        # ── Log text area (dark) ──────────────────────────────────────────
        self.message_frame = tk.Frame(rp, bg=C['log_bg'])
        self.message_frame.pack(fill=tk.BOTH, expand=True)

        self.message_text = scrolledtext.ScrolledText(
            self.message_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg=C['log_bg'],
            fg=C['agent_msg'],
            insertbackground='white',
            state=tk.DISABLED,
            borderwidth=0,
            highlightthickness=0,
            padx=8, pady=6,
        )
        self.message_text.pack(fill=tk.BOTH, expand=True)

        # Tag colours (log area is dark)
        self.message_text.tag_configure('system',   foreground=C['info'],
                                        font=('Consolas', 9, 'bold'))
        self.message_text.tag_configure('user',     foreground=C['user_msg'],
                                        font=('Consolas', 9))
        self.message_text.tag_configure('thinking', foreground=C['thinking'],
                                        font=('Consolas', 9, 'italic'))
        self.message_text.tag_configure('action',   foreground=C['action'])
        self.message_text.tag_configure('success',  foreground=C['success_msg'])
        self.message_text.tag_configure('error',    foreground=C['error_msg'])
        self.message_text.tag_configure('question', foreground=C['question'])
        self.message_text.tag_configure('info',     foreground=C['info'])
        self.message_text.tag_configure('bold',     font=('Consolas', 9, 'bold'))
        # Per-type header tags (header line above each message)
        self.message_text.tag_configure('hdr_user',
                                        foreground=C['user_msg'],
                                        font=('Consolas', 9, 'bold'))
        self.message_text.tag_configure('hdr_agent',
                                        foreground=C['agent_msg'],
                                        font=('Consolas', 9, 'bold'))
        self.message_text.tag_configure('hdr_success',
                                        foreground=C['success_msg'],
                                        font=('Consolas', 9, 'bold'))
        self.message_text.tag_configure('hdr_error',
                                        foreground=C['error_msg'],
                                        font=('Consolas', 9, 'bold'))
        self.message_text.tag_configure('hdr_question',
                                        foreground=C['question'],
                                        font=('Consolas', 9, 'bold'))
        self.message_text.tag_configure('hdr_system',
                                        foreground=C['info'],
                                        font=('Consolas', 9, 'bold'))

        # ── Confirmation area (jury checkpoints) ──────────────────────────
        self.confirm_frame = tk.Frame(rp, bg=C['panel'])
        self.confirm_frame.pack(fill=tk.X)

        self.confirm_label = tk.Label(
            self.confirm_frame,
            text="",
            font=('Segoe UI', 9),
            bg=C['panel'], fg=C['fg'],
            wraplength=340, justify=tk.LEFT,
            anchor=tk.W,
        )
        self.confirm_label.pack(fill=tk.X, padx=10, pady=(8, 4))

        confirm_btns = tk.Frame(self.confirm_frame, bg=C['panel'])
        confirm_btns.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.confirm_yes_btn = tk.Button(
            confirm_btns, text="Confirm",
            font=('Segoe UI', 9, 'bold'),
            bg=C['success'], fg='white',
            relief='flat', cursor='hand2', activebackground="#91b79c",
            command=self._on_confirm_yes)
        self.confirm_yes_btn.pack(side=tk.LEFT, padx=(0, 4), ipady=4, ipadx=10)

        self.confirm_no_btn = tk.Button(
            confirm_btns, text="Cancel",
            font=('Segoe UI', 9),
            bg=C['error'], fg='white',
            relief='flat', cursor='hand2', activebackground='#a8001a',
            command=self._on_confirm_no)
        self.confirm_no_btn.pack(side=tk.LEFT, padx=(0, 4), ipady=4, ipadx=10)

        self.confirm_clarify_btn = tk.Button(
            confirm_btns, text="Clarify",
            font=('Segoe UI', 9),
            bg=C['input_bg'], fg=C['fg'],
            relief='solid', bd=1, cursor='hand2',
            activebackground=C['border'],
            command=self._on_confirm_clarify)
        self.confirm_clarify_btn.pack(side=tk.LEFT, ipady=4, ipadx=10)

        # Approval buttons (legacy task-manager compatibility)
        self.approval_frame = self.confirm_frame
        self.approval_text = self.confirm_label
        self.approve_btn = self.confirm_yes_btn
        self.reject_btn  = self.confirm_no_btn
        self.skip_btn    = self.confirm_clarify_btn

        # Hide confirmation area until needed
        self.set_approval_visible(False)

        # ── Feedback / clarification input ────────────────────────────────
        fb_outer = tk.Frame(rp, bg=C['border'], height=1)
        fb_outer.pack(fill=tk.X)

        fb_area = tk.Frame(rp, bg=C['panel'])
        fb_area.pack(fill=tk.X)

        tk.Label(fb_area, text="Feedback / Clarification:",
                 font=('Segoe UI', 8, 'bold'),
                 fg=C['fg_muted'], bg=C['panel']).pack(
            anchor=tk.W, padx=10, pady=(6, 2))

        fb_row = tk.Frame(fb_area, bg=C['panel'])
        fb_row.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.feedback_var = tk.StringVar()
        self.feedback_entry = tk.Entry(fb_row, textvariable=self.feedback_var,
                                       font=('Segoe UI', 10),
                                       bg=C['input_bg'], fg=C['fg'],
                                       relief='solid', bd=1,
                                       insertbackground=C['fg'])
        self.feedback_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.feedback_entry.bind('<Return>', lambda e: self.send_feedback())

        tk.Button(fb_row, text="Send",
                  font=('Segoe UI', 9, 'bold'),
                  bg=C['accent'], fg='white',
                  relief='flat', cursor='hand2',
                  activebackground=C['accent_hover'],
                  command=self.send_feedback).pack(side=tk.LEFT, ipady=3, ipadx=8)

    def toggle_agent_panel(self):
        """Toggle the agent panel visibility"""
        if self.agent_panel_visible:
            self.main_container.forget(self.right_frame)
            self.toggle_btn.config(text="▶ Agent Panel")
            self.agent_panel_visible = False
        else:
            self.main_container.add(self.right_frame, weight=2)
            self.toggle_btn.config(text="◀ Agent Panel")
            self.agent_panel_visible = True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # NEW UI HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def show_benchmark_info(self):
        """Show info about selected benchmark"""
        benchmark = self.benchmark_var.get()
        if benchmark == "None":
            messagebox.showinfo("Benchmark Info", "Select a benchmark from dropdown to see details.")
            return
        
        info = {
            "Defects4J": "Java bugs with buggy/fixed code pairs.\nFormat: Folder structure\nFields: bug_id, project, buggy.java, fixed.java",
            "Bugs.jar": "Large-scale Java bug dataset.\nFormat: JSON\nFields: bug_id, project, files, metrics, commit_hash",
            "PROMISE": "Software defect prediction.\nFormat: CSV (42 columns)\nFields: wmc, dit, noc, cbo, rfc, lcom, ca, ce, npm, lcom3, loc, dam, moa, mfa, cam, ic, cbm, amc, max_cc, avg_cc, defects",
            "CodeXGLUE": "Microsoft code benchmark.\nFormat: JSONL\nFields: code, docstring, func_name, complexity",
            "CodeSearchNet": "Code-to-documentation.\nFormat: JSONL\nFields: code, docstring, language, url, tokens",
            "ManySStuBs4J": "Simple stupid bugs in Java.\nFormat: JSON\nFields: bug_type, buggy_code, fixed_code, project",
            "Sourcerer": "Large-scale code repository.\nFormat: CSV\nFields: file_path, content, language, project, metrics"
        }
        messagebox.showinfo(f"{benchmark} Info", info.get(benchmark, "No info available"))

    def on_repo_focus(self, event):
        """Handle focus on repo entry"""
        if 'Enter' in self.repo_entry.get():
            self.repo_entry.delete(0, tk.END)

