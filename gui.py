#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI del compilador para el mini lenguaje de gestión de incidencias
de un laboratorio inteligente.

La GUI invoca el ejecutable generado con Flex/Bison (compilador / compilador.exe),
y muestra los errores léxicos, sintácticos y semánticos con su línea.
"""
import os
import re
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE = os.path.dirname(os.path.abspath(__file__))
EXE_NAME = "compilador.exe" if os.name == "nt" else "compilador"

KEYWORDS = ["INCIDENTE", "SENSOR", "NIVEL", "REPORTAR", "LUZ", "TEMPERATURA",
            "SI", "ENTONCES", "ENCENDER", "APAGAR", "MOSTRAR", "FIN", "ON", "OFF"]

CATEGORIA = {
    "IDENT": "Identificador", "NUMERO": "Número", "CADENA": "Cadena",
    "SEMI": "Delimitador",
    "GT": "Operador", "LT": "Operador", "GE": "Operador",
    "LE": "Operador", "EQ": "Operador", "NE": "Operador",
}

COLORES = {            # tipo de error -> color de fondo en el editor
    "LEXICO": "#ffd6d6",
    "SINTACTICO": "#ffe9b8",
    "SEMANTICO": "#d6e4ff",
}

EJEMPLO = """INCIDENTE fuga_gas;
SENSOR sensor_03;
NIVEL 4;
REPORTAR fuga_gas;

LUZ luz_principal ON;
TEMPERATURA 22;
SI TEMPERATURA > 28
ENTONCES APAGAR luz_principal;
FIN
"""


class LineNumbers(tk.Canvas):
    """Numeración de líneas sincronizada con un widget Text."""

    def __init__(self, master, text, **kw):
        super().__init__(master, width=46, highlightthickness=0,
                         bg="#f0f0f0", **kw)
        self.text = text

    def redraw(self, *_):
        self.delete("all")
        i = self.text.index("@0,0")
        last = None
        while i != last:
            info = self.text.dlineinfo(i)
            if info is None:
                break
            self.create_text(40, info[1], anchor="ne", fill="#777",
                             text=i.split(".")[0], font=self.text["font"])
            last = i
            i = self.text.index(f"{i}+1line")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Compilador - Gestión de incidencias de laboratorio inteligente")
        self.geometry("1100x760")
        self.minsize(850, 600)
        self.archivo = None
        self.exe = None
        self._build_ui()
        self.text.insert("1.0", EJEMPLO)
        self._on_change()

    # ------------------------------------------------------------ UI
    def _build_ui(self):
        # Barra de herramientas
        bar = ttk.Frame(self, padding=4)
        bar.pack(fill="x")
        for txt, cmd in [("Abrir…", self.abrir), ("Guardar", self.guardar),
                         ("Nuevo", self.nuevo)]:
            ttk.Button(bar, text=txt, command=cmd).pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar, text="▶ Compilar (F5)",
                   command=self.compilar).pack(side="left", padx=2)
        ttk.Button(bar, text="Seleccionar compilador…",
                   command=self.elegir_exe).pack(side="right", padx=2)
        self.bind("<F5>", lambda e: self.compilar())
        self.bind("<Control-o>", lambda e: self.abrir())
        self.bind("<Control-s>", lambda e: self.guardar())

        paned = ttk.PanedWindow(self, orient="vertical")
        paned.pack(fill="both", expand=True, padx=4, pady=4)

        # Editor
        ed = ttk.LabelFrame(paned, text="Código fuente")
        paned.add(ed, weight=3)
        fr = ttk.Frame(ed)
        fr.pack(fill="both", expand=True)
        self.text = tk.Text(fr, wrap="none", undo=True, font=("Consolas", 12),
                            bg="white", insertbackground="black", tabs=("1c",))
        self.lines = LineNumbers(fr, self.text)
        self.vsb = ttk.Scrollbar(fr, orient="vertical", command=self.text.yview)
        self.hsb = ttk.Scrollbar(ed, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=self._yscroll, xscrollcommand=self.hsb.set)
        self.lines.pack(side="left", fill="y")
        self.vsb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.hsb.pack(fill="x")

        self.text.tag_configure("kw", foreground="#0b5cad", font=("Consolas", 12, "bold"))
        self.text.tag_configure("num", foreground="#b35900")
        self.text.tag_configure("str", foreground="#2e7d32")
        self.text.tag_configure("com", foreground="#888888")
        for tipo, color in COLORES.items():
            self.text.tag_configure("err_" + tipo, background=color)
            self.text.tag_lower("err_" + tipo)
        self.text.bind("<KeyRelease>", self._on_change)
        self.text.bind("<<Paste>>", lambda e: self.after(10, self._on_change))
        self.text.bind("<MouseWheel>", lambda e: self.after(5, self.lines.redraw))
        self.text.bind("<Configure>", lambda e: self.lines.redraw())

        # Resultados
        res = ttk.LabelFrame(paned, text="Resultados de la compilación")
        paned.add(res, weight=2)
        self.resumen = ttk.Label(res, text="Sin compilar.", font=("Segoe UI", 10, "bold"))
        self.resumen.pack(anchor="w", padx=6, pady=3)

        nb = ttk.Notebook(res)
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        self.t_err = self._tabla(nb, "Errores", ("Tipo", "Línea", "Descripción"),
                                 (110, 60, 800))
        self.t_tok = self._tabla(nb, "Tokens (léxico)",
                                 ("Línea", "Categoría", "Token", "Lexema"),
                                 (60, 130, 160, 400))
        self.t_sym = self._tabla(nb, "Tabla de símbolos",
                                 ("Nombre", "Tipo", "Línea", "Detalle"),
                                 (180, 120, 60, 450))
        for tipo, color in COLORES.items():
            self.t_err.tag_configure(tipo, background=color)
        self.t_err.bind("<Double-1>", self._ir_a_linea)

        self.status = ttk.Label(self, anchor="w", relief="sunken")
        self.status.pack(fill="x", side="bottom")

    def _tabla(self, nb, titulo, cols, anchos):
        frame = ttk.Frame(nb)
        nb.add(frame, text=titulo)
        tv = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        for c, w in zip(cols, anchos):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor="w", stretch=(c == cols[-1]))
        sb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tv

    # ------------------------------------------------------ Editor
    def _yscroll(self, a, b):
        self.vsb.set(a, b)
        self.lines.redraw()

    def _on_change(self, *_):
        self.lines.redraw()
        self._resaltar()

    def _resaltar(self):
        for t in ("kw", "num", "str", "com"):
            self.text.tag_remove(t, "1.0", "end")
        code = self.text.get("1.0", "end-1c")
        patrones = [
            ("com", r"//[^\n]*"),
            ("str", r'"[^"\n]*"?'),
            ("kw", r"\b(?:" + "|".join(KEYWORDS) + r")\b"),
            ("num", r"(?<![A-Za-z_0-9])-?\d+(?:\.\d+)?(?![A-Za-z_])"),
        ]
        for tag, pat in patrones:
            for m in re.finditer(pat, code):
                self.text.tag_add(tag, f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def _marcar_errores(self, errores):
        for tipo in COLORES:
            self.text.tag_remove("err_" + tipo, "1.0", "end")
        for tipo, linea, _ in errores:
            self.text.tag_add("err_" + tipo, f"{linea}.0", f"{linea}.0 lineend+1c")

    def _ir_a_linea(self, _evt):
        sel = self.t_err.selection()
        if not sel:
            return
        linea = self.t_err.item(sel[0], "values")[1]
        self.text.mark_set("insert", f"{linea}.0")
        self.text.see(f"{linea}.0")
        self.text.focus_set()

    # ------------------------------------------------------ Archivos
    def nuevo(self):
        self.text.delete("1.0", "end")
        self.archivo = None
        self._on_change()

    def abrir(self):
        ruta = filedialog.askopenfilename(
            title="Abrir código fuente",
            filetypes=[("Código fuente", "*.txt *.lab *.inc"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8", errors="replace") as f:
                contenido = f.read()
        except OSError as e:
            messagebox.showerror("Error", str(e))
            return
        self.text.delete("1.0", "end")
        self.text.insert("1.0", contenido)
        self.archivo = ruta
        self.title(f"Compilador - {os.path.basename(ruta)}")
        self._on_change()
        self.compilar()

    def guardar(self):
        if not self.archivo:
            self.archivo = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Texto", "*.txt")])
            if not self.archivo:
                return
        with open(self.archivo, "w", encoding="utf-8") as f:
            f.write(self.text.get("1.0", "end-1c"))
        self.status.config(text=f"Guardado: {self.archivo}")

    # ------------------------------------------------------ Compilador
    def _buscar_exe(self):
        if self.exe and os.path.isfile(self.exe):
            return self.exe
        for ruta in (os.path.join(BASE, EXE_NAME), os.path.join(BASE, "build", EXE_NAME)):
            if os.path.isfile(ruta):
                self.exe = ruta
                return ruta
        return None

    def elegir_exe(self):
        ruta = filedialog.askopenfilename(title="Seleccionar ejecutable del compilador")
        if ruta:
            self.exe = ruta
            self.status.config(text=f"Compilador: {ruta}")

    def compilar(self):
        codigo = self.text.get("1.0", "end-1c")
        if not codigo.strip():
            messagebox.showwarning("Aviso", "No hay código para compilar.")
            return
        exe = self._buscar_exe()
        if not exe:
            messagebox.showerror(
                "Compilador no encontrado",
                f"No se encontró '{EXE_NAME}' junto a gui.py.\n\n"
                "Genéralo primero con Flex/Bison:\n"
                "  • Linux/macOS: make\n"
                "  • Windows: build.bat\n\n"
                "o selecciona el ejecutable con 'Seleccionar compilador…'.")
            return

        tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                          encoding="utf-8", newline="\n")
        try:
            tmp.write(codigo)
            tmp.close()
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.run([exe, tmp.name], capture_output=True,
                                  timeout=15, creationflags=flags)
            salida = proc.stdout.decode("utf-8", "replace")
            if proc.returncode == 2:
                messagebox.showerror("Error", proc.stderr.decode("utf-8", "replace"))
                return
        except subprocess.TimeoutExpired:
            messagebox.showerror("Error", "El compilador tardó demasiado en responder.")
            return
        except OSError as e:
            messagebox.showerror("Error al ejecutar el compilador", str(e))
            return
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
        self._mostrar(salida)

    def _mostrar(self, salida):
        errores, tokens, simbolos = [], [], []
        resumen = (0, 0, 0)
        for linea in salida.splitlines():
            p = linea.strip("\r").split("|", 4)
            if p[0] == "ERROR" and len(p) >= 4:
                resto = linea.strip("\r").split("|", 3)
                errores.append((resto[1], int(resto[2]), resto[3]))
            elif p[0] == "TOKEN" and len(p) >= 4:
                resto = linea.strip("\r").split("|", 3)
                tipo = resto[2]
                cat = CATEGORIA.get(tipo, "Palabra reservada")
                tokens.append((resto[1], cat, tipo, resto[3]))
            elif p[0] == "SYM" and len(p) >= 5:
                simbolos.append(tuple(p[1:5]))
            elif p[0] == "SUMMARY" and len(p) >= 4:
                resumen = tuple(int(x) for x in p[1:4])

        errores.sort(key=lambda e: (e[1], e[0]))
        for tv in (self.t_err, self.t_tok, self.t_sym):
            tv.delete(*tv.get_children())
        etiquetas = {"LEXICO": "Léxico", "SINTACTICO": "Sintáctico",
                     "SEMANTICO": "Semántico"}
        for tipo, linea, desc in errores:
            self.t_err.insert("", "end", values=(etiquetas[tipo], linea, desc), tags=(tipo,))
        for t in tokens:
            self.t_tok.insert("", "end", values=t)
        for s in simbolos:
            self.t_sym.insert("", "end", values=s)
        self._marcar_errores(errores)

        total = sum(resumen)
        if total == 0:
            self.resumen.config(text="✔ Compilación exitosa: 0 errores.", foreground="#1b7f2a")
        else:
            self.resumen.config(
                text=f"✘ {total} error(es)  —  Léxicos: {resumen[0]}   "
                     f"Sintácticos: {resumen[1]}   Semánticos: {resumen[2]}",
                foreground="#b00020")
        self.status.config(text=f"Tokens: {len(tokens)}   Símbolos: {len(simbolos)}   "
                                f"Errores: {total}")


if __name__ == "__main__":
    App().mainloop()
