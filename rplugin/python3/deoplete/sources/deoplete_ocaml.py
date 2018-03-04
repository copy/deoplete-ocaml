# -*- coding: utf-8 -*-

from .base import Base
import re
import subprocess
import json
import pprint

from neovim.api import nvim
from deoplete import util

DEBUG = False

def concat_map(f, args):
    return [item for arg in args for item in f(arg)]


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'ocaml'
        self.mark = '[ocaml]'
        self.filetypes = ['ocaml']
        self.rank = 1000
        self.input_pattern = r'[^\s\'"]*'
        self.current = vim.current
        self.vim = vim
        self.debug_enabled = False
        self.get_complete_position_re = re.compile(r"\w*$")
        self.complete_query_re = re.compile(r'[^#\s\'"()[\]]*$')

        # Expression suggested by merlin:
        #   https://github.com/ocaml/merlin/blob/a2facd4bb772ee0261859382964c30e8401866e8/vim/merlin/doc/merlin.txt#L352
        #self.complete_query_re = re.compile(r'[^. *\t]\.\w*$|\s\w*$|#$', re.I)

    def _is_set(self, name, default=False):
        if not self.vim.eval("exists('%s')" % name):
            return default
        return not (self.vim.eval(name) in ["", 0, "0", "false"])

    def _list_if_set(self, name):
        return self.vim.eval("exists('{0}') ? {0} : []".format(name))

    def on_init(self, context): # called by deoplete

        try:
            self.merlin_binary = self.vim.eval("merlin#SelectBinary()")
        except nvim.NvimError:
            util.debug(self.vim, "Merlin not found, make sure ocamlmerlin is in your path and merlin's vim plugin is installed")
            self.merlin_binary = None
            return

        self.merlin_completion_with_doc = self._is_set("g:merlin_completion_with_doc")
        self.merlin_binary_flags = self.vim.eval("g:merlin_binary_flags")
        self.buffer_merlin_flags = self._list_if_set("b:merlin_flags")
        self.merlin_extensions = concat_map(lambda ext: ("-extension",ext), self._list_if_set("b:merlin_extensions"))
        self.merlin_packages = concat_map(lambda pkg: ("-package",pkg), self._list_if_set("b:merlin_packages"))
        self.merlin_dot_merlins = concat_map(lambda dm: ("-dot-merlin",dm), self._list_if_set("b:merlin_dot_merlins"))

        if self._is_set("g:merlin_debug"):
            log_errors = ["-log-file", "-"]
        else:
            log_errors = []
        self.merlin_log_errors = log_errors

    def get_complete_position(self, context): # called by deoplete
        m = re.search(self.get_complete_position_re, context["input"])
        if DEBUG:
            with open("/tmp/deoplete-ocaml-complete-position.log", "a") as f:
                pprint.pprint(m.start() if m else None, f)
        return m.start() if m else None

    def _get_complete_query(self, context):
        m = re.search(self.complete_query_re, context["input"])
        return m.group() if m else None

    def gather_candidates(self, context): # called by deoplete

        if not self.merlin_binary:
            return []

        prefix = self._get_complete_query(context) or ""
        filename = context["bufpath"]
        position = "{}:{}".format(context["position"][1], context["position"][2])
        lines = self.vim.current.buffer[:]
        input = "\n".join(lines).encode("utf8")

        cmd = (
            [
                self.merlin_binary,
                "server",
                "complete-prefix",
                "-prefix", prefix,
                "-position", position,
                "-filename", filename,
                "-doc", "y" if self.merlin_completion_with_doc else "n",
            ] +
            self.merlin_extensions +
            self.merlin_packages +
            self.merlin_dot_merlins +
            self.merlin_log_errors +
            self.merlin_binary_flags +
            self.buffer_merlin_flags
        )

        process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False)

        (output, errors) = process.communicate(input=input)

        if errors:
            buf = int(self.vim.eval("bufnr('*merlin-log*',1)"))
            self.vim.buffers[buf].append(errors.split(b'\n'))

        try:
            result_json = json.loads(output)
            value = result_json["value"]
            entries = value["entries"]
        except Exception as e:
            entries = []

            if DEBUG:
                with open("/tmp/deoplete-ocaml-exn.log", "a"): pprint.pprint(e, f)

        if DEBUG:
            if errors:
                with open("/tmp/deoplete-ocaml-merlin-errors.log", "a") as f:
                    pprint.pprint(errors, f)
            with open("/tmp/deoplete-ocaml-entries.log", "a") as f: pprint.pprint(entries, f)
            with open("/tmp/deoplete-ocaml-context.log", "a") as f: pprint.pprint(context, f)
            with open("/tmp/deoplete-ocaml-cmd.log", "a") as f: pprint.pprint(cmd, f)

        complete_entries = [
            {
                "word": e["name"],
                "abbr": e["name"],
                "kind": e["desc"],
                "info": e["name"] + " : " + e["desc"] + "\n" + e["info"].strip(),
                "dup": 1,
            }
            for e in entries
        ]

        return complete_entries
