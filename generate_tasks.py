import argparse
import sys
from simso.core import Model
from simso.configuration import Configuration
from simso.generator.task_generator import UUniFastDiscard, gen_periods_uniform, gen_tasksets

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--min-t", type=int, default=5)
    parser.add_argument("--max-t", type=int, default=50)
    parser.add_argument("--set", type=int, default=1)
    parser.add_argument("--max-uf", type=float, default=.75)
    return parser.parse_args()

args = getargs()

u_list = UUniFastDiscard(args.n, args.max_uf, args.set)

t_list_unsorted = gen_periods_uniform(args.n, args.set, args.min_t, args.max_t, True)

t_list = []
for periods in t_list_unsorted:
    t_list.append(sorted(periods))

gen_task_sets = gen_tasksets(u_list, t_list)

for task_set in gen_task_sets:
    print(len(task_set))
    for task in task_set:
        c = round(task[0])
        if c == 0:
            c = 1
        print(f"{c} {int(task[1])} {int(task[1])}")
