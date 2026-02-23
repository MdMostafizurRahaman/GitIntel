# -*- mode: python ; coding: utf-8 -*-

import os

dataset_dir = os.path.abspath(os.path.join(os.path.dirname(SPEC), '..'))
gui_dir = os.path.dirname(SPEC)

a = Analysis(
    ['main.py'],
    pathex=[dataset_dir, gui_dir],
    binaries=[],
    datas=[],
    hiddenimports=[
        # GUI modules
        'dataset_helpers', 'gui_types', 'gui_styles', 'gui_layout',
        'gui_messages', 'gui_repo', 'gui_plan', 'gui_tasks', 'gui_dataset',
        'gui_jury_tab', 'gui_formula_tab', 'gui_chat', 'gui_orchestrator_tab',
        # Dataset-level modules
        'metrics_catalog', 'integrated_jury_system', 'dataset_generator',
        'batch_query_runner',
        # dataset_generators package
        'dataset_generators', 'dataset_generators.metrics_helper',
        'dataset_generators.defects4j_generator', 'dataset_generators.bugsjar_generator',
        'dataset_generators.manystubs4j_generator', 'dataset_generators.promise_generator',
        'dataset_generators.codesearchnet_generator', 'dataset_generators.codexglue_generator',
        'dataset_generators.sourcerer_generator', 'dataset_generators.run_all_generators',
        # metrics_generators package
        'metrics_generators', 'metrics_generators.master_metrics_generator',
        'metrics_generators.shared_utils',
        # extractors package
        'extractors', 'extractors.base_extractor', 'extractors.code_extractors',
        'extractors.java_extractors', 'extractors.metrics_extractors', 'extractors.factory',
        # config package
        'config', 'config.config',
        # boto3 / botocore hidden imports
        'boto3', 'botocore', 'botocore.loaders', 'botocore.handlers',
        'botocore.parsers', 'botocore.serialize', 'botocore.endpoint',
        'botocore.regions', 'botocore.credentials', 'botocore.configprovider',
        's3transfer', 'jmespath',
        # google-generativeai hidden imports
        'google.generativeai', 'google.ai.generativelanguage',
        'google.api_core', 'google.auth',
        'grpc', 'grpc._channel',
        # GitPython
        'git', 'gitdb', 'smmap',
        # lizard
        'lizard',
        # other stdlib/common
        'queue', 'threading', 'subprocess', 'json', 'csv',
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
        'tkinter.scrolledtext',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GitIntel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
