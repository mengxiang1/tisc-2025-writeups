# Solve equations from exfiltrated from timestamps from scrape.py

import itertools
import operator

def get_val(operand, sources, indices):
    if operand.startswith("l"):
        key, idx = (operand, f"{operand}_idx") if operand in ["l1", "l2"] else (operand, None)
        value = sources[key][indices[idx]] if idx else sources[key]
        if idx:
            indices[idx] += 1
        return value
    elif operand.startswith("r"):
        return sources['results'][int(operand[1:])]
    return sources[operand]

ops = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.floordiv}

def solve(equations):
    solutions = []
    op_combinations = itertools.product(*(ops.keys() if op == "?" else [op] for _, op, _ in equations))
    
    for l1_perm, l2_perm, op_perm in itertools.product(itertools.permutations(l1), itertools.permutations(l2), op_combinations):
        results = {}
        indices = {"l1_idx": 0, "l2_idx": 0}
        sources = {**fixed, 'l1': l1_perm, 'l2': l2_perm, 'results': results}
        
        for i, ((lhs, _, rhs), op) in enumerate(zip(equations, op_perm), 1):
            lv = get_val(lhs, sources, indices)
            rv = get_val(rhs, sources, indices)
            
            res = ops[op](lv, rv)
            if res < 0 or (op == "/" and (rv == 0 or lv % rv != 0)):
                break
            results[i] = res
        else:
            if 1000 <= results[len(equations)] <= 9999:
                solutions.append((l1_perm, l2_perm, op_perm, results))

    return solutions


fixed = {"l3": 152, "l4": 1007}
l1 = [1, 2, 4]
l2 = [11, 34]
equations = [
    [('l1', '+', 'l3'), ('l1', '*', 'l2'), ('r1', '?', 'r2'), ('r3', '?', 'l2'), ('l1', '?', 'r4'), ('r5', '-', 'l4')],
    [('l1', '*', 'l3'), ('l1', '+', 'l2'), ('r2', '?', 'l2'), ('r1', '-', 'r3'), ('l4', '?', 'r4'), ('l1', '?', 'r5')]
]

solutions = [solve(eq_set) for eq_set in equations]

common_sols = set(s[3][6] for s in solutions[0])
for sols in solutions[1:]:
    common_sols &= {s[3][6] for s in sols}

print(f"Solutions: {common_sols}")

for i, (solutions, eq_set) in enumerate(zip(solutions, equations), 1):
    print(f"\n=== Set {i} ===")
    unique = {}
    for sol in solutions:
        final = sol[3][6]
        if final in common_sols and final not in unique:
            unique[final] = sol

    for j, (l1_p, l2_p, op_p, res) in enumerate(unique.values(), 1):
        print(f"\nSolution {j}:")
        indices = {"l1_idx": 0, "l2_idx": 0}
        sources = {**fixed, 'l1': l1_p, 'l2': l2_p, 'results': res}
        for j, ((lhs, _, rhs), op) in enumerate(zip(eq_set, op_p), 1):
            lv = get_val(lhs, sources, indices)
            rv = get_val(rhs, sources, indices)
            print(f"{lv} {op} {rv} = {res[j]}")