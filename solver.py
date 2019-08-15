from __future__ import print_function
from functools import reduce
import math
import argparse

rts_list = {'a': [(1,3,3), (1,4,4), (1,6,6)],
            'b': [(2,4,4), (1,5,5), (1,7,7)],
            'c': [(2,4,4), (1,5,5), (1,6,6), (1,12,12)],
            'd': [(2,5,5), (1,7,7), (2,10,10), (2,17,17)],
            'e': [(2,5,5), (1,8,8), (2,10,10), (2,15,15)],
            'f': [(2,5,5), (1,6,6), (1,7,7), (2,10,10), (2,30,30)],
            'g': [(6,40,40), (5,50,50), (10,60,60), (12,70,70), (10,80,80)],
            'h': [(10,50,50), (6,60,60), (8,60,60), (12,80,80), (7,90,90), (10,100,100)],
            'i': [(1,4,4), (1,6,6), (1,8,8), (1,10,10), (1,12,12), (1,20,20), (1,22,22), (2,24,24)],
            'j': [(7,55,55), (3,66,66), (2,66,66), (4,66,66), (1,70,70), (11,77,77), (3,77,77), (7,105,105), (6,110,110), (18,154,154)],
            'k': [(1,5,5), (1,6,6), (1,7,7), (1,10,10), (1,20,20)],
            'l': [(1,5,5), (2,7,7), (1,10,10), (3,15,15)],
            'm': [(1,4,4), (2,7,7), (1,9,9), (1,15,15), (2,20,20)],
            'n': [(1,5,5), (3,8,8), (1,12,12), (1,15,15), (2,20,20)],
            'o': [(2,5,5), (1,8,8), (2,12,12), (2,13,13)],
            'p': [(1,4,4), (2,7,7), (2,11,11), (1,15,15,)]}
              

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


def round_robin(rts):
    """ Evaluate schedulability of the round robin algorithm """
    min_d = float("inf")
    sum_c = 0
    for task in rts:
        if task[2] < min_d:
            min_d = task[2]
        sum_c = sum_c + task[0]
    return [min_d >= sum_c, min_d, sum_c]


def liu_bound(rts):
    """ Evaluate rts schedulability using the Liu & Layland bound """
    u = uf(rts)
    bound = len(rts) * (pow(2, 1.0 / float(len(rts))) - 1)
    return [u, bound, u <= bound]

    
def bini_bound(rts):
    """ Evaluate rts schedulability using the hyperbolic bound """
    bound = 1
    for task in rts:
        bound *= ((float(task[0]) / float(task[1])) + 1 )
    return [bound, bound <= 2.0]
    
    
def joseph_wcrt(rts):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    wcrt = [0] * len(rts)
    schedulable = True
    wcrt[0] = rts[0][0]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        r = 0
        c, t, d = task[0], task[1], task[2]        
        while schedulable:
            w = 0
            for taskp in rts[:i]:
                cp, tp = taskp[0], taskp[1]                
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
    wcrt[0] = rts[0][0]  # task 0 wcet
    for i, task in enumerate(rts[1:], 1):
        c, t, d = task[0], task[1], task[2]
        r = wcrt[i-1] + c
        while schedulable:
            w = 0
            for taskp in rts[:i]:
                cp, tp = taskp[0], taskp[1]
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
                c, t = taskp[0], taskp[1]
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
    ks[0] = rts[0][1] - rts[0][0]
        
    for i, task in enumerate(rts[1:], 1):
        r = 1
        k = 1
        c, t, d = task[0], task[1], task[2]
        while True:
            w = 0
            for taskp in rts[:i]:
                cp, tp = taskp[0], taskp[1]                
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
    

def calculate_servers(rts):
    """ Calculate DS capacity for each priority level. """
    priorities = set([task[1] for task in rts])
        
    ks = calculate_k(rts)
    
    cds_list = []
    
    for tds in sorted(priorities):
        cds = [(float(k) / float(math.ceil(float(task[1]) / float(tds)))) for k, task in zip(ks, rts)]
        cds_list.append((tds, min(cds)))
        
    return cds_list


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
    
    for k in l:
        rts = rts_list[k]
        print("rts", k)
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
    
