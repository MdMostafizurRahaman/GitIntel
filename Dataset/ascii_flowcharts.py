"""
GitIntel ASCII Flowchart Diagrams
Visual representation of all scenario workflows
"""

MAIN_WORKFLOW = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                      GITINTEL MAIN WORKFLOW                              ║
║                  From Request to Research Dataset                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

                              START
                                │
                                ▼
                      ┌─────────────────────┐
                      │  User Input         │
                      │  (Natural Language) │
                      └────────┬────────────┘
                               │
                               ▼
                      ┌─────────────────────┐
                      │ LLM Parse Input     │
                      │ Extract Components  │
                      └────────┬────────────┘
                               │
                               ▼
                      ┌─────────────────────┐
                      │ Show Summary        │
                      │ Ask Confirmation    │
                      └────────┬────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                  YES│                    │NO/MODIFY
                    │                     │
                    ▼                     ▼
            ┌──────────────┐      ┌──────────────────┐
            │ PROCEED      │      │ Clarify/Modify   │
            │              │      │ Update Config    │
            └──────┬───────┘      └────────┬─────────┘
                   │                       │
                   │                   ┌───┴──────────┐
                   │                   │              │
                   │                   └──────────────┘
                   │                        ▲
                   │                        │
                   └────────────────────────┘
                            │
                            ▼
                   ┌──────────────────────┐
                   │ Repository Analysis  │
                   │ Extract Metrics      │
                   │ 64+ Metrics          │
                   └──────────┬───────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
                    ▼                    ▼
            ┌──────────────────┐  ┌──────────────────┐
            │ Pre-built         │  │ Custom Metric?   │
            │ Metrics           │  │                  │
            │ (64+)             │  └────────┬─────────┘
            └────────┬─────────┘           │
                     │            ┌────────▼─────────┐
                     │            │                  │
                     │            ▼                  ▼
                     │       ┌────────────┐   ┌────────────────┐
                     │       │ LLM Gen    │   │ Use Preset     │
                     │       │ Code       │   │ Metrics        │
                     │       └─────┬──────┘   └────────┬───────┘
                     │             │                   │
                     │             ▼                   │
                     │       ┌────────────────────┐    │
                     │       │ Multi-LLM Jury     │    │
                     │       │ Validation (3+)    │    │
                     │       │ • Judge 1          │    │
                     │       │ • Judge 2          │    │
                     │       │ • Judge 3          │    │
                     │       └──────┬─────────────┘    │
                     │              │                  │
                     │         ┌────▴────┐             │
                     │         │          │            │
                     │      APPROVED    REJECT         │
                     │         │          │            │
                     │         │          ▼            │
                     │         │     ┌─────────────┐   │
                     │         │     │Refine Code  │   │
                     │         │     │ (Max 5 iter)│   │
                     │         │     └──────┬──────┘   │
                     │         │            │          │
                     │         │        ┌───┴────┐     │
                     │         │        │        │     │
                     │         │     APPROVED FAIL     │
                     │         │        │        │     │
                     │         │        ▼        ▼     │
                     │         │              ┌──────┐ │
                     │         │              │Human │ │
                     │         │              │Review│ │
                     │         │              └──────┘ │
                     │         │                       │
                     └─────────┴───────────────────────┘
                               │
                               ▼
                      ┌──────────────────────┐
                      │ Extract Features     │
                      │ from Repository      │
                      │ • Commits            │
                      │ • Files              │
                      │ • Code Metrics       │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │ Align with           │
                      │ Benchmarks (7)       │
                      │ • Defects4J          │
                      │ • Bugs.jar           │
                      │ • PROMISE            │
                      │ ... (7 total)        │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │ Compute All          │
                      │ Requested Metrics    │
                      │ Pre-built + Custom   │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │ Process Data         │
                      │ • Normalize          │
                      │ • Deduplicate        │
                      │ • Aggregate          │
                      │ • Validate           │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │ Export Datasets      │
                      │ • CSV                │
                      │ • JSON               │
                      │ • Excel              │
                      │ • Metadata           │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │ Generate Reports     │
                      │ • Quality metrics    │
                      │ • Statistics         │
                      │ • Visualizations     │
                      └──────────┬───────────┘
                                 │
                                 ▼
                            ✅ SUCCESS
                            DATASETS READY
"""

ASK_MODE_FLOW = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                    ASK MODE CONFIRMATION FLOW                             ║
║                  Interactive Step-by-Step Workflow                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

User Input → Parse → Summary → User Decides → Execute

                    [1] USER ENTERS REQUEST
                            │
                            ▼
                    ┌──────────────────┐
                    │ [2] AI PARSES    │
                    │ Input            │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │ [3] SYSTEM SHOWS SUMMARY │
                    │ "I understand you want:  │
                    │  • Repository: X         │
                    │  • Dataset: Defects4J    │
                    │  • Metrics: Y            │
                    │  • Format: CSV"          │
                    └────────┬─────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
              YES│           NO│       MODIFY│
                │            │            │
                ▼            ▼            ▼
            ┌────────┐  ┌─────────┐  ┌──────────────┐
            │ EXECUTE│  │ CLARIFY │  │ SHOW OPTIONS │
            └─┬──────┘  └────┬────┘  │ User picks   │
              │              │       │ alternative  │
              │          [REPHRASE]  └─────┬────────┘
              │              │              │
              │         [REPARSE]          │
              │              │              │
              │              │      [CONFIG UPDATE]
              │              │              │
              │              └──────┬───────┘
              │                     │
              │          [SHOW SUMMARY AGAIN]
              │                     │
              └─────────────────────┘
                        │
                        ▼
                [4] ANALYSIS BEGINS
                Progress shown in real-time
                        │
                ┌───────┴────────┐
                │                │
         [CONTINUE]      [PAUSE/CANCEL]
                │                │
                ▼                ▼
            Execute      Save checkpoint
                │                │
                │            Resume later
                │
                ▼
        [5] RESULTS GENERATED
        Download & Review
"""

AGENT_MODE_FLOW = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                  AUTONOMOUS AGENT MODE FLOW                               ║
║              Minimal User Interaction, Smart Automation                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

User Input → Agent Analyzes → Auto-Execute → Notify

                    [1] USER INPUT
                            │
                            ▼
                    ┌──────────────────┐
                    │ [2] AGENT        │
                    │ ANALYSIS         │
                    └────────┬─────────┘
                             │
                    ┌────────▼────────┐
                    │ Check:          │
                    │ • Clarity       │
                    │ • Feasibility   │
                    │ • Resources     │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
              ALL OK│  AMBIGUITY?│   BLOCKED?│
                │            │            │
                ▼            ▼            ▼
            ┌──────┐    ┌─────────┐  ┌────────┐
            │GO     │   │ ASK FOR │  │ REPORT │
            │AUTONOMOUS│ CLARIFY  │  │ ERROR  │
            └──┬───┘   └────┬────┘  └───┬────┘
               │            │          │
               │      [GET USER]       │
               │       [RESPONSE]      │
               │            │          │
               │       [CONTINUE]      │
               │            │          │
               │            ▼          │
               │        ┌──────┐      │
               │        │ GO   │      │
               │        │EXEC  │      │
               │        └──┬───┘      │
               │           │         │
               └───┬───────┘         │
                   │                │
                   ▼                ▼
                [3] EXECUTION        User takes action
                No more prompts      or retries
                Progress updates
                        │
                        ▼
                [4] COMPLETION
                Auto-save results
                Notify user
                        │
                        ▼
                ✅ READY FOR USE
"""

JURY_SYSTEM_FLOW = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                    LLM JURY VALIDATION SYSTEM                             ║
║              Multi-Judge Code Review & Approval Process                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

Metric Formula → Code Gen → 3 Judges → Validation → Integration

                [1] METRIC FORMULA
                        │
                        ▼
                ┌──────────────────┐
                │ [2] LLM GENERATOR│
                │ Creates Code (v1)│
                └────────┬─────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    [JUDGE 1]      [JUDGE 2]        [JUDGE 3]
    
    [A] Generate    [A] Generate    [A] Generate
        tests           tests           tests
        
    [B] Execute     [B] Execute     [B] Execute
        tests           tests           tests
        
    [C] Review      [C] Review      [C] Review
        logic           logic           logic
        
    [D] VOTE        [D] VOTE        [D] VOTE
        │               │               │
        ▼               ▼               ▼
    ┌──────┐       ┌──────┐       ┌──────┐
    │APPRV │       │APPRV │       │REJECT│
    └──┬───┘       └──┬───┘       └───┬──┘
       │               │               │
       └───────────┬───┴────────┬──────┘
                   │
           ┌───────▼────────┐
           │ VOTING RESULT  │
           │ 2/3 APPROVED   │
           │ → ACCEPT       │
           └───────┬────────┘
                   │
        ┌──────────▼──────────┐
        │ CODE INTEGRATED     │
        │ into Pipeline       │
        │ READY FOR USE       │
        └─────────┬──────────┘
                  │
        IF 2+ judges reject:
        ├─ Collect feedback
        ├─ Refine code (v2)
        ├─ Re-validate
        ├─ Max 5 iterations
        ├─ After 5 fails
        └─ → HUMAN REVIEW
"""

MULTI_BENCHMARK_FLOW = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                  MULTI-BENCHMARK PARALLEL PROCESSING                      ║
║        Analyze Repository Against 7 Different Research Benchmarks        ║
╚═══════════════════════════════════════════════════════════════════════════╝

Single Repository
        │
        ├──────────────────────────────────────┐
        │                                      │
        ▼                                      ▼
    ┌────────────┐                    Multiple Benchmarks
    │ REPOSITORY │                    (run in parallel)
    │ Analysis   │
    └────────────┘
        │
        ├──► [Defects4J]  ──► 245 pairs
        ├──► [Bugs.jar]   ──► 180 instances
        ├──► [PROMISE]    ──► 1250 records
        ├──► [CodeXGLUE]  ──► metrics
        ├──► [CodeSearch] ──► code-doc pairs
        ├──► [ManySStuBs] ──► multi-domain bugs
        └──► [Sourcerer]  ──► large-scale data
        
        All processes run SIMULTANEOUSLY
        
        ┌────────────┬────────────┬────────────┐
        │            │            │            │
        ▼            ▼            ▼            ▼
    [Defects4J]  [Bugs.jar]  [PROMISE]   [Others]
    Extract      Extract      Extract     Extract
    Transform    Transform    Transform   Transform
    Align        Align        Align       Align
        │            │            │            │
        └────────────┼────────────┼────────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ MERGE RESULTS    │
            │ Cross-validate   │
            │ Correlation      │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ UNIFIED DATASET  │
            │ Quality Report   │
            └──────────────────┘
"""

LARGE_REPO_OPTIMIZATION = """
╔═══════════════════════════════════════════════════════════════════════════╗
║              LARGE REPOSITORY ADAPTIVE OPTIMIZATION                       ║
║           Intelligent Resource Management for 50GB+ Repos                ║
╚═══════════════════════════════════════════════════════════════════════════╝

Large Repository (50,000+ commits, 10GB+)
            │
            ▼
    System Health Check
    ├─ Memory: 4 GB
    ├─ Disk: 50 GB
    ├─ Commits: 50,000
    └─ Projected time: 8 hours (normal)
            │
            ▼
    Optimization Strategy
    ┌───────────────────────────────┐
    │ MEMORY: Streaming              │
    │ Process 100 commits at a time  │
    │ Peak usage: 1.2 GB             │
    │ (instead of 8 GB)              │
    └───────────────────────────────┘
    ┌───────────────────────────────┐
    │ DISK: Checkpointing            │
    │ Save progress every 1000       │
    │ commits - Can resume           │
    └───────────────────────────────┘
    ┌───────────────────────────────┐
    │ CPU: Parallelization           │
    │ Use 4 available cores          │
    │ Parallel batch processing      │
    └───────────────────────────────┘
    ┌───────────────────────────────┐
    │ TIME: Result                   │
    │ 2.5 hours (3.2x faster)        │
    └───────────────────────────────┘
            │
            ▼
    [BATCH 1] [BATCH 2] [BATCH 3] ...
     100c      100c      100c
     ~5min     ~5min     ~5min
            │
            ▼
    Checkpoint saved
    Resume possible
            │
            ▼
    [CONTINUE WITH NEXT BATCH]
            │
            ▼
    [MERGE & AGGREGATE]
            │
            ▼
    ✅ COMPLETE (2.5 hours total)
    ✅ 85% memory saved
    ✅ 3.2x time improvement
    ✅ Can resume if interrupted
"""

def print_all_diagrams():
    """Print all ASCII diagrams"""
    diagrams = [
        ("MAIN WORKFLOW", MAIN_WORKFLOW),
        ("ASK MODE FLOW", ASK_MODE_FLOW),
        ("AGENT MODE FLOW", AGENT_MODE_FLOW),
        ("JURY SYSTEM FLOW", JURY_SYSTEM_FLOW),
        ("MULTI-BENCHMARK FLOW", MULTI_BENCHMARK_FLOW),
        ("LARGE REPO OPTIMIZATION", LARGE_REPO_OPTIMIZATION)
    ]
    
    for title, diagram in diagrams:
        print(diagram)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    print_all_diagrams()
