
from libcfg.Instruction import *
from typing import Callable, Dict, Set
from os import mkdir
from html import escape
import os
from graphviz import Digraph

def make_graph(binary, disassembler:Callable[[bytes, int], BaseInstruction], entry_points):
    graph = {}
    dfs_stack = []
    func_starts = set(entry_points)
    
    for ip in entry_points:
        dfs_stack.append(ip)
        while len(dfs_stack):
            ip = dfs_stack.pop()
            if ip in graph:
                continue
            instr = disassembler(binary, ip)
            if type(instr) not in {Instruction, Call, Jump, CondJump, Ret}:
                raise TypeError("disassembler must retutn one of Instruction, Call, Jump, CondJump, Ret")
            if type(instr) == Call:
                func_starts.add(instr.target)
                dfs_stack.append(instr.target)
            graph[ip] = instr
            for nx in instr.nextis():
                if nx not in graph:
                    dfs_stack.append(nx)
    return graph, func_starts

class UFDS:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        self.num_cc = 0
    
    def find(self, x):
        if x not in self.rank:
            self.rank[x] = 0
        if x not in self.parent or self.parent[x] == -1:
            self.parent[x] = -1
            self.num_cc += 1
            return x
        p = self.find(self.parent[x])
        self.parent[x] = p
        return p

    def union(self, a, b):
        a = self.find(a)
        b = self.find(b)
        if a == b:
            return
        self.num_cc -= 1
        if self.rank[a] > self.rank[b]:
            b, a = a, b
        self.parent[a] = b
        if self.rank[a] == self.rank[b]:
            self.rank[b] += 1


def extract_components(graph:Dict[int, BaseInstruction]) -> UFDS:
    dsu = UFDS()
    for ip, instr in graph.items():
        for x in instr.nextis():
            dsu.union(ip, x)
    return dsu

def create_xrefs(graph: Dict[int, BaseInstruction], func_entries: Set[int], dsu: UFDS, cc_to_funcs):
    xrefs = {entry: set() for entry in func_entries}
    for ip, instr in graph.items():
        if type(instr) != Call or instr.target not in xrefs:
            continue
        caller_cc = dsu.find(ip)
        xrefs[instr.target].update(cc_to_funcs.get(caller_cc, set()))
    return xrefs

def create_blocks(graph: Dict[int, BaseInstruction], entry_pts: Set[int], func_to_filename):
    block_starts = entry_pts.copy()
    func_entries = entry_pts.copy()
    for instr in graph.values():
        if type(instr) == Jump:
            block_starts.add(instr.target)
        if type(instr) == Call:
            func_entries.add(instr.target)
            block_starts.add(instr.target)
        if type(instr) == CondJump:
            block_starts.add(instr.cond_false)
            block_starts.add(instr.cond_true)
    blocks = {}
    for entry in block_starts:
        blocks[entry] = {"type":"block", "name":f"loc_{entry:x}"}
        ptr = entry
        block_text = ""
        while type(graph[ptr]) in {Instruction, Call} and graph[ptr].nexti not in block_starts:
            if type(graph[ptr]) == Call:
                instr = graph[ptr]
                filename = f'{func_to_filename[instr.target]}.html'
                block_text += f'<TR><TD ALIGN="LEFT"><FONT COLOR="gray">0x{ptr:06x}</FONT></TD><TD ALIGN="LEFT" HREF="{filename}" TARGET="_top" TOOLTIP="Open {filename}"><FONT COLOR="blue">{escape(instr.s)} '+ \
                        f'sub_{instr.target:x}</FONT></TD></TR>'
            else:
                block_text += f'<TR><TD ALIGN="LEFT"><FONT COLOR="gray">0x{ptr:06x}</FONT></TD><TD ALIGN="LEFT">{escape(graph[ptr].s)}</TD></TR>'
            ptr = graph[ptr].nexti
        block_text += f'<TR><TD ALIGN="LEFT"><FONT COLOR="gray">0x{ptr:06x}</FONT></TD><TD ALIGN="LEFT">{escape(graph[ptr].s)}</TD></TR>'
        blocks[entry]["end"] = ptr
        blocks[entry]["arrows"] = graph[ptr].arrs()
        blocks[entry]["text"] = f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">{block_text}</TABLE>>'
    return blocks

def render_html(name, directory, callers, func_to_filename):
    xref_links = ""
    if callers:
        for caller in sorted(callers):
            filename = f"{func_to_filename[caller]}.html"
            xref_links += f'<a href="{escape(filename)}">sub_{caller:x}</a>\n'
    else:
        xref_links = '<span class="empty">none</span>'

    function_links = ""
    for func, filename_base in sorted(func_to_filename.items(), key=lambda item: item[1]):
        filename = f"{filename_base}.html"
        function_links += f'<a href="{escape(filename)}">sub_{func:x}</a>\n'

    html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(name)}</title>
  <style>
    body {{
      margin: 0;
      height: 100vh;
      display: grid;
      grid-template-columns: 220px 1fr;
      font-family: monospace;
      color: #0f172a;
      background: white;
    }}
    aside {{
      border-right: 1px solid #334155;
      background: #f8fafc;
      padding: 12px;
      overflow: auto;
    }}
    main {{
      overflow: auto;
      padding: 12px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 14px;
    }}
    h1.section {{
      margin-top: 24px;
    }}
    aside a {{
      display: block;
      margin-bottom: 6px;
      color: #1d4ed8;
      text-decoration: none;
    }}
    aside a:hover {{
      text-decoration: underline;
    }}
    .empty {{
      color: #64748b;
    }}
    object {{
      display: block;
      width: auto;
      height: auto;
      border: 0;
    }}
  </style>
</head>
<body>
  <aside>
    <h1>xrefs</h1>
    {xref_links}
    <h1 class="section">functions</h1>
    {function_links}
  </aside>
  <main>
    <object data="{escape(name)}.svg" type="image/svg+xml"></object>
  </main>
</body>
</html>
'''
    with open(os.path.join(directory, f"{name}.html"), "w", encoding="utf-8") as f:
        f.write(html)

def render_svg(blocks, cc, entries, name, directory, xrefs, func_to_filename):
    dot = Digraph(comment=name)
    dot.attr("graph", splines="ortho")
    dot.attr('node', shape='box', fontname='monospace')

    callers = set()
    for entry in entries:
        callers.update(xrefs.get(entry, set()))

    for x in blocks:
        block = blocks[x]
        dot.node(f"loc_{x:x}", block["text"])
    for x in blocks:
        block = blocks[x]
        for arr in block["arrows"]:
            dot.edge(block["name"], f'loc_{arr["to"]:x}', color=arr["color"])
    dot.render(os.path.join(directory, name), format="svg")
    render_html(name, directory, callers, func_to_filename)

def CFG(binary, disassembler: Callable[[bytes, int], BaseInstruction], entry_points :List[int], directory:str="CFG"):
    graph, func_entries = make_graph(binary, disassembler, entry_points)
    dsu : UFDS = extract_components(graph)

    func_to_cc = {x : dsu.find(x) for x in func_entries}
    cc_to_funcs = {}
    for f, cc in func_to_cc.items():
        if cc not in cc_to_funcs:
            cc_to_funcs[cc] = set()
        cc_to_funcs[cc].add(f)

    multifunc_count = 0
    cc_to_filename = {}
    for cc, funcs in cc_to_funcs.items():
        if len(funcs) == 1:
            cc_to_filename[cc] = f"sub_{list(funcs)[0]:x}"
        else:
            multifunc_count += 1
            cc_to_filename[cc] = f"multifunc_{multifunc_count}"

    func_to_filename = {f:cc_to_filename[func_to_cc[f]] for f in func_entries}
    xrefs = create_xrefs(graph, func_entries, dsu, cc_to_funcs)
    blocks = create_blocks(graph, func_entries, func_to_filename)
    cc_blocks = {}
    for addr, block in blocks.items():
        cc = dsu.find(addr)
        cc_blocks[cc] = cc_blocks.get(cc, {})
        cc_blocks[cc][addr]=block

    try:
        mkdir(directory)
    except FileExistsError:
        pass

    for cc, funcs in cc_to_funcs.items():
        render_svg(cc_blocks[cc], cc, funcs, cc_to_filename[cc], directory, xrefs, func_to_filename)
