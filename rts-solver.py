from simso.generator import task_generator
import math
import argparse
import json


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


def mix_range(s):
    r = []
    for i in s.split(','):
        if '-' not in i:
            r.append(int(i))
        else:
            l, h = map(int, i.split('-'))
            r += range(l, h+1)
    return r


def getargs():
    """ Command line arguments """
    parser = argparse.ArgumentParser(description="Basic methods for RTS schedulability and WCRT analysis.")
    parser.add_argument("file", type=argparse.FileType('r'), help="JSON file with RTS or RTS params.")
    parser.add_argument("--rts", type=str, help="RTS to evaluate")
    parser.add_argument("--pdf-name", type=str, help="Name of the output PDF file(s). If topic is greater than one, it's appended to the filename.")
    parser.add_argument("--topics", type=int, default=1, help="Number of topics.")
    return parser.parse_args()


def main():
    args = getargs()

    with args.file as file:
        rts_list = json.load(file)
        for rts in [rts_list[i] for i in mix_range(args.rts)] if args.rts else rts_list:
            if type(rts) is list:
                print(rts)
            if type(rts) is dict:
                print(generate_rts(rts))


if __name__ == '__main__':
    main()
