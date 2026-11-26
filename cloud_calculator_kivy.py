import ast
import math
import operator

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, Rectangle


# CLOUD CALCULATOR - Android/Kivy edition
BG = (0.027, 0.043, 0.086, 1)
PANEL = (0.063, 0.094, 0.165, 1)
DISPLAY = (0.082, 0.133, 0.227, 1)
BLUE = (0.20, 0.39, 0.72, 1)
BLUE_LIGHT = (0.51, 0.68, 1.0, 1)
PURPLE = (0.52, 0.39, 0.78, 1)
GREEN = (0.57, 0.85, 0.72, 1)
WHITE = (0.91, 0.94, 1.0, 1)
GRAY = (0.53, 0.59, 0.70, 1)

memory = 0
history = []
angle_mode = "DEG"

binary_ops = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv
}
unary_ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_eval(expression, x_value=None):
    expression = expression.replace("^", "**").replace("π", "pi")
    expression = expression.replace("×", "*").replace("÷", "/")
    if len(expression) > 250:
        raise ValueError("Expresión demasiado larga")

    def trig(fn):
        return lambda x: fn(math.radians(x) if angle_mode == "DEG" else x)

    def inv(fn):
        return lambda x: math.degrees(fn(x)) if angle_mode == "DEG" else fn(x)

    funcs = {
        "sin": trig(math.sin), "cos": trig(math.cos), "tan": trig(math.tan),
        "asin": inv(math.asin), "acos": inv(math.acos), "atan": inv(math.atan),
        "sqrt": math.sqrt, "cbrt": lambda x: math.copysign(abs(x)**(1/3), x),
        "log": math.log10, "ln": math.log, "abs": abs, "exp": math.exp,
        "floor": math.floor, "ceil": math.ceil, "round": round,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh
    }
    constants = {"pi": math.pi, "e": math.e, "tau": math.tau}
    tree = ast.parse(expression, mode="eval")

    def calc(node):
        if isinstance(node, ast.Expression):
            return calc(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name):
            if node.id == "x" and x_value is not None:
                return x_value
            if node.id in constants:
                return constants[node.id]
            raise ValueError("Variable desconocida: " + node.id)
        if isinstance(node, ast.BinOp):
            op = type(node.op)
            if op not in binary_ops:
                raise ValueError("Operación no permitida")
            a, b = calc(node.left), calc(node.right)
            if op == ast.Pow and abs(b) > 100:
                raise ValueError("Exponente demasiado grande")
            result = binary_ops[op](a, b)
            if isinstance(result, complex):
                raise ValueError("Resultado complejo")
            if isinstance(result, float) and not math.isfinite(result):
                raise ValueError("Resultado no definido")
            return result
        if isinstance(node, ast.UnaryOp):
            op = type(node.op)
            if op not in unary_ops:
                raise ValueError("Operación no permitida")
            return unary_ops[op](calc(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if node.keywords:
                raise ValueError("Argumentos no permitidos")
            if name == "factorial":
                if len(node.args) != 1:
                    raise ValueError("Usa factorial(n)")
                n = calc(node.args[0])
                if not isinstance(n, int) or n < 0 or n > 170:
                    raise ValueError("Factorial requiere entero entre 0 y 170")
                return math.factorial(n)
            if name not in funcs or len(node.args) != 1:
                raise ValueError("Función o argumentos no válidos")
            return funcs[name](calc(node.args[0]))
        raise ValueError("Expresión no válida")

    result = calc(tree)
    if isinstance(result, complex):
        raise ValueError("Resultado complejo")
    if isinstance(result, float) and not math.isfinite(result):
        raise ValueError("Resultado no definido")
    return result


def fmt(value):
    return f"{value:.10g}" if isinstance(value, float) else str(value)


def parse_matrix(text):
    rows = [[float(v.strip()) for v in row.split(",")]
            for row in text.strip().split(";")]
    if not rows or not rows[0] or any(len(r) != len(rows[0]) for r in rows):
        raise ValueError("Matriz vacía o no rectangular")
    if len(rows) > 8 or len(rows[0]) > 8:
        raise ValueError("Máximo 8 x 8")
    return rows


def det(m):
    if len(m) != len(m[0]):
        raise ValueError("La matriz debe ser cuadrada")
    n = len(m)
    if n == 1:
        return m[0][0]
    if n == 2:
        return m[0][0]*m[1][1] - m[0][1]*m[1][0]
    return sum(((-1)**j) * m[0][j] *
               det([row[:j] + row[j+1:] for row in m[1:]])
               for j in range(n))


def parse_vector(text):
    v = [float(x.strip()) for x in text.split(",")]
    if len(v) not in (2, 3):
        raise ValueError("Usa 2 o 3 componentes")
    return v


class CloudCalculator(App):
    def build(self):
        self.title = "Cloud Calculator"
        self.root_box = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        self.root_box.bind(size=self.paint_bg)
        with self.root_box.canvas.before:
            self.bg_color = Color(*BG)
            self.bg_rect = Rectangle(pos=self.root_box.pos, size=self.root_box.size)

        title = Label(text="[b]C L O U D   C A L C U L A T O R[/b]",
                      markup=True, color=BLUE_LIGHT, size_hint_y=None, height=dp(32))
        self.root_box.add_widget(title)
        self.mode_label = Label(text="SCIENTIFIC  •  DEG", color=PURPLE,
                                size_hint_y=None, height=dp(22))
        self.root_box.add_widget(self.mode_label)

        self.expr = TextInput(text="", hint_text="Escribe una operación",
                              multiline=False, font_size="25sp", halign="right",
                              size_hint_y=None, height=dp(58),
                              background_color=DISPLAY, foreground_color=WHITE,
                              cursor_color=GREEN)
        self.root_box.add_widget(self.expr)
        self.result = Label(text="0", color=GREEN, font_size="20sp",
                            size_hint_y=None, height=dp(34), halign="right")
        self.result.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.root_box.add_widget(self.result)

        labrow = GridLayout(cols=3, spacing=dp(5), size_hint_y=None, height=dp(48))
        for name, fn, col in [
            ("GRAPHICS", self.graph_popup, GREEN),
            ("MATRIX", self.matrix_popup, BLUE),
            ("VECTOR", self.vector_popup, PURPLE)
        ]:
            labrow.add_widget(self.btn(name, fn, col))
        self.root_box.add_widget(labrow)

        scroll = ScrollView()
        keys = GridLayout(cols=5, spacing=dp(4), padding=dp(2),
                          size_hint_y=None)
        keys.bind(minimum_height=keys.setter("height"))
        layout = [
            ["AC", "DEL", "(", ")", "MODE"],
            ["sin(", "cos(", "tan(", "sqrt(", "pi"],
            ["asin(", "acos(", "atan(", "log(", "ln("],
            ["7", "8", "9", "/", "%"],
            ["4", "5", "6", "*", "e"],
            ["1", "2", "3", "-", "^"],
            ["0", ".", "x", "+", "!"],
            ["M+", "M-", "MR", "MC", "HIST"],
            ["abs(", "exp(", "cbrt(", "tau", "ANS"]
        ]
        for row in layout:
            for key in row:
                color = PURPLE if key in ("AC", "DEL") else BLUE
                if key in ("MODE", "HIST"):
                    color = GREEN
                keys.add_widget(self.btn(key, lambda k=key: self.keypress(k), color,
                                         height=dp(48)))
        scroll.add_widget(keys)
        self.root_box.add_widget(scroll)
        self.ans = "0"
        return self.root_box

    def paint_bg(self, *_):
        self.bg_rect.pos = self.root_box.pos
        self.bg_rect.size = self.root_box.size

    def btn(self, text, callback, color=BLUE, height=dp(46)):
        b = Button(text=text, size_hint_y=None, height=height,
                   background_normal="", background_down="",
                   background_color=color, color=WHITE,
                   font_size="14sp")
        b.bind(on_release=lambda *_: callback())
        return b

    def notify(self, title, message):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=str(message), color=WHITE))
        close = Button(text="VOLVER", size_hint_y=None, height=dp(45),
                       background_normal="", background_color=PURPLE)
        content.add_widget(close)
        pop = Popup(title=title, content=content, size_hint=(.92, .55))
        close.bind(on_release=pop.dismiss)
        pop.open()

    def keypress(self, key):
        global memory, angle_mode
        if key == "AC":
            self.expr.text = ""
            self.result.text = "0"
        elif key == "DEL":
            self.expr.text = self.expr.text[:-1]
        elif key == "MODE":
            angle_mode = "RAD" if angle_mode == "DEG" else "DEG"
            self.mode_label.text = "SCIENTIFIC  •  " + angle_mode
        elif key == "HIST":
            self.history_popup()
        elif key == "M+":
            try: memory += safe_eval(self.expr.text)
            except Exception as e: self.notify("Memoria", e)
        elif key == "M-":
            try: memory -= safe_eval(self.expr.text)
            except Exception as e: self.notify("Memoria", e)
        elif key == "MR":
            self.expr.text += str(memory)
        elif key == "MC":
            memory = 0
        elif key == "%":
            self.expr.text += "/100"
        elif key == "!":
            self.expr.text += "factorial("
        elif key == "ANS":
            self.expr.text += self.ans
        else:
            self.expr.text += key
        self.calculate_preview()

    def calculate_preview(self):
        try:
            if self.expr.text.strip():
                self.result.text = fmt(safe_eval(self.expr.text))
        except Exception:
            self.result.text = ""

    def calculate(self):
        try:
            exp = self.expr.text.strip()
            value = safe_eval(exp)
            self.ans = fmt(value)
            history.append(f"{exp} = {self.ans}")
            self.result.text = self.ans
            self.expr.text = self.ans
        except Exception as e:
            self.notify("Error de cálculo", e)

    def history_popup(self):
        body = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        listing = "\n".join(reversed(history[-40:])) or "Todavía no hay operaciones"
        body.add_widget(Label(text=listing, color=WHITE, halign="left",
                              valign="top", text_size=(dp(300), None)))
        close = self.btn("VOLVER", lambda: pop.dismiss(), PURPLE)
        body.add_widget(close)
        pop = Popup(title="HISTORY", content=body, size_hint=(.94, .8))
        pop.open()

    def matrix_popup(self):
        body = BoxLayout(orientation="vertical", spacing=dp(7), padding=dp(8))
        a = TextInput(text="1,2;3,4", hint_text="Matriz A: 1,2;3,4",
                      multiline=False, size_hint_y=None, height=dp(48))
        b = TextInput(text="5,6;7,8", hint_text="Matriz B",
                      multiline=False, size_hint_y=None, height=dp(48))
        out = Label(text="Resultado", color=GREEN)
        body.add_widget(Label(text="MATRIX LAB — columnas con coma, filas con ;",
                              color=BLUE_LIGHT, size_hint_y=None, height=dp(35)))
        body.add_widget(a); body.add_widget(b); body.add_widget(out)
        actions = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(150))
        def run(op):
            try:
                A = parse_matrix(a.text)
                B = parse_matrix(b.text) if b.text.strip() else None
                if op == "DET": r = det(A)
                elif op == "TRANS": r = [list(x) for x in zip(*A)]
                elif op in ("SUMA", "RESTA"):
                    if B is None or len(A) != len(B) or len(A[0]) != len(B[0]):
                        raise ValueError("Dimensiones incompatibles")
                    sign = 1 if op == "SUMA" else -1
                    r = [[A[i][j] + sign*B[i][j] for j in range(len(A[0]))]
                         for i in range(len(A))]
                else:
                    if B is None or len(A[0]) != len(B):
                        raise ValueError("Dimensiones incompatibles")
                    r = [[sum(A[i][k]*B[k][j] for k in range(len(B)))
                          for j in range(len(B[0]))] for i in range(len(A))]
                out.text = f"{op}: {r}"
            except Exception as e: out.text = "ERROR: " + str(e)
        for op in ("DET", "TRANS", "SUMA", "RESTA", "MULT"):
            actions.add_widget(self.btn(op, lambda x=op: run(x), PURPLE if op == "DET" else BLUE))
        body.add_widget(actions)
        pop = Popup(title="MATRIX LAB", content=body, size_hint=(.96, .88))
        body.add_widget(self.btn("VOLVER", pop.dismiss, PURPLE))
        pop.open()

    def vector_popup(self):
        body = BoxLayout(orientation="vertical", spacing=dp(7), padding=dp(8))
        a = TextInput(text="2,3,4", hint_text="Vector A: 2,3,4",
                      multiline=False, size_hint_y=None, height=dp(48))
        b = TextInput(text="1,2,3", hint_text="Vector B: 1,2,3",
                      multiline=False, size_hint_y=None, height=dp(48))
        out = Label(text="Resultado", color=GREEN)
        body.add_widget(a); body.add_widget(b); body.add_widget(out)
        actions = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(210))
        def run(op):
            try:
                A = parse_vector(a.text)
                B = parse_vector(b.text) if b.text.strip() else None
                if op == "NORMA A": r = math.sqrt(sum(x*x for x in A))
                elif op == "NORMA B":
                    if B is None: raise ValueError("Falta B")
                    r = math.sqrt(sum(x*x for x in B))
                else:
                    if B is None or len(A) != len(B):
                        raise ValueError("Vectores incompatibles")
                    if op == "SUMA": r = [x+y for x,y in zip(A,B)]
                    elif op == "RESTA": r = [x-y for x,y in zip(A,B)]
                    elif op == "PUNTO": r = sum(x*y for x,y in zip(A,B))
                    elif op == "CRUZ":
                        if len(A) != 3: raise ValueError("Producto cruz requiere 3D")
                        r = [A[1]*B[2]-A[2]*B[1], A[2]*B[0]-A[0]*B[2],
                             A[0]*B[1]-A[1]*B[0]]
                    else:
                        na = math.sqrt(sum(x*x for x in A)); nb = math.sqrt(sum(x*x for x in B))
                        if na == 0 or nb == 0: raise ValueError("Vector nulo")
                        c = max(-1, min(1, sum(x*y for x,y in zip(A,B))/(na*nb)))
                        r = math.degrees(math.acos(c))
                out.text = f"{op}: {r}"
            except Exception as e: out.text = "ERROR: " + str(e)
        for op in ("NORMA A", "NORMA B", "SUMA", "RESTA", "PUNTO", "CRUZ", "ANGULO"):
            actions.add_widget(self.btn(op, lambda x=op: run(x), PURPLE if op == "ANGULO" else BLUE))
        body.add_widget(actions)
        pop = Popup(title="VECTOR LAB", content=body, size_hint=(.96, .88))
        body.add_widget(self.btn("VOLVER", pop.dismiss, PURPLE))
        pop.open()

    def graph_popup(self):
        body = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        fn = TextInput(text="x^2", hint_text="Función: x^2, sin(x), cos(x)",
                       multiline=False, size_hint_y=None, height=dp(45))
        ranges = GridLayout(cols=4, spacing=dp(4), size_hint_y=None, height=dp(42))
        fields = []
        for value in ("-10", "10", "-10", "10"):
            t = TextInput(text=value, multiline=False, size_hint_x=1)
            fields.append(t); ranges.add_widget(t)
        canvas_box = BoxLayout()
        with canvas_box.canvas:
            Color(0.03, 0.06, 0.12, 1)
            rect = Rectangle(pos=canvas_box.pos, size=canvas_box.size)
        def redraw(*_):
            canvas_box.canvas.clear()
            w, h = canvas_box.size
            if w < 20 or h < 20: return
            try:
                xmin, xmax, ymin, ymax = [float(t.text) for t in fields]
                if xmin >= xmax or ymin >= ymax: raise ValueError("Rangos inválidos")
                with canvas_box.canvas:
                    Color(0.03, 0.06, 0.12, 1); Rectangle(pos=canvas_box.pos, size=canvas_box.size)
                    Color(0.12, 0.19, 0.30, 1)
                    for i in range(11):
                        x = canvas_box.x + w*i/10
                        y = canvas_box.y + h*i/10
                        Line(points=[x, canvas_box.y, x, canvas_box.top], width=1)
                        Line(points=[canvas_box.x, y, canvas_box.right, y], width=1)
                    Color(*WHITE)
                    if xmin <= 0 <= xmax:
                        x0 = canvas_box.x + (0-xmin)/(xmax-xmin)*w
                        Line(points=[x0, canvas_box.y, x0, canvas_box.top], width=1.2)
                    if ymin <= 0 <= ymax:
                        y0 = canvas_box.y + (0-ymin)/(ymax-ymin)*h
                        Line(points=[canvas_box.x, y0, canvas_box.right, y0], width=1.2)
                    Color(*BLUE_LIGHT)
                    points = []
                    old = angle_mode
                    globals()["angle_mode"] = "RAD"
                    try:
                        for i in range(401):
                            x = xmin + (xmax-xmin)*i/400
                            try:
                                y = safe_eval(fn.text, x)
                                if abs(y) > 1e6: raise ValueError()
                                points.extend([canvas_box.x+(x-xmin)/(xmax-xmin)*w,
                                               canvas_box.y+(y-ymin)/(ymax-ymin)*h])
                            except Exception:
                                if len(points) >= 4: Line(points=points, width=1.7)
                                points = []
                        if len(points) >= 4: Line(points=points, width=1.7)
                    finally:
                        globals()["angle_mode"] = old
            except Exception:
                pass
        canvas_box.bind(size=redraw, pos=redraw)
        def draw_now(*_):
            redraw()
        body.add_widget(fn); body.add_widget(ranges); body.add_widget(canvas_box)
        body.add_widget(self.btn("DIBUJAR", draw_now, GREEN))
        pop = Popup(title="CLOUD GRAPHICS", content=body, size_hint=(.98, .92))
        body.add_widget(self.btn("VOLVER", pop.dismiss, PURPLE))
        pop.bind(on_open=lambda *_: redraw())
        pop.open()


if __name__ == "__main__":
    CloudCalculator().run()
