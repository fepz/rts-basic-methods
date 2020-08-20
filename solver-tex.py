from pylatex import Document, Section, Subsection, Subsubsection, Command, Math, Package, Alignat
from pylatex.basic import NewPage, LineBreak, NewLine
from pylatex.utils import italic, NoEscape
from pylatex.base_classes import Environment, Container, Options
from simso.generator import task_generator
from functools import reduce
import math
import string
import argparse
import json
import os


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
        periods.append(task["t"])
    return reduce(lambda x, y: (x * y) // math.gcd(x, y), periods, 1)


def uf(rts):
    """ tasks utilization factor """
    fu = 0
    for task in rts:
        fu = fu + (float(task["c"]) / float(task["t"]))
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
        bound *= ((float(task["c"]) / float(task["t"])) + 1)
    return [bound, bound <= 2.0]


def joseph_wcrt(rts, doc):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """

    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["c"]  # task 0 wcet
    rts[0]["r"] = wcrt[0]

    with doc.create(Subsubsection("Tarea 1")):
        doc.append(Math(data=["R_1=C_1={:d}".format(wcrt[0])], escape=False))

    for i, task in enumerate(rts[1:], 1):
        r = 0
        c, t, d = task["c"], task["t"], task["d"]

        iter = 0
        cc = 0

        with doc.create(Subsubsection("Tarea {0:}".format(i+1))):
            doc.append(Math(data=["t^0={0:}".format(r)], escape=False))
            while schedulable:
                iter += 1
                w = 0

                for taskp in rts[:i]:
                    cp, tp = taskp["c"], taskp["t"]
                    w += math.ceil(float(r) / float(tp)) * cp
                    cc += 1

                w = c + w

                # Latex
                l2 = ["t^{0:}={1:}+".format(iter, c)]
                l2.extend(['+'.join(map(str,
                                        ["\\ceil*{{\\frac{{ {0:} }} {{ {1:} }} }} {2:}".format(r, task["t"], task["c"]) for task in rts[:i]]
                                        ))])
                l2.append("={:0}".format(w))
                if w <= d:
                    l2.append("=t^{0:} \Rightarrow R_{1:}=t^{2:}={3:}".format(iter - 1, i + 1, iter, r) if r == w else "\\neq t^{0:}".format(iter - 1))
                else:
                    l2.append(">D_{0:}".format(i+1))
                doc.append(Math(data=l2, escape=False))

                if r == w:
                    break
                r = w
                if r > d:
                    schedulable = False

            wcrt[i] = r

            doc.append("Se necesitaron {0:} ciclos y {1:} calculos de techos.".format(iter, cc))

            if not schedulable:
                doc.append(NewLine())
                doc.append("Sistema no planificable por RM/DM.")
                break

    return schedulable, wcrt


def rta_wcrt(rts, doc):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["c"]  # task 0 wcet
    rts[0]["r"] = wcrt[0]

    with doc.create(Subsubsection("Tarea 1")):
        doc.append(Math(data=["R_1=C_1={:d}".format(wcrt[0])], escape=False))

    for i, task in enumerate(rts[1:], 1):
        c, t, d = task["c"], task["t"], task["d"]
        r = wcrt[i-1] + c
        cc = 0
        iter = 0
        with doc.create(Subsubsection("Tarea {0:}".format(i+1))):
            doc.append(Math(data=["t^0=R_{{ {0:} }}+C_{{ {1:} }}={2:}".format(i, i+1, r)], escape=False))
            while schedulable:
                iter += 1
                w = 0
                for taskp in rts[:i]:
                    cp, tp = taskp["c"], taskp["t"]
                    w += math.ceil(float(r) / float(tp)) * cp
                    cc += 1
                w = c + w

                # Latex
                l2 = ["t^{0:}={1:}+".format(iter, c)]
                l2.extend(['+'.join(map(str,
                                        ["\\ceil*{{\\frac{{ {0:} }} {{ {1:} }} }} {2:}".format(r, task["t"], task["c"]) for task in rts[:i]]
                                        ))])
                l2.append("={:0}".format(w))
                if w <= d:
                    l2.append("=t^{0:} \Rightarrow R_{{ {1:} }}=t^{{ {2:} }}={3:}".format(iter - 1, i + 1, iter, r) if r == w else "\\neq t^{{ {0:} }}".format(iter - 1))
                else:
                    l2.append(">D_{{ {0:} }}".format(i+1))
                doc.append(Math(data=l2, escape=False))

                if r == w:
                    break
                r = w
                if r > d:
                    schedulable = False
            wcrt[i] = r
            task["r"] = r
            if not schedulable:
                break

        doc.append("{0:} {1:} y {2:} {3:}.".format(iter, "iteraciones" if iter > 1 else "iteración", cc,
                                                   "techos" if cc > 1 else "techo"))

    return [schedulable, wcrt]


def first_free_slot(rts, doc):
    """ Calcula primer instante que contiene un slot libre por subsistema """
    free = [0] * len(rts)
    for i, task in enumerate(rts, 0):
        r = task["r"] + task["c"] if i > 0 else task["c"]
        with doc.create(Subsubsection("Tarea {0:}".format(i+1))):
            data = ["t^0=R_{{ {0:} }}+C_{{ {1:} }}={2:}".format(i, i + 1, r)] if i > 0 else ["t^0=C_1={{ {0:} }}".format(r)]
            doc.append(Math(data=data, escape=False))
            iter = 0
            while True:
                iter += 1
                l = ["1"]
                l2 = ["t^{{ {0:} }}=".format(iter)]
                w = 0
                for taskp in rts[:i+1]:
                    c, t = taskp["c"], taskp["t"]
                    w += math.ceil(r / t) * c
                    l.append("\\ceil*{\\frac{" + str(r) + '}{' + str(t) + "}} }} {:0}".format(c))
                w = w + 1
                l2.extend(['+'.join(map(str, l))])
                l2.append("={:0}".format(w))
                l2.append("=t^{{ {0:} }}".format(iter-1) if r == w else "\\neq t^{{ {0:} }}".format(iter-1))
                doc.append(Math(data=l2, escape=False))
                if r == w:
                    break
                r = w

            doc.append("Primera unidad libre en [{0:}-{1:}].".format(r-1, r))
        free[i] = r
    return free


def calculate_k(rts, doc):
    """ Calcula el K de cada tarea (maximo retraso en el instante critico) """
    ks = [0] * len(rts)
    ks[0] = rts[0]["d"] - rts[0]["c"]
    rts[0]["k"] = rts[0]["d"] - rts[0]["c"]

    with doc.create(Subsubsection("Tarea 1")):
        doc.append("El máximo retraso para la tarea 1 es ")
        doc.append(Math(data=["K_1=D_1-C_1={0:}".format(rts[0]["k"])], escape=False, inline=True))
        doc.append(".")

    for i, task in enumerate(rts[1:], 1):
        r = 1
        k = 1
        c, t, d = task["c"], task["t"], task["d"]
        with doc.create(Subsubsection("Tarea {0:}".format(i+1))):
            iter = 0
            doc.append("Con ")
            doc.append(Math(data=["K_{{ {0:} }} = {1:}".format(i + 1, k)], escape=False, inline=True))
            while True:
                iter += 1
                w = 0
                l = ["{0:}".format(k)]
                l2 = ["t^{{ {0:} }}=".format(iter)]
                for taskp in rts[:i]:
                    cp, tp = taskp["c"], taskp["t"]
                    w += math.ceil(float(r) / float(tp)) * cp
                    l.append("\\ceil*{\\frac{" + str(r) + '}{' + str(t) + "}} }} {:0}".format(c))
                w = c + w + k
                l2.extend(['+'.join(map(str, l))])
                l2.append("={:0}".format(w))
                if w <= d:
                    l2.append("=t^{{ {0:} }}".format(iter-1) if r == w else "\\neq t^{{ {0:} }}".format(iter-1))
                else:
                    l2.append(">D_{{ {0:} }}".format(i+1))
                doc.append(Math(data=l2, escape=False))
                if r == w:
                    r = 1
                    k = k + 1
                    doc.append("Con ")
                    doc.append(Math(data=["K_{{ {0:} }} = {1:}".format(i + 1, k)], escape=False, inline=True))
                r = w
                if r > d:
                    break
            ks[i] = k - 1
            task["k"] = k - 1
            doc.append("El máximo retraso para la tarea {0:} es ".format(i+1))
            doc.append(Math(data=["K_{{ {0:} }}={1:}".format(i+1, task["k"])], escape=False, inline=True))
            doc.append(".")
    return ks


def wcrt(rts):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["c"]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        c, t, d = task["c"], task["t"], task["d"]
        r = wcrt[i - 1] + c
        while schedulable:
            w = 0
            for taskp in rts[:i]:
                cp, tp = taskp["c"], taskp["t"]
                w += math.ceil(float(r) / float(tp)) * cp
            w = c + w
            if r == w:
                break
            r = w
            if r > d:
                schedulable = False
        wcrt[i] = r
        if not schedulable:
            break
    return [schedulable, wcrt]


def gen_rts(params):

    rts_list = []

    for param in params:
        ntask, uf, mint, maxt = param["ntask"], param["uf"], param["mint"], param["maxt"]

        print("Generating RTS with params {0:}".format(param))

        sched_found = False
        while not sched_found:
            u = task_generator.gen_randfixedsum(1, ntask, uf)
            t = task_generator.gen_periods_uniform(ntask, 1, mint, maxt, round_to_int=True)
            rts = []
            for taskset in iter(task_generator.gen_tasksets(u, t)):
                for task in taskset:
                    c, t = task
                    rts.append({"c": math.ceil(c), "t": int(t), "d": int(t)})
            rts = sorted(rts, key=lambda k: k['t'])
            sched_found = wcrt(rts)[0]
            if sched_found:
                rts_list.append(rts)

    return rts_list


def add_rts_2(key, rts, doc):
    def free_slots(rts):
        """ Calcula primer instante que contiene un slot libre por subsistema """
        free = [0] * len(rts)
        for i, task in enumerate(rts, 0):
            r = 1
            while True:
                w = 0
                for taskp in rts[:i + 1]:
                    c, t = taskp["c"], taskp["t"]
                    w += math.ceil(float(r) / float(t)) * float(c)
                w = w + 1
                if r == w:
                    break
                r = w
            free[i] = r
        return free

    def calc_k(rts):
        """ Calcula el K de cada tarea (maximo retraso en el instante critico) """
        ks = [0] * len(rts)
        ks[0] = rts[0]["d"] - rts[0]["c"]

        for i, task in enumerate(rts[1:], 1):
            r = 1
            k = 1
            c, t, d = task["c"], task["t"], task["d"]
            while True:
                w = 0
                for taskp in rts[:i]:
                    cp, tp = taskp["c"], taskp["t"]
                    w += math.ceil(float(r) / float(tp)) * cp
                w = c + w + k
                if r == w:
                    r = 1
                    k = k + 1
                r = w
                if r > d:
                    break
            ks[i] = k - 1
        return ks

    with doc.create(Section("STR " + key)):
        doc.append(Math(data=["\Gamma("+str(len(rts))+")", '=', "\\left\\{",
                              ",".join("\\left({0:}, {1:}, {2:}\\right)".format(task["c"], task["t"], task["d"]) for task in rts),
                              "\\right\\}"], escape=False))
        doc.append(Math(data=[",".join(["R_{{ {0:} }}={1:}".format(i, r) for i, r in enumerate(wcrt(rts)[1], 1)])], escape=False))
        doc.append(Math(data=[",".join(["K_{{ {0:} }}={1:}".format(i, r) for i, r in enumerate(calc_k(rts), 1)])], escape=False))
        doc.append(Math(data=[",".join(["F_{{ {0:} }}=\\left[{1:},{2:}\\right]".format(i, int(r)-1, int(r)) for i, r in enumerate(free_slots(rts), 1)])], escape=False))


def add_rts(key, rts, doc):
    rts_uf = uf(rts)

    with doc.create(Section('STR ' + str(key))):
        ",".join("({0:}, {1:}, {2:}".format(task["c"], task["t"], task["d"]) for task in rts)

        doc.append(Math(data=["\Gamma("+str(len(rts))+")", '=', "\\left\\{",
                              ",".join("({0:}, {1:}, {2:})".format(task["c"], task["t"], task["d"]) for task in rts),
                              "\\right\\}"], escape=False))

        doc.append(Math(data=['H=', str(lcm(rts))]))

        with doc.create(Subsection("Factor de utilización")):
            a = ["FU", '=', '\sum_{i=1}^{'+str(len(rts))+'}\\frac{C_i}{T_i}', '=']
            s = []
            for task in rts:
                s.append("\\frac{" + str(task["c"]) + '}{' + str(task["t"]) + '}')
            a.extend(['+'.join(map(str, s)), '=', "{:.3f}".format(uf(rts))])
            doc.append(Math(data=a, escape=False))
            doc.append("El FU del sistema es de {:.00%}.".format(uf(rts)))

        with doc.create(Subsection('Cota de Liu')):
            liu = liu_bound(rts)
            a = ["n(2^{1/n}-1)".replace('n', str(len(rts))), '\\approx', "{:.3f}".format(liu[1])]
            a.extend(["\\geq" if liu[2] else "\\ngeq", "{:.3f}".format(uf(rts))])
            doc.append(Math(data=a, escape=False))
            doc.append("Planificable por RM según cota de Liu." if liu[2] else "No se puede garantizar la planificabilidad en RM en base a la cota de Liu.")
            doc.append(Math(data=["FU = {0:.3f}".format(rts_uf), " \\leq 1" if rts_uf <= 1 else " > 1"], escape=False))
            doc.append("Planificable por EDF según cota de Liu." if rts_uf <= 1 else "No planificable por EDF en base a la cota de Liu.")

        with doc.create(Subsection('Cota de Bini')):
            bini = bini_bound(rts)
            with doc.create(Dmath()):
                a = ["\prod_{i=1}^{n}".replace('n', str(len(rts))), "\\left(\\frac{C_i}{T_i}+1\\right)="]
                s = []
                for task in rts:
                    s.append("\\left(\\frac{"+str(task["c"])+'}{'+str(task["t"])+'}+1\\right)')
                a.extend(['+'.join(map(str, s)), '\\approx', "{:.3f}".format(bini[0])])
                a.extend(["\leq" if bini[1] else "\\nleq", "2"])
                #doc.append(Math(data=a, inline=True, escape=False))
                doc.append(" ".join(a))
            doc.append("Planificable según cota de Bini." if bini[1] else "No se puede garantizar la planificabilidad en base a la cota de Bini.")

        sched_joseph = False
        sched_rta = False

        with doc.create(Subsection('Peores casos de tiempo de respuesta con Joseph')):
            sched_joseph, _ = joseph_wcrt(rts, doc)

        with doc.create(Subsection('Peores casos de tiempo de respuesta con RTA')):
            sched_rta, _ = rta_wcrt(rts, doc)

        with doc.create(Subsection("Planificabilidad")):
            doc.append("Planificable por RM." if sched_joseph and sched_rta else "No se puede planificar por RM.")

        with doc.create(Subsection('Primera unidad libre')):
            if rts_uf < 1:
                first_free_slot(rts, doc)
            else:
                doc.append("Sistema {0:}.".format("saturado" if rts_uf == 1 else "sobresaturado"))

        with doc.create(Subsection('Máximo retraso desde el instante crítico')):
            calculate_k(rts, doc)

        doc.append(NewPage())


def getargs():
    """ Command line arguments """
    parser = argparse.ArgumentParser(description="Basic methods for RTS schedulability and wcrt analysis.")
    parser.add_argument("--params-file", type=argparse.FileType('r'), help="JSON file with RTS params.")
    parser.add_argument("--rts-file", type=argparse.FileType('r'), help="JSON file with RTS.")
    parser.add_argument("--rts", nargs="*", help="RTS to evaluate")
    parser.add_argument("--pdf-name", type=str, help="Name of the output PDF file(s). If topic is greater than one, it's appended to the filename.")
    parser.add_argument("--topics", type=int, default=1, help="Number of topics.")
    return parser.parse_args()


def generate_pdf(rts_list, pdf_name, topic=0):
    geometry_options = {"tmargin": "2cm", "lmargin": "2cm", "rmargin": "2cm", "bmargin": "2cm"}

    doc = Document(fontenc="T1", inputenc="utf8", geometry_options=geometry_options, document_options="fleqn")
    doc2 = Document(fontenc="T1", inputenc="utf8", geometry_options=geometry_options, document_options="fleqn")

    packages = [
        Package('hyperref', Options("pdftex", pdfauthor="IF025", pdftitle="TP1")),
        Package('amssymb'),
        Package('bookmark'),
        Package('mathtools')
    ]
    for package in packages:
        doc.packages.append(package)
        doc2.packages.append(package)

    # Use \ceil to enclose expressions
    doc.preamble.append(NoEscape(r'\DeclarePairedDelimiter{\ceil}{\lceil}{\rceil}'))
    doc.preamble.append(NoEscape(r'\DeclarePairedDelimiter{\floor}{\lceil}{\floor}'))

    doc.preamble.append(Command('title', "Trabajo Práctico Nro. 1 - Tema {0:}".format(topic)))
    doc.preamble.append(Command('date', NoEscape(r'\the\year{}')))
    doc.append(NoEscape(r'\maketitle'))

    doc2.preamble.append(Command('title', "Trabajo Práctico Nro. 1 - Tema {0:}".format(topic)))
    doc2.preamble.append(Command('date', NoEscape(r'\the\year{}')))
    doc2.append(NoEscape(r'\maketitle'))

    for k, rts in zip(string.ascii_lowercase, gen_rts(rts_list)):
        add_rts(k, rts, doc)
        add_rts_2(k, rts, doc2)
    doc.generate_pdf(filepath=pdf_name + "-soluciones")
    doc2.generate_pdf(filepath=pdf_name)


def main():
    args = getargs()

    if args.rts_file:
        with args.rts_file as file:
            rts_list = json.load(file)

            if not args.rts:
                l = sorted(rts_list)
            else:
                l = args.rts

            for k in l:
                rts = rts_list[k]
                #add_rts(k, rts, doc)

            #doc.generate_tex()
            #doc.generate_pdf()

    if args.params_file:
        with args.params_file as file:
            params_list = json.load(file)
            for topic in range(1, args.topics+1):
                print("Topic {0:} ...".format(topic))
                filepath = "{0:}-tema-{1:}".format(args.pdf_name if args.pdf_name else os.path.splitext(file.name)[0], topic)
                generate_pdf(params_list, filepath, topic=topic)
            print("Done!")


if __name__ == '__main__':
    main()
