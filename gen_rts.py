from simso.generator import task_generator
import math

def rta_wcrt(rts):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0]["c"]  # task 0 wcet
    rts[0]["r"] = rts[0]["c"]
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
        task["r"] = r
        if not schedulable:
            break
    return [schedulable, wcrt]


def gen_rts():
    params = [(4, .8, 3, 40), (5, .9, 3, 50), (5, .95, 5, 60)]
    rts_list = []

    for param in params:
        ntask, uf, mint, maxt = param

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
            sched_found = rta_wcrt(rts)[0]
            if sched_found:
                rts_list.append(rts)

    for rts in rts_list:
        print(rts)

if __name__ == '__main__':
    gen_rts()
