import numpy as np

class OptimizationResult:
    def __init__(self, x, fun, success, message, nfev):
        self.x = x
        self.fun = fun
        self.success = success
        self.message = message
        self.nfev = nfev

def minimize(fun, x0, bounds=None, tol=1e-5, maxiter=1000):
    def is_within_bounds(x, bounds):
        if bounds is None:
            return True
        for xi, (lower, upper) in zip(x, bounds):
            if xi < lower or xi > upper:
                return False
        return True

    def random_perturbation(x, step_size=0.1):
        perturbation = np.random.uniform(-step_size, step_size, size=len(x))
        return x + perturbation

    x_best = np.array(x0)
    f_best = fun(x_best)

    for _ in range(maxiter):
        x_new = random_perturbation(x_best)

        # Enforce bounds
        if bounds.any():
            x_new = np.clip(x_new, [b[0] for b in bounds], [b[1] for b in bounds])

        if not is_within_bounds(x_new, bounds):
            continue

        f_new = fun(x_new)

        if f_new < f_best - tol:
            x_best = x_new
            f_best = f_new

    result = OptimizationResult(x_best, f_best, True, 'Optimization terminated successfully.', maxiter)
    # result = object()
    # result.x = x_best
    # result.fun = f_best
    # result.success = True
    # result.message = 'Optimization terminated successfully.'
    # result.nfev = maxiter

    return result

