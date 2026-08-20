from nicegui import ui
from main import app, repo_analyser, repo_search, Url, Request
import uvicorn
import httpx

# ---------------------------------------------------------------------------
# Theme: a dark, monospace "terminal / git diff" aesthetic — fitting for a
# tool whose whole job is reading code. Bars stand in for numbers wherever
# possible so magnitude is something you can see, not just read.
# ---------------------------------------------------------------------------

THEME_STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
    --ra-bg: #0f1216;
    --ra-surface: #171b21;
    --ra-surface-2: #1d222a;
    --ra-border: #272c34;
    --ra-text: #e7e9ec;
    --ra-text-dim: #868c97;
    --ra-accent: #4cc38a;
    --ra-accent-dim: rgba(76, 195, 138, 0.14);
    --ra-amber: #e8a33d;
    --ra-amber-dim: rgba(232, 163, 61, 0.14);
    --ra-blue: #5b8dee;
    --ra-blue-dim: rgba(91, 141, 238, 0.14);
    --ra-danger: #f0616d;
}

body {
    background: var(--ra-bg) !important;
    color: var(--ra-text);
    font-family: 'Inter', sans-serif;
    background-image:
        linear-gradient(var(--ra-border) 1px, transparent 1px),
        linear-gradient(90deg, var(--ra-border) 1px, transparent 1px);
    background-size: 42px 42px;
    background-position: -1px -1px;
    background-attachment: fixed;
}

.ra-mono { font-family: 'JetBrains Mono', monospace; }

.ra-cursor {
    display: inline-block;
    width: 0.5em;
    background: var(--ra-accent);
    margin-left: 4px;
    animation: ra-blink 1.1s steps(1) infinite;
}
@keyframes ra-blink { 50% { opacity: 0; } }

.ra-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-size: 0.72rem;
    color: var(--ra-accent);
}

.ra-title {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    letter-spacing: -0.01em;
}

.ra-subtitle { color: var(--ra-text-dim); }

.ra-panel {
    background: var(--ra-surface) !important;
    border: 1px solid var(--ra-border) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    transition: border-color 0.25s ease, transform 0.25s ease;
}
.ra-panel:hover { border-color: #333a45 !important; }

.ra-input .q-field__control {
    background: var(--ra-surface-2) !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace;
}
.ra-input .q-field__native, .ra-input .q-field__prefix { color: var(--ra-text) !important; }
.ra-input .q-field__prefix { color: var(--ra-accent) !important; font-weight: 600; }

.ra-btn {
    background: var(--ra-accent) !important;
    color: #08130d !important;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    letter-spacing: 0.02em;
    border-radius: 8px !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}
.ra-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px -8px rgba(76, 195, 138, 0.55);
}
.ra-btn:active:not(:disabled) { transform: translateY(0px) scale(0.99); }
.ra-btn:disabled { opacity: 0.55 !important; }

.ra-status {
    color: var(--ra-danger) !important;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

.ra-section-head {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 0.8rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--ra-text-dim);
}

.ra-stat-tile {
    background: var(--ra-surface-2);
    border: 1px solid var(--ra-border);
    border-left: 3px solid var(--ra-accent);
    border-radius: 8px;
    padding: 10px 14px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.ra-stat-tile:hover { transform: translateY(-2px); border-color: #333a45; }
.ra-stat-tile.ra-tile-amber { border-left-color: var(--ra-amber); }
.ra-stat-tile.ra-tile-blue { border-left-color: var(--ra-blue); }

.ra-stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--ra-text-dim);
}
.ra-stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 1.3rem;
    color: var(--ra-text);
}

.ra-file-row {
    border-bottom: 1px solid var(--ra-border) !important;
    transition: background 0.15s ease;
    border-radius: 6px;
}
.ra-file-row:hover { background: var(--ra-surface-2); }
.ra-file-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: var(--ra-text);
}
.ra-file-count {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--ra-text-dim);
    min-width: 64px;
    text-align: right;
}
.ra-bar-track {
    background: var(--ra-surface-2);
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
    flex: 1;
}
.ra-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--ra-accent), var(--ra-blue));
    border-radius: 4px;
    width: 0%;
    transition: width 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.ra-reveal {
    opacity: 0;
    animation: ra-fade-up 0.5s ease forwards;
}
@keyframes ra-fade-up {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.ra-repo-card {
    background: var(--ra-surface) !important;
    border: 1px solid var(--ra-border) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.ra-repo-card:hover {
    transform: translateY(-2px);
    border-color: var(--ra-accent) !important;
}

.ra-outline-btn {
    font-family: 'JetBrains Mono', monospace;
    color: var(--ra-accent) !important;
    border-color: var(--ra-accent) !important;
    transition: background 0.15s ease;
}
.ra-outline-btn:hover { background: var(--ra-accent-dim) !important; }
</style>
"""


def apply_theme():
    ui.add_head_html(THEME_STYLE)
    ui.dark_mode().enable()


def stat_tile(label: str, value, variant: str = "") -> None:
    classes = "ra-stat-tile " + variant
    with ui.column().classes(classes).style("gap: 2px;"):
        ui.label(label.replace("_", " ")).classes("ra-stat-label")
        ui.label(str(value)).classes("ra-stat-value")


@ui.page("/analyser")
async def index():
    ui.page_title("GitHub Repository Analyser")
    apply_theme()

    # Left half of the screen
    with ui.column().classes("w-1/2 p-6 mx-auto").style("min-width: 420px;"):
        ui.label("$ repo-analyser").classes("ra-eyebrow")
        with ui.row().classes("items-center").style("gap: 0;"):
            ui.label("Repository Analyser").classes("ra-title text-3xl")
            ui.element("span").classes("ra-cursor").style("height: 1.4rem;")
        ui.label(
            "Paste a GitHub URL and break its codebase down file by file."
        ).classes("ra-subtitle mb-4")

        with ui.row().classes("w-full items-center").style("gap: 0;"):
            repo_url = ui.input(
                label="GitHub repository URL",
                placeholder="https://github.com/user/repository",
            ).classes("w-full ra-input").props('outlined prefix="$"')

        status_row = ui.row().classes("items-center w-full").style("gap: 8px; min-height: 24px;")
        with status_row:
            spinner = ui.spinner(size="1.1rem", color="green").classes("ra-mono")
            spinner.set_visibility(False)
            status = ui.label().classes("ra-status")

        results = ui.column().classes("w-full")

        async def analyse():
            status.set_text("")
            results.clear()

            if not repo_url.value:
                status.set_text("> enter a github repository url")
                return

            analyse_button.disable()
            analyse_button.props("icon=hourglass_top")
            spinner.set_visibility(True)
            status.set_text("analysing repository ...")

            try:
                url = Url(url=repo_url.value.strip())

                sorted_files, total_count, average_count = await repo_analyser(url)

                spinner.set_visibility(False)
                status.set_text("")

                max_lines = max(sorted_files.values()) if sorted_files else 1

                with results:
                    with ui.row().classes("items-baseline ra-reveal").style("gap: 10px;"):
                        ui.label("Repository Analysis").classes("ra-title text-2xl")
                        ui.label(f"{len(sorted_files)} files").classes("ra-mono ra-subtitle")

                    # Totals
                    with ui.card().classes("w-full ra-panel ra-reveal").style("animation-delay: 0.05s;"):
                        ui.label("Totals").classes("ra-section-head mb-2")

                        with ui.grid(columns=2).classes("w-full gap-3"):
                            stat_tile("lines of code", total_count['no_of_lines'])
                            stat_tile("assignments", total_count['assigns'], "ra-tile-amber")
                            stat_tile("if statements", total_count['ifs'], "ra-tile-blue")
                            stat_tile("function definitions", total_count['func_defs'])
                            stat_tile("function calls", total_count['func_calls'], "ra-tile-amber")
                            stat_tile("for loops", total_count['for_loops'], "ra-tile-blue")
                            stat_tile("framework", total_count['framework'])

                    # Averages
                    with ui.card().classes("w-full ra-panel ra-reveal").style("animation-delay: 0.1s;"):
                        ui.label("Averages").classes("ra-section-head mb-2")

                        with ui.grid(columns=2).classes("w-full gap-3"):
                            stat_tile("lines of code", average_count['no_of_lines'])
                            stat_tile("assignments", average_count['assigns'], "ra-tile-amber")
                            stat_tile("if statements", average_count['ifs'], "ra-tile-blue")
                            stat_tile("function definitions", average_count['func_defs'])
                            stat_tile("function calls", average_count['func_calls'], "ra-tile-amber")
                            stat_tile("for loops", average_count['for_loops'], "ra-tile-blue")
                            stat_tile("framework", average_count['framework'])

                    # Files
                    with ui.card().classes("w-full ra-panel ra-reveal").style("animation-delay: 0.15s;"):
                        ui.label("Python Files").classes("ra-section-head mb-3")

                        for i, (file_name, line_count) in enumerate(sorted_files.items()):
                            pct = round((line_count / max_lines) * 100, 1) if max_lines else 0
                            with ui.row().classes(
                                "w-full items-center ra-file-row p-2"
                            ).style(f"gap: 12px;"):
                                ui.label(file_name).classes("ra-file-name").style("min-width: 220px;")
                                with ui.element("div").classes("ra-bar-track"):
                                    bar = ui.element("div").classes("ra-bar-fill")
                                    ui.timer(
                                        0.02 * i,
                                        lambda b=bar, p=pct: b.style(f"width: {p}%;"),
                                        once=True,
                                    )
                                ui.label(f"{line_count} lines").classes("ra-file-count")

            except Exception as e:
                spinner.set_visibility(False)
                status.set_text(f"> error: {e}")

            finally:
                analyse_button.enable()
                analyse_button.props("icon=bolt")

        analyse_button = ui.button(
            "Analyse Repository",
            icon="bolt",
            on_click=analyse,
        ).classes("w-full ra-btn mt-3")


@ui.page('/repo_search')
async def repo_search_page():
    apply_theme()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'http://127.0.0.1:8000/repo_search'
        )

    response.raise_for_status()
    repos = response.json()

    with ui.column().classes('w-full max-w-4xl mx-auto p-8 gap-4'):
        ui.label("$ repo-analyser --list").classes("ra-eyebrow")
        ui.label('Repository Search').classes('ra-title text-3xl')

        ui.label(
            'Select a repository to view its analysis.'
        ).classes('ra-subtitle mb-4')

        for i, repo in enumerate(repos):
            with ui.card().classes(
                'w-full ra-repo-card ra-reveal p-1'
            ).style(f"animation-delay: {0.04 * i}s;"):
                with ui.row().classes(
                    'w-full items-center justify-between p-2'
                ):
                    with ui.row().classes("items-center").style("gap: 10px;"):
                        ui.icon("folder_open").classes("text-2xl").style("color: var(--ra-accent);")
                        ui.label(repo['name']).classes('ra-mono text-lg font-semibold')

                    ui.button(
                        'View Analysis',
                        icon="arrow_forward",
                        on_click=lambda repo_id=repo['repo_id']:
                            ui.navigate.to(
                                f'/get_analysis/{repo_id}'
                            )
                    ).props('outline').classes('ra-outline-btn')


@ui.page('/get_analysis/{repo_id}')
async def analysis_page(repo_id: int):
    apply_theme()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'http://127.0.0.1:8000/get_analysis/{repo_id}'
        )

    response.raise_for_status()
    data = response.json()

    with ui.column().classes('w-full max-w-6xl mx-auto p-8 gap-6'):

        # Header
        ui.label("$ repo-analyser --show").classes("ra-eyebrow")
        ui.label(data['name']).classes('ra-title text-3xl')

        ui.label('Repository Analysis').classes('ra-subtitle text-lg mb-2')

        # Totals / averages
        with ui.row().classes('w-full gap-4'):

            with ui.card().classes('flex-1 ra-panel ra-reveal'):
                ui.label('Totals').classes('ra-section-head mb-2')

                with ui.grid(columns=2).classes("w-full gap-3"):
                    variants = ["", "ra-tile-amber", "ra-tile-blue"]
                    for i, (key, value) in enumerate(data['totals'].items()):
                        stat_tile(key, value, variants[i % 3])

            with ui.card().classes('flex-1 ra-panel ra-reveal').style("animation-delay: 0.05s;"):
                ui.label('Averages').classes('ra-section-head mb-2')

                with ui.grid(columns=2).classes("w-full gap-3"):
                    variants = ["", "ra-tile-amber", "ra-tile-blue"]
                    for i, (key, value) in enumerate(data['averages'].items()):
                        stat_tile(key, value, variants[i % 3])

        # Files
        with ui.card().classes('w-full ra-panel ra-reveal').style("animation-delay: 0.1s;"):
            ui.label('Code Files').classes('ra-section-head mb-3')

            files = data['files']
            max_lines = max((f['linecount'] for f in files), default=1) or 1

            for i, f in enumerate(files):
                pct = round((f['linecount'] / max_lines) * 100, 1)
                with ui.row().classes('w-full items-center ra-file-row p-2').style("gap: 12px;"):
                    ui.label(f['file_name']).classes('ra-file-name').style("min-width: 220px;")
                    with ui.element("div").classes("ra-bar-track"):
                        bar = ui.element("div").classes("ra-bar-fill")
                        ui.timer(
                            0.02 * i,
                            lambda b=bar, p=pct: b.style(f"width: {p}%;"),
                            once=True,
                        )
                    ui.label(f"{f['linecount']} lines").classes('ra-file-count')

ui.run_with(
    app,
    title="GitHub Repository Analyser",
    mount_path="/frontend"
)


if __name__ == "__main__":
    uvicorn.run(
        "frontend:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )