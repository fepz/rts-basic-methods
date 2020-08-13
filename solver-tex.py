from pylatex import Document, Section, Subsection, Subsubsection, Command, Math, Package, Alignat
from pylatex.basic import NewPage
from pylatex.utils import italic, NoEscape
from pylatex.base_classes import Environment, Container
from functools import reduce
import math
import argparse


rts_list = {'a': [(1, 3, 3), (1, 4, 4), (1, 6, 6)],
            'b': [(2, 4, 4), (1, 5, 5), (1, 7, 7)],
            'c': [(2, 4, 4), (1, 5, 5), (1, 6, 6), (1, 12, 12)],
            'd': [(2, 5, 5), (1, 7, 7), (2, 10, 10), (2, 17, 17)],
            'e': [(2, 5, 5), (1, 8, 8), (2, 10, 10), (2, 15, 15)],
            'f': [(2, 5, 5), (1, 6, 6), (1, 7, 7), (2, 10, 10), (2, 30, 30)],
            'g': [(6, 40, 40), (5, 50, 50), (10, 60, 60), (12, 70, 70), (10, 80, 80)],
            'h': [(10, 50, 50), (6, 60, 60), (8, 60, 60), (12, 80, 80), (7, 90, 90), (10, 100, 100)],
            'i': [(1, 4, 4), (1, 6, 6), (1, 8, 8), (1, 10, 10), (1, 12, 12), (1, 20, 20), (1, 22, 22), (2, 24, 24)],
            'j': [(7, 55, 55), (3, 66, 66), (2, 66, 66), (4, 66, 66), (1, 70, 70), (11, 77, 77), (3, 77, 77),
                  (7, 105, 105), (6, 110, 110), (18, 154, 154)],
            'k': [(1, 5, 5), (1, 6, 6), (1, 7, 7), (1, 10, 10), (1, 20, 20)],
            'l': [(1, 5, 5), (2, 7, 7), (1, 10, 10), (3, 15, 15)],
            'm': [(1, 4, 4), (2, 7, 7), (1, 9, 9), (1, 15, 15), (2, 20, 20)],
            'n': [(1, 5, 5), (3, 8, 8), (1, 12, 12), (1, 15, 15), (2, 20, 20)],
            'o': [(2, 5, 5), (1, 8, 8), (2, 12, 12), (2, 13, 13)],
            'p': [(1, 4, 4), (2, 7, 7), (2, 11, 11), (1, 15, 15,)]}


class Dmath(Environment):
    """A class to wrap LaTeX's breqn environment."""
    _latex_name = "dmath*"
    packages = [Package('breqn')]
    escape = False
    content_separator = "\n"


class Aligned(Environment):
    packages = [Package('amsmath')]
    escape = False
    content_separator = "\n"


def lcm(rts):
    """ rts hiperperiod (l.c.m) """
    periods = []
    for task in rts:
        periods.append(task[1])
    return reduce(lambda x, y: (x * y) // math.gcd(x, y), periods, 1)


def uf(rts):
    """ tasks utilization factor """
    fu = 0
    for task in rts:
        fu = fu + (float(task[0]) / float(task[1]))
    return fu


def liu_bound(rts):
    """ Evaluate rts schedulability using the Liu & Layland bound """
    u = uf(rts)
    bound = len(rts) * (pow(2, 1.0 / float(len(rts))) - 1)
    return [u, bound, u <= bound]


def bini_bound(rts):
    """ Evaluate rts schedulability using the hyperbolic bound """
    bound = 1
    for task in rts:
        bound *= ((float(task[0]) / float(task[1])) + 1)
    return [bound, bound <= 2.0]


def joseph_wcrt(rts, doc):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """

    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0][0]  # task 0 wcet

    with doc.create(Subsubsection("Tarea 1")):
        doc.append(Math(data=["t=0"], escape=False))
        doc.append(Math(data=["R_1=C_1={:d}".format(wcrt[0])], escape=False))

    for i, task in enumerate(rts[1:], 1):
        r = 0
        c, t, d = task[0], task[1], task[2]

        iter = 0
        cc = 0

        with doc.create(Subsubsection("Tarea {0:}".format(i+1))):
            doc.append(Math(data=["t^0={0:}".format(r)], escape=False))
            while schedulable:
                iter += 1
                w = 0
                l = ["{0:}".format(c)]
                l2 = ["t^{0:}=".format(iter)]
                for taskp in rts[:i]:
                    cp, tp = taskp[0], taskp[1]
                    w += math.ceil(float(r) / float(tp)) * cp
                    cc += 1
                    l.append("\\ceil*{\\frac{" + str(r) + '}{' + str(tp) + "}} }} {:0}".format(cp))
                l2.extend(['+'.join(map(str, l))])
                w = c + w
                l2.append("={:0}".format(w))
                l2.append("=t^{0:} \Rightarrow R_{1:}=t^{0:}={2:}".format(iter-1, i, r) if r == w else "\\neq t^{0:}".format(iter-1))
                doc.append(Math(data=l2, escape=False))
                if r == w:
                    break
                r = w
                if r > d:
                    schedulable = False

            wcrt[i] = r
            if not schedulable:
                break

        doc.append("Se necesitaron {0:} ciclos y {1:} calculos de techos.".format(iter, cc))

    return schedulable, wcrt


def rta_wcrt(rts, doc):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0][0]  # task 0 wcet

    with doc.create(Subsubsection("Tarea 1")):
        doc.append(Math(data=["t=0"], escape=False))
        doc.append(Math(data=["R_1=C_1={:d}".format(wcrt[0])], escape=False))

    for i, task in enumerate(rts[1:], 1):
        c, t, d = task[0], task[1], task[2]
        r = wcrt[i-1] + c
        cc = 0
        iter = 0
        with doc.create(Subsubsection("Tarea {0:}".format(i+1))):
            doc.append(Math(data=["t^0=R_{0:}+C_{1:}={2:}".format(i, i+1, r)], escape=False))
            while schedulable:
                iter += 1
                w = 0
                l = ["{0:}".format(c)]
                l2 = ["t^{0:}=".format(iter)]
                for taskp in rts[:i]:
                    cp, tp = taskp[0], taskp[1]
                    w += math.ceil(float(r) / float(tp)) * cp
                    cc += 1
                    l.append("\\ceil*{\\frac{" + str(r) + '}{' + str(tp) + "}} }} {:0}".format(cp))
                l2.extend(['+'.join(map(str, l))])
                w = c + w
                l2.append("={:0}".format(w))
                l2.append("=t^{0:} \Rightarrow R_{1:}=t^{0:}={2:}".format(iter-1, i, r) if r == w else "\\neq t^{0:}".format(iter-1))
                doc.append(Math(data=l2, escape=False))
                if r == w:
                    break
                r = w
                if r > d:
                    schedulable = False
            wcrt[i] = r
            if not schedulable:
                break

        doc.append("{0:} {1:} y {2:} {3:}.".format(iter, "iteraciones" if iter > 1 else "iteración", cc,
                                                   "techos" if cc > 1 else "techo"))

    return [schedulable, wcrt]


def add_rts(key, rts, doc):
    with doc.create(Section('STR ' + str(key))):
        doc.append(Math(data=["\Gamma("+str(len(rts))+")", '=', '\{', str(rts).strip('[]'), '\}'], escape=False))

        doc.append(Math(data=['H=', str(lcm(rts))]))

        with doc.create(Subsection("Factor de utilización")):
            a = ["FU", '=', '\sum_{i=1}^{'+str(len(rts))+'}\\frac{C_i}{T_i}', '=']
            s = []
            for task in rts:
                s.append("\\frac{" + str(task[0]) + '}{' + str(task[1]) + '}')
            a.extend(['+'.join(map(str, s)), '=', "{:.3f}".format(uf(rts))])
            doc.append(Math(data=a, escape=False))
            doc.append("El FU del sistema es de {:.0%}.".format(uf(rts)))

        with doc.create(Subsection('Cota de Liu')):
            liu = liu_bound(rts)
            a = ["n(2^{1/n}-1)".replace('n', str(len(rts))), '\\approx', "{:.3f}".format(liu[1])]
            a.extend(["\geq" if liu[2] else "\\ngeq", "{:.3f}".format(uf(rts))])
            doc.append(Math(data=a, escape=False))
            doc.append("Planificable según cota de Liu." if liu[2] else "No se puede garantizar la planificabilidad en base a la cota de Liu.")

        with doc.create(Subsection('Cota de Bini')):
            bini = bini_bound(rts)
            with doc.create(Dmath()):
                a = ["\prod_{i=1}^{n}".replace('n', str(len(rts))), "\\left(\\frac{C_i}{T_i}-1\\right)="]
                s = []
                for task in rts:
                    s.append("\\left(\\frac{"+str(task[0])+'}{'+str(task[1])+'}+1\\right)')
                a.extend(['+'.join(map(str, s)), '\\approx', "{:.3f}".format(bini[0])])
                a.extend(["\leq" if bini[1] else "\\nleq", "2"])
                #doc.append(Math(data=a, inline=True, escape=False))
                doc.append(" ".join(a))
            doc.append("Planificable según cota de Bini." if bini[1] else "No se puede garantizar la planificabilidad en base a la cota de Bini.")

        with doc.create(Subsection('Peores casos de tiempo de respuesta con Joseph')):
            schedulable, wcrt = joseph_wcrt(rts, doc)

        with doc.create(Subsection('Peores casos de tiempo de respuesta con RTA')):
            schedulable, wcrt = rta_wcrt(rts, doc)

        doc.append(NewPage())


def getargs():
    """ Command line arguments """
    parser = argparse.ArgumentParser(description="Basic methods for RTS schedulability and wcrt analysis.")
    parser.add_argument("rts", nargs="*", help="RTS to evaluate")
    return parser.parse_args()


def main():
    args = getargs()

    geometry_options = {"tmargin": "2cm", "lmargin": "2cm", "rmargin":"2cm", "bmargin":"2cm"}

    doc = Document('results', fontenc="T1", inputenc="utf8", geometry_options=geometry_options, document_options="fleqn")

    doc.packages.append(Package('amssymb'))
    doc.packages.append(Package('bookmark'))
    doc.packages.append(Package('mathtools'))

    doc.preamble.append(NoEscape(r'\DeclarePairedDelimiter{\ceil}{\lceil}{\rceil}'))
    doc.preamble.append(NoEscape(r'\DeclarePairedDelimiter{\floor}{\lceil}{\floor}'))

    doc.preamble.append(Command('title', 'Trabajo Práctico Nro. 1'))
    doc.preamble.append(Command('author', 'Francisco E. Páez (JTP)'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))


    if not args.rts:
        l = sorted(rts_list)
    else:
        l = args.rts

    for k in l:
        rts = rts_list[k]
        add_rts(k, rts, doc)

    doc.generate_tex()
    doc.generate_pdf()


if __name__ == '__main__':
    main()
