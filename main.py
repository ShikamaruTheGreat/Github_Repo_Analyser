from fastapi import FastAPI, Request, Response, HTTPException, Depends
import uvicorn
import ast
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel
import shutil
from itertools import repeat
import statistics
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, select, ForeignKey, update, delete, insert
from dotenv import load_dotenv
import os
import re

load_dotenv("secrecy.env")
app = FastAPI(title="Github Repository Analyser")

engine = create_engine(os.environ.get("DBURL"))
meta = MetaData()

repositories = Table(
    "repositories",
    meta,
    Column("repo_id", Integer, primary_key=True),
    Column("name", String, nullable=False)
)

code_files = Table(
    "code_files",
    meta,
    Column("file_id", Integer, primary_key=True),
    Column("repo_id", Integer, ForeignKey("repositories.repo_id")),
    Column("file_name", String, nullable=False),
    Column("linecount", Integer)
)

totals = Table(
    "totals",
    meta,
    Column("totals_id", Integer, primary_key=True),
    Column("repo_id", Integer, ForeignKey("repositories.repo_id")),
    Column("assignments", Integer),
    Column("if_statements", Integer),
    Column("function_definitions", Integer),
    Column("function_calls", Integer),
    Column("for_loops", Integer),
    Column("framework", String),
    Column("linecount", Integer)
)

averages = Table(
    "averages",
    meta,
    Column("averages_id", Integer, primary_key=True),
    Column("repo_id", Integer, ForeignKey("repositories.repo_id")),
    Column("assignments", Integer),
    Column("if_statements", Integer),
    Column("function_definitions", Integer),
    Column("function_calls", Integer),
    Column("for_loops", Integer),
    Column("framework", String),
    Column("linecount", Integer)
)

meta.create_all(engine)

class PyAnalyser(ast.NodeVisitor):
    def __init__(self):
        self.assignments = 0
        self.if_statements = 0
        self.function_defs = 0
        self.function_calls = 0
        self.for_loops = 0

        self.imports = []
        self.framework = "other"
    def visit_Assign(self, node):
        self.assignments += 1
        self.generic_visit(node)
    def visit_If(self, node):
        self.if_statements += 1
        self.generic_visit(node)
    def visit_FunctionDef(self, node):
        self.function_defs += 1
        self.generic_visit(node)
    def visit_Call(self, node):
        self.function_calls += 1
        self.generic_visit(node)
    def visit_For(self, node):
        self.for_loops += 1
        self.generic_visit(node)

    def visit_Import(self, node):
        for mod in node.names:
            self.imports.append(mod.name)
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
    def framework_check(self):
        frameworks = ["django", "flask", "fastapi", "starlette", "tornado", "pyramid", "bottle",
                      "falcon", "sanic", "aiohttp", "quart", "cherrypy", "twisted", "litestar"]
        if "fastapi" in self.imports and "starlette" in self.imports:
            self.framework = "fastapi"
        for fw in frameworks:
            if fw in self.imports:
                self.framework = fw

    def get_vals(self):
        return [self.assignments, self.if_statements, self.function_defs, self.function_calls, self.for_loops,
                 self.framework]

def logic_counter(file_name: str, dir_name: str):
    if file_name.endswith(".py"):
        result = subprocess.run(["wc", "-l", file_name], capture_output=True, text=True,
                                cwd=f"working_dir/{dir_name}")
        proxy = result.stdout[5:9].strip()
        no_of_lines = int(proxy)

        with open(f"working_dir/{dir_name}/{file_name}", "r") as code:
            code = code.read()
            tree = ast.parse(code)
        analyser = PyAnalyser()
        analyser.visit(tree)
        analyser.framework_check()
        data = analyser.get_vals()
        data.append(no_of_lines)
        return data
    else:
        return None # ignore the Nones in the repo_analyser function


def repo_flattener(dir_name: str):
    sub_dirs = []
    is_flat = True
    path = Path(f"working_dir/{dir_name}")
    for item in path.iterdir():
        if item.is_dir():
            sub_dirs.append(item)
            is_flat = False
    if is_flat:
        return True
    else:
        for subdir in sub_dirs:
            sub = Path(subdir)
            for file in sub.iterdir():
                shutil.move(file, path)
            sub.rmdir()
        return repo_flattener(dir_name)

class Url(BaseModel):
    url: str

@app.post("/repo_analyser")
async def repo_analyser(url: Url):
    url_pattern = (r"^https://github\.com/[A-Za-z0-9](?:[A-Za-z0-9-]"
                   r"{0,38})/[A-Za-z0-9](?:[A-Za-z0-9._-]{0,99})/?$")

    if re.fullmatch(url_pattern, url.url) == False:
        raise HTTPException(400, "this ain't a github url you dog")

    subprocess.run(["gh", "repo", "clone", url.url], cwd="working_dir")
    url_list = url.url.split("/")
    dir_name = url_list[-1]

    shutil.rmtree(f"working_dir/{dir_name}/.git") # .git folder is really meddlesome
    repo_flattener(dir_name)

    path = Path(f"working_dir/{dir_name}")
    file_names = [f.name for f in path.iterdir() if f.is_file()]

    with ThreadPoolExecutor(max_workers=4) as executor:
        proxy = executor.map(logic_counter, file_names, repeat(dir_name))

    results = [real for real in proxy if real is not None]
    if len(results) == 0:
        raise HTTPException(400, "sorry, there were no python files in this repository")

    file_map = {}

    index = 0
    for name in file_names:
        if name.endswith(".py"):
            file_map[name] = results[index]
            index += 1

    sorted_on_linecount = {}
    for file, linecount in sorted(file_map.items(), key=lambda data: data[1][6], reverse=True):
        sorted_on_linecount[file] = linecount[6]
    # this loop does this:
    # 1. file_map.items(): this method makes every key-value pair in file map a tuple i.e smth like
    #    ("naruto.py", [4, 76, 22, ...])
    # 2. the sorted function over it, sorts it
    # 3. the key kwarg in sorted accepts a lambda, which is used to pass in each tuple into it
    #    and for each of them, it returns the 2nd element i.e a list, and the 7th element within that list
    #    then that end value is assigned to the key kwarg, which the sorting of each tuple is based on
    # 4. there's another kwarg in sorted, reverse, which when true sorts in descending order
    # 5. then a loop is iterated over the sorted list of tuples, taking the first(file) and second(linecount)
    #    elements in each tuple and assigning the first as the key and the second as the value in a new dict

    total_count = {
        "assigns": 0,
        "ifs": 0,
        "func_defs": 0,
        "func_calls": 0,
        "for_loops": 0,
        "framework": "",
        "no_of_lines": 0
    }
    average_count = {
        "assigns": [],
        "ifs": [],
        "func_defs": [],
        "func_calls": [],
        "for_loops": [],
        "framework": "",
        "no_of_lines": []
    }

    index = 0
    for attr in total_count:
        for key in file_map:
            if index == 5:
                total_count[attr] = file_map[key][index]
            else:
                total_count[attr] += file_map[key][index]
        index += 1

    avg_index = 0
    for attr in average_count:
        for key in file_map:
            if avg_index == 5:
                average_count[attr] = file_map[key][avg_index]
            else:
                average_count[attr].append(file_map[key][avg_index])
        avg_index += 1
    for attr in average_count:
        if attr == "framework":
            continue
        average_count[attr] = round(statistics.mean(average_count[attr]))

    subprocess.run(["rm", "-r", dir_name], cwd="working_dir")

    await insert_repo_to_db(sorted_on_linecount, total_count, average_count, dir_name)
    return sorted_on_linecount, total_count, average_count

async def insert_repo_to_db(sorted_on_linecount: dict, total_count: dict, average_count: dict, dir_name: str):
    with engine.begin() as conn:
        insert_repo = repositories.insert().values(name=dir_name)
        result = conn.execute(insert_repo)
        repo_id = result.inserted_primary_key[0]

        for file_name, linecount in sorted_on_linecount.items():
            insert_file = code_files.insert().values(repo_id=repo_id, file_name=file_name, linecount=linecount)
            conn.execute(insert_file)

        insert_totals = (totals.insert().values(
            repo_id=repo_id, assignments=total_count["assigns"], if_statements=total_count["ifs"],
            function_definitions=total_count["func_defs"], function_calls=total_count["func_calls"],
            for_loops=total_count["for_loops"], framework=total_count["framework"],
            linecount=total_count["no_of_lines"]
        ))
        conn.execute(insert_totals)

        insert_averages = (averages.insert().values(
            repo_id=repo_id, assignments=average_count["assigns"], if_statements=average_count["ifs"],
            function_definitions=average_count["func_defs"], function_calls=average_count["func_calls"],
            for_loops=average_count["for_loops"], framework=average_count["framework"],
            linecount=average_count["no_of_lines"]
        ))
        conn.execute(insert_averages)
    return "stuff inserted"


@app.get("/get_analysis/{repo_id}")
async def get_analysis(repo_id: int):
    with engine.begin() as conn:
        select_code_files = (select(code_files.c.file_name, code_files.c.linecount)
                             .where(code_files.c.repo_id == repo_id))
        proxy_files = conn.execute(select_code_files)
        sorted_files = [dict(row) for row in proxy_files.mappings()]

        select_totals = select(totals).where(totals.c.repo_id == repo_id)
        result = conn.execute(select_totals).mappings().first()
        if result:
            total_count = dict(result)

        select_averages = select(averages).where(averages.c.repo_id == repo_id)
        a_result = conn.execute(select_averages).mappings().first()
        if a_result:
            average_count = dict(a_result)

        select_dir = select(repositories.c.name).where(repositories.c.repo_id == repo_id)
        dir_name = conn.scalar(select_dir)

        return {"name": dir_name, "files": sorted_files, "totals": total_count, "averages": average_count}

@app.get("/repo_search")
async def repo_search(request: Request):
    with engine.begin() as conn:
        select_repos = select(repositories.c.repo_id, repositories.c.name)
        repo_list = conn.execute(select_repos).fetchall()

    return_thing = []
    for r_id, name in repo_list:
        return_thing.append({
            "repo_id": r_id,
            "name": name
        })
    return return_thing

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)