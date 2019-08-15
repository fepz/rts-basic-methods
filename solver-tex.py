from pylatex import Document, Section, Subsection, Command, Math
from pylatex.utils import italic, NoEscape
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


def add_rts(rts, doc):
    with doc.create(Section('STR')):
        doc.append(Math(data=['\Gamma('+str(len(rts))+')', '=', '\{', str(rts).strip('[]'), '\}'], escape=False))

        a = ['FU','=','\sum_{i=1}^'+str(len(rts))+'\\frac{C_i}{T_i}','=']
        s = []
        for task in rts:
            s.append("\\frac{"+str(task[0])+'}{'+str(task[1])+'}')
        a.extend(['+'.join(map(str, s)), '=', str(uf(rts))])
        doc.append(Math(data=a, escape=False))

        liu = liu_bound(rts)
        a = ["n(2^{1/n}-1)".replace('n', str(len(rts))), '=', str(liu[1])]
        doc.append(Math(data=a, escape=False))


def fill_document(doc):
    with doc.create(Section('A section')):
        doc.append('Some regular text and some ')
        doc.append(italic('italic text. '))

        with doc.create(Subsection('A subsection')):
            doc.append('Also some crazy characters: $&#{}')


def getargs():
    """ Command line arguments """
    parser = argparse.ArgumentParser(description="Basic methods for RTS schedulability and wcrt analysis.");
    parser.add_argument("rts", nargs="*", help="RTS to evaluate");
    return parser.parse_args();


def main():
    args = getargs();

    if not args.rts:
        l = sorted(rts_list)
    else:
        l = args.rts

    doc = Document('results', fontenc="T1", inputenc="utf8")

    doc.preamble.append(Command('title', 'Trabajo Práctico Nro. 1'))
    doc.preamble.append(Command('author', 'Francisco E. Páez (JTP)'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))

    #fill_document(doc)
    add_rts(rts_list['a'], doc)
    add_rts(rts_list['b'], doc)

    doc.generate_tex()
    print(doc.dumps())


if __name__ == '__main__':
    main()

