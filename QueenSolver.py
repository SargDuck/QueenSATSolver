import sys
import subprocess
import itertools

# Function to write a CNF file in DIMACS format.
def writeCNF(n, k, outputFile):
    # Helper functions to calculate the IDs used for the white and black queens respectively
    def wVar(i,j):
        return i*n + j + 1
    def bVar(i,j):
        return n*n + i*n + j + 1

    # List of clauses we will store
    clauses = []
    # Cell coords for the white and black queens respectively
    wCells = [(i,j) for i in range(n) for j in range(n)]
    bCells = [(i,j) for i in range(n) for j in range(n)]
    # Total cells on the chessboard
    totalCells = n*n

    # Constraints to ensure exactly k queens are placed on the board
    ## At most k queens
    for combi in itertools.combinations(wCells, k+1):
        clause = [-wVar(i,j) for (i,j) in combi]
        clauses.append(clause)
    for combi in itertools.combinations(bCells, k+1):
        clause = [-bVar(i,j) for (i,j) in combi]
        clauses.append(clause)
    ## At least k queens
    for combi in itertools.combinations(wCells, totalCells - k + 1):
        clause = [wVar(i, j) for (i, j) in combi]
        clauses.append(clause)
    for combi in itertools.combinations(bCells, totalCells - k + 1):
        clause = [bVar(i, j) for (i, j) in combi]
        clauses.append(clause)
        
    # Ensures no two queens attack each others
    for i in range(n):
        for j in range(n):
            wv = wVar(i,j)
            for jj in range(n):
                if jj != j:
                    bv = bVar(i,jj)
                    clauses.append([-wv, -bv])
            for ii in range(n):
                if ii != i:
                    bv = bVar(ii,j)
                    clauses.append([-wv, -bv])
            for d in range(-n+1, n):
                if d != 0:
                    ii = i + d
                    jj = j + d
                    if 0 <= ii < n and 0 <= jj < n:
                        bv = bVar(ii,jj)
                        clauses.append([-wv, -bv])
            for d in range(-n+1, n):
                if d != 0:
                    ii = i + d
                    jj = j - d
                    if 0 <= ii < n and 0 <= jj < n:
                        bv = bVar(ii,jj)
                        clauses.append([-wv, -bv])

    # Each cell can contain at most one queen
    for i in range(n):
        for j in range(n):
            wv = wVar(i,j)
            bv = bVar(i,j)
            clauses.append([-wv, -bv])

    # Writes the CNF file
    maxVar = 2*n*n
    with open(outputFile, "w") as f:
        f.write("p cnf {} {}\n".format(maxVar, len(clauses)))
        for c in clauses:
            f.write(" ".join(map(str, c)) + " 0\n")

# Function to solve the CNF file using glucose
def solveCNF(cnfFile, printStats = False):
    # Runs glucose on the CNF file
    result = subprocess.run(["glucose", "-model", cnfFile], capture_output=True, text=True)
    output = result.stdout.splitlines()
    sat = None
    # Stores the solution model if it is satisfiable
    model = []
    for l in output:
        # Finds whether the problem is satisfiable or not
        if l.startswith("s "):
            if "UNSATISFIABLE" in l:
                sat = False
            else: 
                sat = True
        if l.startswith("v "):
            # Readies the models to be read by the solution decoder
            parts = l.split()
            for p in parts[1:]:
                val = int(p)
                if val != 0:
                    model.append(val)
    if printStats:
        print("\nSolver Stats:")
        for l in output:
            if l.startswith("c "):
                print(l)
    return sat, model

# Function to decode the SAT model into a more presentable board representable
def decodeSolution(n, model):
    wPositions = set()
    bPositions = set()
    trueVars = set([v for v in model if v > 0])
    for i in range(n):
        for j in range(n):
            wv = i*n + j + 1
            bv = n*n + i*n + j + 1
            if wv in trueVars:
                wPositions.add((i,j))
            if bv in trueVars:
                bPositions.add((i,j))

    # Constructs the board
    board = []
    for i in range(n):
        row = []
        for j in range(n):
            if (i,j) in wPositions:
                row.append('W')
            elif (i,j) in bPositions:
                row.append('B')
            else:
                row.append('.')
        board.append(" ".join(row))
    return "\n".join(board)

# Main function for argument parsing and program execution
def main():
    import argparse
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Peaceably co-existing armies of queens")
    parser.add_argument("--n", type=int, help="size of the board")
    parser.add_argument("--k", type=int, help="number of queens per army")
    parser.add_argument("--cnf", type=str, help="output DIMACS CNF file path")
    parser.add_argument("--solve", action='store_true', help="solve the CNF")
    parser.add_argument("--stats", action='store_true', help="print solver stats")
    parser.add_argument("--instance", type=str, help="file containing instance n on first line and k on second line")
    
    args = parser.parse_args()

    # Parse n and k from the input file or cmd args
    if args.instance:
        with open(args.instance,"r") as f:
            lines = f.read().strip().splitlines()
            n = int(lines[0])
            k = int(lines[1])
    else:
        n = args.n
        k = args.k
    
    if not n or not k:
        print("Please specify n and k.")
        sys.exit(1)

    # Default CNF file name
    cnfFile = args.cnf if args.cnf else "tmp.cnf"
    # Generates the CNF file
    writeCNF(n, k, cnfFile)

    # Solves the problem if requested with "--solve"
    if args.solve:
        sat, model = solveCNF(cnfFile, printStats=args.stats)
        if sat is None:
            print("Error running solver.")
        elif sat:
            print("SAT")
            print(decodeSolution(n, model))
        else:
            print("UNSAT")


if __name__ == "__main__":
    main()
