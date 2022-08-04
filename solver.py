from functools import reduce
from simso.generator import task_generator
from math import ceil
import json
import argparse
from tabulate import tabulate


def lcm(rts):
    """ Real-time system hiperperiod (l.c.m) """
    return reduce(lambda x, y: (x * y) // math.gcd(x, y), [task["t"] for task in rts], 1)


def uf(rts):
    """ Real-time system utilization factor """
    return sum([float(task["c"]) / float(task["t"]) for task in rts])


def round_robin(rts):
    """ Evaluate schedulability of the round robin scheduling algorithm """
    min_d = float("inf")
    sum_c = 0
    for task in rts:
        if task["d"] < min_d:
            min_d = task["d"]
        sum_c = sum_c + task["c"]
    return [min_d >= sum_c, min_d, sum_c]


def liu_bound(rts):
    """ Evaluate schedulability using the Liu & Layland bound """
    bound = len(rts) * (pow(2, 1.0 / float(len(rts))) - 1)
    return [bound, uf(rts) <= bound]


def bini_bound(rts):
    """ Evaluate schedulability using the hyperbolic bound """
    bound = reduce(lambda a, b: a*b, [float(task["c"]) / float(task["t"]) + 1 for task in rts])
    return [bound, bound <= 2.0]


def joseph_wcrt(rts):
    """ Evaluate schedulability using the Joseph & Pandya exact schedulability test """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["c"]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        t = 0
        while schedulable:
            w = task["c"] + sum([ceil(float(t) / float(taskp["t"]))*taskp["c"] for taskp in rts[:i]])
            if t == w:
                break
            t = w
            if t > task["d"]:
                schedulable = False
        wcrt[i] = t
        if not schedulable:
            break
    return [schedulable, wcrt]


def rta_wcrt(rts):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["c"]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        r = wcrt[i-1] + task["c"]
        while schedulable:
            w = task["c"] + sum([ceil(float(r) / float(taskp["t"]))*taskp["c"] for taskp in rts[:i]])
            if r == w:
                break
            r = w
            if r > task["d"]:
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
            w = 1 + sum([ceil(float(t) / float(taskp["t"]))*taskp["c"] for taskp in rts[:i+1]])
            if t == w:
                break
            t = w
        free[i] = t
    return free


def calculate_k(rts):
    """ Calcula el K de cada tarea (maximo retraso en el instante critico) """
    ks = [0] * len(rts)
    ks[0] = rts[0]["t"] - rts[0]["c"]

    for i, task in enumerate(rts[1:], 1):
        t = 0
        k = 1
        while t <= task["d"]:
            w = k + task["c"] + sum([ceil(float(t) / float(taskp["t"]))*taskp["c"] for taskp in rts[:i]])
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
        y.append(task[0]["d"] - task[1])
    return y


def calculate_ps_bound(rts):
    u = uf(rts)
    bound = (len(rts)+1) * (pow(2, 1.0 / float(len(rts)+1)) - 1)
    return [((bound - u) * task["t"], task["t"]) for task in rts]


def calculate_ds_bound(rts):
    p = pow((uf(rts) / len(rts)) + 1, len(rts))
    uds = (2 - p) / ((2 * p) - 1)
    return [(uds * task["t"], task["t"]) for task in rts]


def calculate_ds_k(rts):
    """ Calculate DS capacity for each priority level. """
    def f(k, t, tds):
        return float(k) / (float(ceil(float(t) / float(tds))))
    ks = calculate_k(rts)
    cds_list = []
    for tds in [task["t"] for task in rts]:
        cds_list.append((min([f(k, task["t"], tds) for k, task in zip(ks, rts)]), tds))
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
                rts.append({"c": math.ceil(c), "t": int(t), "d": int(t)})
        rts = sorted(rts, key=lambda k: k['t'])
        if wcrt(rts)[0]:
            return rts


def getargs():
    """ Command line arguments """
    parser = argparse.ArgumentParser(description="Basic methods for RTS schedulability and WCRT analysis.")
    parser.add_argument("file", type=argparse.FileType('r'), help="JSON file with RTS or RTS params.")
    parser.add_argument("--rts", type=str, help="RTS to evaluate")
    return parser.parse_args()


def main():
    args = getargs()

    with args.file as file:
        rts_in_file = json.load(file)
        for rts in [rts_in_file[i] for i in mix_range(args.rts)] if args.rts else rts_in_file:
            if type(rts) is list:
                for task in rts:
                    if "d" not in task:
                        task["d"] = task["t"]
            if type(rts) is dict:
                rts = generate_rts(rts)

            print("RTS: {0:}".format(rts))
            results = [
                ("h", lcm(rts)),
                ("uf", uf(rts)),
                ("liu", liu_bound(rts)),
                ("bini", bini_bound(rts)),
                ("wcrt", wcrt(rts)),
                ("edf", (uf(rts) <= 1)),
                ("free", first_free_slot(rts)),
                ("k", calculate_k(rts)),
                ("y", calculate_y(rts)),
                ("rr", round_robin(rts)),
                ("ps (bound)", calculate_ps_bound(rts)),
                ("ds (bound)", calculate_ds_bound(rts)),
                ("ds (k)", calculate_ds_k(rts))
            ]
            print(tabulate(results, tablefmt="grid"))


if __name__ == '__main__':
    main()
