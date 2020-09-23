from functools import reduce
from simso.generator import task_generator
import math
import json
import argparse
from tabulate import tabulate


def lcm(rts):
    """ Real-time system hiperperiod (l.c.m) """
    periods = []
    for task in rts:
        periods.append(task["t"])
    return reduce(lambda x, y: (x * y) // math.gcd(x, y), periods, 1)


def uf(rts):
    """ Real-time system utilization factor """
    fu = 0
    for task in rts:
        fu = fu + (float(task["c"]) / float(task["t"]))
    return fu


def round_robin(rts):
    """ Evaluate schedulability of the round robin algorithm """
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
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["c"]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        r = 0
        c, t, d = task["c"], task["t"], task["d"]
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


def rta_wcrt(rts):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["c"]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        c, t, d = task["c"], task["t"], task["d"]
        r = wcrt[i-1] + c
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


def wcrt(rts):
    """ Calcula wcrt y planificabilidad con todos los metodos implementados """
    results = {'joseph': joseph_wcrt(rts), 'rta': rta_wcrt(rts)}
    return results


def first_free_slot(rts):
    """ Calcula primer instante que contiene un slot libre por subsistema """
    free = [0] * len(rts)
    for i, task in enumerate(rts, 0):
        r = 1        
        while True:
            w = 0
            for taskp in rts[:i+1]:
                c, t = taskp["c"], taskp["t"]
                w += math.ceil(float(r) / float(t)) * float(c)
            w = w + 1
            if r == w:
                break
            r = w            
        free[i] = r
    return free
    
    
def calculate_k(rts):
    """ Calcula el K de cada tarea (maximo retraso en el instante critico) """
    ks = [0] * len(rts)
    ks[0] = rts[0]["t"] - rts[0]["c"]
        
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
                k = k + 1
            r = w
            if r > d:
                break
        ks[i] = k - 1
    return ks


def calculate_ds_bound(rts):
    p = pow((uf(rts) / len(rts)) + 1, len(rts))
    uds = (2 - p) / ((2 * p) - 1)
    return [(uds * task["t"], task["t"]) for task in rts]


def calculate_ds_k(rts):
    """ Calculate DS capacity for each priority level. """
    priorities = set([task["t"] for task in rts])
        
    ks = calculate_k(rts)
    
    cds_list = []
    
    for tds in sorted(priorities):
        cds = [(float(k) / float(math.ceil(float(task["t"]) / float(tds)))) for k, task in zip(ks, rts)]
        cds_list.append((min(cds), tds))
        
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
    sched_found = False
    while not sched_found:
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

            print("rts", rts)
            print("h:    ", lcm(rts))
            print("uf:   ", uf(rts))
            print("liu:  ", liu_bound(rts))
            print("bini: ", bini_bound(rts))
            print("wcrt:  ", wcrt(rts))
            print("edf:  ", (uf(rts) <= 1))
            print("free: ", first_free_slot(rts))
            print("k:    ", calculate_k(rts))
            print("rr:   ", round_robin(rts))
            print("cds:  ", calculate_servers(rts))
    
    
if __name__ == '__main__':
    main()
