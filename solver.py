import argparse
import sys
from functools import reduce
from math import ceil, gcd
from simso.generator import task_generator
from tabulate import tabulate
from files import get_from_file


def lcm(rts):
    """ Real-time system hiperperiod (l.c.m) """
    return reduce(lambda x, y: (x * y) // gcd(x, y), [task["T"] for task in rts], 1)


def uf(rts):
    """ Real-time system utilization factor """
    return sum([float(task["C"]) / float(task["T"]) for task in rts])


def round_robin(rts):
    """ Evaluate schedulability of the round robin scheduling algorithm """
    min_d = float("inf")
    sum_c = 0
    for task in rts:
        if task["D"] < min_d:
            min_d = task["D"]
        sum_c = sum_c + task["C"]
    return [min_d >= sum_c, min_d, sum_c]


def liu_bound(rts):
    """ Evaluate schedulability using the Liu & Layland bound """
    bound = len(rts) * (pow(2, 1.0 / float(len(rts))) - 1)
    return [bound, uf(rts) <= bound]


def bini_bound(rts):
    """ Evaluate schedulability using the hyperbolic bound """
    bound = reduce(lambda a, b: a*b, [float(task["C"]) / float(task["T"]) + 1 for task in rts])
    return [bound, bound <= 2.0]


def joseph_wcrt(rts):
    """ Evaluate schedulability using the Joseph & Pandya exact schedulability test """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["C"]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        t = 0
        while schedulable:
            w = task["C"] + sum([ceil(float(t) / float(taskp["T"]))*taskp["C"] for taskp in rts[:i]])
            if t == w:
                break
            t = w
            if t > task["D"]:
                schedulable = False
        wcrt[i] = t
        if not schedulable:
            break
    return [schedulable, wcrt]


def rta_wcrt(rts):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["C"]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        r = wcrt[i-1] + task["C"]
        while schedulable:
            w = task["C"] + sum([ceil(float(r) / float(taskp["T"]))*taskp["C"] for taskp in rts[:i]])
            if r == w:
                break
            r = w
            if r > task["D"]:
                schedulable = False
        wcrt[i] = r
        if not schedulable:
            break
    return [schedulable, wcrt]


def wcrt(rts):
    """ Calcula wcrt y planificabilidad con todos los metodos implementados """
    return {'joseph': joseph_wcrt(rts), 'rta': rta_wcrt(rts)}


def first_free_slot(rts):
    """ Calcula primer instante que contiene un slot libre por subsistema """
    free = [0] * len(rts)
    for i, task in enumerate(rts, 0):
        t = 0
        while True:
            w = 1 + sum([ceil(float(t) / float(taskp["T"]))*taskp["C"] for taskp in rts[:i+1]])
            if t == w:
                break
            t = w
        free[i] = t
    return free


def calculate_k(rts):
    """ Calcula el K de cada tarea (maximo retraso en el instante critico) """
    ks = [0] * len(rts)
    ks[0] = rts[0]["T"] - rts[0]["C"]

    for i, task in enumerate(rts[1:], 1):
        t = 0
        k = 1
        while t <= task["D"]:
            w = k + task["C"] + sum([ceil(float(t) / float(taskp["T"]))*taskp["C"] for taskp in rts[:i]])
            if t == w:
                k += 1
            t = w
        ks[i] = k - 1
    return ks

def calculate_y(rts):
    """ Calcula los tiempos de promoción de cada tarea para Dual Priority """
    wcrt = rta_wcrt(rts)[1]
    y = []
    for i, task in enumerate(zip(rts, wcrt), 1):
        y.append(task[0]["D"] - task[1])
    return y


def calculate_ps_bound(rts):
    u = uf(rts)
    bound = (len(rts)+1) * (pow(2, 1.0 / float(len(rts)+1)) - 1)
    return [((bound - u) * task["T"], task["T"]) for task in rts]


def calculate_ds_bound(rts):
    p = pow((uf(rts) / len(rts)) + 1, len(rts))
    uds = (2 - p) / ((2 * p) - 1)
    return [(uds * task["T"], task["T"]) for task in rts]


def calculate_ds_k(rts):
    """ Calculate DS capacity for each priority level. """
    def f(k, t, tds):
        return float(k) / (float(ceil(float(t) / float(tds))))
    ks = calculate_k(rts)
    cds_list = []
    for tds in [task["T"] for task in rts]:
        cds_list.append((min([f(k, task["T"], tds) for k, task in zip(ks, rts)]), tds))
    return cds_list


def mix_range(s):
    r = []
    for i in s.split(','):
        if '-' not in i:
            r.append(int(i))
        else:
            l, h = map(int, i.split('-'))
            r += range(l, h+1)
    return r


def generate_rts(param):
    while True:
        u = task_generator.gen_randfixedsum(1, param["ntask"], param["uf"])
        t = task_generator.gen_periods_uniform(param["ntask"], 1, param["mint"], param["maxt"], round_to_int=True)
        rts = []
        for taskset in iter(task_generator.gen_tasksets(u, t)):
            for task in taskset:
                c, t = task
                rts.append({"C": ceil(c), "T": int(t), "D": int(t)})
        rts = sorted(rts, key=lambda k: k['t'])
        if wcrt(rts)[0]:
            return rts


def getargs():
    """ Command line arguments """
    parser = argparse.ArgumentParser(description="Basic methods for RTS schedulability and WCRT analysis.")
    parser.add_argument("file", type=argparse.FileType('r'), default=sys.stdin, help="JSON file with RTS or RTS params.")
    parser.add_argument("--rts", type=str, default="0", help="RTS to evaluate")
    parser.add_argument("--table", action="store_true", default=False)
    parser.add_argument("--print-rts", action="store_true", default=False)
    parser.add_argument("--only-print-rts", action="store_true", default=False)
    return parser.parse_args()


def main():
    args = getargs()

    with args.file as file:
        #rts_in_file = json.load(file)
        #for rts in [rts_in_file[i] for i in mix_range(args.rts)] if args.rts else rts_in_file:
        for rts in get_from_file(file, mix_range(args.rts)):
            ptasks = rts["ptasks"]

            if args.print_rts or args.only_print_rts:
                column_names = ptasks[0].keys()
                print(tabulate(ptasks, headers="keys", tablefmt="simple"))

            if args.only_print_rts:
                continue

            rm_schedulable = rta_wcrt(ptasks)[0]

            liu_bound_result = liu_bound(ptasks)
            bini_bound_result = bini_bound(ptasks)

            results = [
                ("h", lcm(ptasks)),
                ("uf", uf(ptasks)),
                ("liu", liu_bound_result),
                ("bini", bini_bound_result),
                ("wcrt", wcrt(ptasks)),
                ("edf", (uf(ptasks) <= 1)),
                ("free", first_free_slot(ptasks) if rm_schedulable else "No planificable"),
                ("k", calculate_k(ptasks)),
                ("y", calculate_y(ptasks)),
                ("rr", round_robin(ptasks)),
                ("ps (bound)", calculate_ps_bound(ptasks) if liu_bound_result[1] else "No aplica"),
                ("ds (bound)", calculate_ds_bound(ptasks) if bini_bound_result[1] else "No aplica"),
                ("ds (k)", calculate_ds_k(ptasks))
            ]
            if args.table:
                print(tabulate(results, tablefmt="grid"))
            else:
                for result in results:
                    key, value = result
                    print(f"{key}\t{value}")


if __name__ == '__main__':
    main()
