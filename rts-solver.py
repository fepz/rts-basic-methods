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


def generate_rts(params):
    rts_list = []

    for id, param in params.items():
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


def getargs():
    """ Command line arguments """
    parser = argparse.ArgumentParser(description="Basic methods for RTS schedulability and WCRT analysis.")
    parser.add_argument("--params-file", type=argparse.FileType('r'), help="JSON file with RTS params.")
    parser.add_argument("--rts-file", type=argparse.FileType('r'), help="JSON file with RTS.")
    parser.add_argument("--rts", nargs="*", help="RTS to evaluate")
    parser.add_argument("--pdf-name", type=str, help="Name of the output PDF file(s). If topic is greater than one, it's appended to the filename.")
    parser.add_argument("--topics", type=int, default=1, help="Number of topics.")
    return parser.parse_args()


def main():
    args = getargs()

    if args.rts_file:
        with args.rts_file as file:
            rts_list = json.load(file)

            if type(rts_list) is dict:
                if args.rts:
                    unwanted = set(rts_list) - set(args.rts)
                    for unwanted_key in unwanted:
                        rts_list.pop(unwanted_key, None)

                for key, rts in rts_list.items():
                    print(rts)

            if type(rts_list) is list:
                for rts in rts_list:
                    print(rts)

    if args.params_file:
        with args.params_file as file:
            params_list = json.load(file)
            for rts in generate_rts(params_list):
                print(rts)


if __name__ == '__main__':
    main()
