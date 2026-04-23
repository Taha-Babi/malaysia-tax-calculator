"""
Malaysia Tax Calculator — Kivy UI
Compatible with Buildozer for Android APK generation.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = get_color_from_hex("#0f0f1a")
CARD        = get_color_from_hex("#1a1a2e")
ACCENT      = get_color_from_hex("#4361ee")
ACCENT2     = get_color_from_hex("#4cc9f0")
TEXT        = get_color_from_hex("#e0e0e0")
SUBTEXT     = get_color_from_hex("#a0a0b0")
DIVIDER     = get_color_from_hex("#2a2a3e")
GREEN       = get_color_from_hex("#4ade80")
RED         = get_color_from_hex("#f87171")
WHITE       = get_color_from_hex("#ffffff")

Window.clearcolor = BG

# ── Tax logic ─────────────────────────────────────────────────────────────────
TAX_BRACKETS = [
    (5_000,        0.00),
    (15_000,       0.01),
    (15_000,       0.03),
    (15_000,       0.06),
    (15_000,       0.11),
    (20_000,       0.19),
    (30_000,       0.25),
    (float("inf"), 0.26),
]

def round_sen(x): return round(x, 2)
def round_rm(x):  return round(x)

def calculate(monthly_salary, tax_reliefs, monthly_socso, monthly_eis,
              is_foreigner, usd_to_myr):
    yearly_gross = round_sen(monthly_salary * 12)
    epf_rate     = 0.02 if is_foreigner else 0.11
    yearly_epf   = round_sen(yearly_gross * epf_rate)
    monthly_epf  = round_sen(yearly_epf / 12)
    yearly_socso = round_sen(monthly_socso * 12)
    yearly_eis   = round_sen(monthly_eis * 12)

    taxable_income = max(round_sen(yearly_gross - tax_reliefs - yearly_epf), 0)

    remaining, total_tax, breakdown = taxable_income, 0.0, []
    for limit, rate in TAX_BRACKETS:
        if remaining <= 0:
            break
        amt = min(remaining, limit)
        tax = amt * rate
        breakdown.append((amt, rate, tax))
        total_tax += tax
        remaining -= amt

    yearly_tax  = round_sen(total_tax)
    monthly_tax = round_rm(yearly_tax / 12)
    yearly_net  = round_sen(yearly_gross - yearly_tax - yearly_socso - yearly_eis - yearly_epf)
    monthly_net = round_sen(monthly_salary - monthly_tax - monthly_socso - monthly_eis - monthly_epf)

    return dict(
        monthly_salary=monthly_salary, yearly_gross=yearly_gross,
        epf_rate=epf_rate, yearly_epf=yearly_epf, monthly_epf=monthly_epf,
        yearly_socso=yearly_socso, monthly_socso=monthly_socso,
        yearly_eis=yearly_eis, monthly_eis=monthly_eis,
        taxable_income=taxable_income, breakdown=breakdown,
        yearly_tax=yearly_tax, monthly_tax=monthly_tax,
        yearly_net=yearly_net, monthly_net=monthly_net,
    )

# ── Helpers ───────────────────────────────────────────────────────────────────
def card(padding=dp(16), spacing=dp(10), orientation="vertical", **kw):
    b = BoxLayout(orientation=orientation, padding=padding,
                  spacing=spacing, size_hint_y=None, **kw)
    with b.canvas.before:
        from kivy.graphics import Color, RoundedRectangle
        Color(*CARD)
        b._rect = RoundedRectangle(pos=b.pos, size=b.size, radius=[dp(12)])
    b.bind(pos=lambda w, v: setattr(w._rect, "pos", v),
           size=lambda w, v: setattr(w._rect, "size", v))
    return b

def lbl(text, size=14, color=TEXT, bold=False, halign="left", **kw):
    l = Label(text=text, font_size=sp(size), color=color, bold=bold,
              halign=halign, valign="middle", size_hint_y=None, **kw)
    l.bind(texture_size=lambda w, v: setattr(w, "height", v[1] + dp(4)))
    l.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
    return l

def field(hint, default="", numeric=True):
    return TextInput(
        hint_text=hint, text=default, multiline=False,
        input_filter="float" if numeric else None,
        font_size=sp(14), foreground_color=WHITE,
        background_color=get_color_from_hex("#16213e"),
        cursor_color=ACCENT2, hint_text_color=SUBTEXT,
        padding=[dp(10), dp(10)],
        size_hint_y=None, height=dp(44))

def divider():
    from kivy.uix.widget import Widget
    from kivy.graphics import Color, Rectangle
    w = Widget(size_hint_y=None, height=dp(1))
    with w.canvas:
        Color(*DIVIDER)
        w._line = Rectangle(pos=w.pos, size=w.size)
    w.bind(pos=lambda s, v: setattr(s._line, "pos", v),
           size=lambda s, v: setattr(s._line, "size", v))
    return w

def toggle_row(values, group, active_index=0):
    row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
    btns = []
    for i, val in enumerate(values):
        tb = ToggleButton(
            text=val, group=group,
            state="down" if i == active_index else "normal",
            font_size=sp(13),
            background_normal="", background_down="",
            background_color=(0, 0, 0, 0))
        # colour via canvas
        def _update(btn, *_):
            btn.canvas.before.clear()
            with btn.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                if btn.state == "down":
                    Color(*ACCENT)
                else:
                    Color(*get_color_from_hex("#2a2a3e"))
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])
        tb.bind(state=_update, pos=_update, size=_update)
        row.add_widget(tb)
        btns.append(tb)
    return row, btns

# ─────────────────────────────────────────────────────────────────────────────
class InputScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(56),
                        padding=[dp(16), 0])
        with hdr.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*get_color_from_hex("#1a1a2e"))
            hdr._bg = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda w, v: setattr(w._bg, "pos", v),
                 size=lambda w, v: setattr(w._bg, "size", v))
        hdr.add_widget(lbl("🇲🇾  Malaysia Tax Calculator",
                           size=17, bold=True, color=ACCENT2))
        root.add_widget(hdr)

        # Scrollable form
        sv = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation="vertical", spacing=dp(12),
                         padding=[dp(12), dp(12)], size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        # ── Salary card ───────────────────────────────────────────────────────
        sc = card()
        sc.add_widget(lbl("Salary Type", bold=True, color=ACCENT2))
        self.salary_row, self.salary_btns = toggle_row(
            ["Monthly", "Yearly"], "salary_type")
        sc.add_widget(self.salary_row)
        self.salary_label = lbl("Monthly Salary (RM)", color=SUBTEXT, size=12)
        sc.add_widget(self.salary_label)
        self.f_salary = field("e.g. 6000", "6000")
        sc.add_widget(self.f_salary)
        self.salary_btns[0].bind(state=self._on_salary_type)
        self.salary_btns[1].bind(state=self._on_salary_type)
        sc.height = self._card_height(sc)
        sc.bind(minimum_height=sc.setter("height"))
        form.add_widget(sc)

        # ── Deductions card ───────────────────────────────────────────────────
        dc = card()
        dc.add_widget(lbl("Deductions & Reliefs", bold=True, color=ACCENT2))
        for lbl_text, hint, default, attr in [
            ("Tax Reliefs (RM)",            "e.g. 9000",  "9000",  "f_relief"),
            ("Monthly SOCSO (RM)",          "e.g. 29.75", "29.75", "f_socso"),
            ("Monthly EIS (RM) — optional", "e.g. 12.00", "0",     "f_eis"),
            ("USD → MYR Rate",              "e.g. 4.47",  "4.47",  "f_usd"),
        ]:
            dc.add_widget(lbl(lbl_text, color=SUBTEXT, size=12))
            f = field(hint, default)
            dc.add_widget(f)
            setattr(self, attr, f)
        dc.bind(minimum_height=dc.setter("height"))
        form.add_widget(dc)

        # ── Employee type card ────────────────────────────────────────────────
        ec = card()
        ec.add_widget(lbl("Employee Type", bold=True, color=ACCENT2))
        self.emp_row, self.emp_btns = toggle_row(
            ["Local  EPF 11%", "Foreigner  EPF 2%"], "emp_type")
        ec.add_widget(self.emp_row)
        ec.bind(minimum_height=ec.setter("height"))
        form.add_widget(ec)

        # ── Calculate button ──────────────────────────────────────────────────
        btn = Button(
            text="Calculate  →", size_hint_y=None, height=dp(50),
            font_size=sp(15), bold=True,
            background_normal="", background_color=ACCENT,
            color=WHITE)
        btn.bind(on_release=self._on_calculate)
        form.add_widget(btn)

        sv.add_widget(form)
        root.add_widget(sv)
        self.add_widget(root)

    def _card_height(self, c):
        return sum(ch.height for ch in c.children) + dp(32)

    def _on_salary_type(self, btn, state):
        if btn == self.salary_btns[1] and state == "down":
            self.salary_label.text = "Yearly Salary (RM)"
        elif btn == self.salary_btns[0] and state == "down":
            self.salary_label.text = "Monthly Salary (RM)"

    def _on_calculate(self, *_):
        try:
            salary_val    = float(self.f_salary.text  or "0")
            tax_reliefs   = float(self.f_relief.text  or "0")
            monthly_socso = float(self.f_socso.text   or "0")
            monthly_eis   = float(self.f_eis.text     or "0")
            usd_to_myr    = float(self.f_usd.text     or "0")
            if usd_to_myr <= 0:
                raise ValueError
            is_yearly    = self.salary_btns[1].state == "down"
            is_foreigner = self.emp_btns[1].state == "down"
            monthly_salary = round_sen(salary_val / 12) if is_yearly else salary_val
        except ValueError:
            Popup(title="Invalid Input",
                  content=lbl("Please enter valid numbers\nin all fields.",
                               halign="center"),
                  size_hint=(0.8, 0.3)).open()
            return

        r = calculate(monthly_salary, tax_reliefs, monthly_socso,
                      monthly_eis, is_foreigner, usd_to_myr)

        # Pass to results screen
        rs = self.manager.get_screen("results")
        rs.populate(r, usd_to_myr)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "results"


# ─────────────────────────────────────────────────────────────────────────────
class ResultsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(56),
                        padding=[dp(8), 0], spacing=dp(8))
        with hdr.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*get_color_from_hex("#1a1a2e"))
            hdr._bg = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda w, v: setattr(w._bg, "pos", v),
                 size=lambda w, v: setattr(w._bg, "size", v))

        back_btn = Button(
            text="← Back", size_hint=(None, None),
            width=dp(80), height=dp(40),
            font_size=sp(13), color=ACCENT2,
            background_normal="", background_color=(0, 0, 0, 0))
        back_btn.bind(on_release=self._go_back)
        hdr.add_widget(back_btn)
        hdr.add_widget(lbl("📊  Results", size=17, bold=True, color=ACCENT2))
        root.add_widget(hdr)

        sv = ScrollView(do_scroll_x=False)
        self.content = BoxLayout(
            orientation="vertical", spacing=dp(12),
            padding=[dp(12), dp(12)], size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        sv.add_widget(self.content)
        root.add_widget(sv)
        self.add_widget(root)

    def _go_back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "input"

    def _row(self, left, rm_val, usd_val=None, bold=False, color=TEXT):
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
        row.add_widget(lbl(left, size=13, color=color, bold=bold))
        rm_str = f"RM {rm_val:,.2f}" if isinstance(rm_val, float) else f"RM {rm_val:,}"
        row.add_widget(lbl(rm_str, size=13, color=color, bold=bold, halign="right"))
        if usd_val is not None:
            row.add_widget(lbl(f"USD {usd_val:,.2f}", size=12,
                               color=SUBTEXT, halign="right"))
        return row

    def populate(self, r, u):
        self.content.clear_widgets()
        c = self.content

        # ── Summary card ──────────────────────────────────────────────────────
        sc = card()
        sc.add_widget(lbl("Summary", bold=True, color=ACCENT2, size=14))
        sc.add_widget(divider())
        sc.add_widget(self._row("Monthly Gross",
                                r['monthly_salary'], r['monthly_salary'] / u))
        sc.add_widget(self._row("Yearly Gross",
                                r['yearly_gross'], r['yearly_gross'] / u))
        sc.add_widget(divider())
        sc.add_widget(self._row("Tax Reliefs", r['taxable_income']))
        sc.add_widget(lbl(f"EPF Rate: {r['epf_rate']*100:.0f}%",
                          size=12, color=SUBTEXT))
        sc.add_widget(self._row("  Monthly EPF",  r['monthly_epf']))
        sc.add_widget(self._row("  Yearly EPF",   r['yearly_epf']))
        sc.add_widget(self._row("  Monthly SOCSO", r['monthly_socso']))
        sc.add_widget(self._row("  Yearly SOCSO",  r['yearly_socso']))
        if r['monthly_eis']:
            sc.add_widget(self._row("  Monthly EIS", r['monthly_eis']))
            sc.add_widget(self._row("  Yearly EIS",  r['yearly_eis']))
        sc.add_widget(divider())
        sc.add_widget(self._row("Taxable Income", r['taxable_income']))
        sc.bind(minimum_height=sc.setter("height"))
        c.add_widget(sc)

        # ── Tax result card ───────────────────────────────────────────────────
        tc = card()
        tc.add_widget(lbl("Tax", bold=True, color=ACCENT2, size=14))
        tc.add_widget(divider())
        tc.add_widget(self._row("Yearly Tax",
                                r['yearly_tax'], r['yearly_tax'] / u,
                                bold=True, color=RED))
        tc.add_widget(self._row("Monthly Tax",
                                float(r['monthly_tax']), r['monthly_tax'] / u,
                                bold=True, color=RED))
        tc.bind(minimum_height=tc.setter("height"))
        c.add_widget(tc)

        # ── Net salary card ───────────────────────────────────────────────────
        nc = card()
        nc.add_widget(lbl("Net Salary", bold=True, color=ACCENT2, size=14))
        nc.add_widget(divider())
        nc.add_widget(self._row("Yearly Net",
                                r['yearly_net'], r['yearly_net'] / u,
                                bold=True, color=GREEN))
        nc.add_widget(self._row("Monthly Net",
                                r['monthly_net'], r['monthly_net'] / u,
                                bold=True, color=GREEN))
        nc.bind(minimum_height=nc.setter("height"))
        c.add_widget(nc)

        # ── Breakdown card ────────────────────────────────────────────────────
        bc = card()
        bc.add_widget(lbl("Tax Bracket Breakdown", bold=True,
                          color=ACCENT2, size=14))
        bc.add_widget(divider())
        hrow = BoxLayout(size_hint_y=None, height=dp(28))
        hrow.add_widget(lbl("Bracket",  size=12, color=SUBTEXT, bold=True))
        hrow.add_widget(lbl("Rate",     size=12, color=SUBTEXT, bold=True, halign="center"))
        hrow.add_widget(lbl("Tax (RM)", size=12, color=SUBTEXT, bold=True, halign="right"))
        bc.add_widget(hrow)
        bc.add_widget(divider())
        for amt, rate, tax in r['breakdown']:
            row = BoxLayout(size_hint_y=None, height=dp(30))
            row.add_widget(lbl(f"RM {amt:,.0f}", size=12, color=TEXT))
            row.add_widget(lbl(f"{rate*100:.0f}%", size=12,
                               color=ACCENT2, halign="center"))
            row.add_widget(lbl(f"RM {tax:,.2f}", size=12,
                               color=TEXT, halign="right"))
            bc.add_widget(row)
        bc.add_widget(divider())
        total_row = BoxLayout(size_hint_y=None, height=dp(32))
        total_row.add_widget(lbl("TOTAL", size=13, bold=True, color=RED))
        total_row.add_widget(lbl("", size=12))
        total_row.add_widget(lbl(f"RM {r['yearly_tax']:,.2f}",
                                 size=13, bold=True, color=RED, halign="right"))
        bc.add_widget(total_row)
        bc.bind(minimum_height=bc.setter("height"))
        c.add_widget(bc)


# ─────────────────────────────────────────────────────────────────────────────
class TaxApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(InputScreen(name="input"))
        sm.add_widget(ResultsScreen(name="results"))
        return sm


if __name__ == "__main__":
    TaxApp().run()
