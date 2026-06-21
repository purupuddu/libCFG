# libCFG

Language-agnostic Python library for building and rendering control flow graphs with minimal intermediate language.

The CFGs are svg files generated with graphviz. HTML wrappers are included for easy navigation.

## Requirements

On Debian/Ubuntu

```bash
sudo apt install graphviz
```
On macOS with Homebrew:

```bash
brew install graphviz
```

## Installation


```bash
python -m pip install git+https://github.com/purupuddu/libCFG.git
```

With `uv`:

```bash
uv add git+https://github.com/purupuddu/libCFG.git
```

## Usage

All you need to do is provide a python function which acts as disassembler and returns instructions in the intermediate language. 

The instructions are of these kinds:
- `Instruction(nexti, "disassembled")` : a default for any non-control-flow instruction
- `Call(nexti, target)`
- `Ret("name")` : also for cases such as exit / jmp $reg, where you don't have a known next address
- `Jump(target)`
- `CondJump(cond_true, cond_false, "jXX loc_YYY")`

The disassembler takes the whole binary file as bytes and an address and returns the instruction at that address.

Calling 
```
libcfg.CFG(binary:bytes, disassembler:Callable[[bytes, int], BaseInstruction], entry_points:List[int])
```
generates a directory containing an html+svg for each function. 


