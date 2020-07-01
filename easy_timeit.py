#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import warnings

from functools import partial
from timeit import default_repeat, default_timer, Timer


# Source: Lib/timeit.py
def _format_time(
    seconds,
    units=[(1e-09, "nsec"), (1e-06, "µsec"), (0.001, "msec"), (1.0, "sec")],
    precision=3,
):
    for scale, unit in units:
        if seconds >= scale:
            break
    return f"{(seconds / scale):.{precision}g} {unit}"


# Default settings from Lib/timeit.py
def timeit(
    stmt="pass",
    setup="pass",
    timer=default_timer,
    number=None,
    repeat=default_repeat,
    globals=None,
    units=None,
    precision=None,
    print_output=True,
):
    """Implements timeit.timeit with extra features similar to timeit CLI.

    Implements a very similar function to timeit.timeit, except that the
    function works more similarly to running timeit on the command line, or:
    `python -m timeit [args...]`, where the number of loops is automatically
    calculated and the output is formatted to the nearest unit.

    Example:
        $ python -m timeit -s "x = []" "x.append(1)"
        5000000 loops, best of 5: 49.1 nsec per loop

        $ python
        >>> :package:.timeit(setup="x = []", stmt="x.append(1))

    Args:
        number (int, optional):
            The number of times to run the code when timing it. Passed along to
            Timer.repeat(). If this is not specified, then it will be
            determined by Timer.autorange(), where number will be the smallest
            number required for the cumulative time taken to reach 0.2 seconds.
        repeat (int, optional):
            Passed to Timer.repeat; how many times to repeat the timing
            function, given the number of loops. Defaults to using
            timeit.default_repeat
        units (List[Tuple], optional):
            The units to use when formatting times. Defaults to None, in which
            case the default argument in _format_time is used. See _format_time
            for more details.
        precision (int, optional):
            The number of decimal places of precision to use for the output.
            Defaults to None, in which case the default value of _format_time
            is used. See _format_time for more details.
        print_output (bool, optional):
            Whether to print the output of the timings in a similar format to
            the using `python -m timeit`. Defaults to True.

    Returns:
        List[Int]: Raw timings per repetition, not per loop.
            The raw timings per repetition, when running the code with the
            either the given or determined number of loops. Returns cumulative
            time, rather than per-loop time.
    """
    # Create format_time function, removing arguments if None
    format_time_kwargs = (("units", units), ("precision", precision))
    format_time_kwargs = {k: v for k, v in format_time_kwargs if v is not None}
    format_time = partial(_format_time, **format_time_kwargs)
    # Suppress printing if specified
    if print_output:
        printfunc = print
    else:
        printfunc = lambda *a, **k: None  # noqa: E731

    # Set up Timer instances
    timer = Timer(stmt=stmt, setup=setup, timer=timer, globals=globals)

    # Include the current directory, so that local imports work (sys.path
    # contains the directory of this script, rather than the current
    # directory)
    sys.path.insert(0, os.getcwd())

    # Main code, some is from Lib/timeit.py
    # Get number of loops from timer.autorange, where loops is the number of
    # loops so that the cumulative time taken reaches 0.2 seconds.
    try:
        loops, _ = timer.autorange()
    except Exception:
        timer.print_exc()
        return False

    # Main timing code
    try:
        raw_timings = timer.repeat(repeat, loops)
    except Exception:
        timer.print_exc()
        return False

    # Get the timings per loop
    timings = [timing / loops for timing in raw_timings]

    best = min(timings)
    worst = max(timings)

    # Warn if deviation is too large
    if worst >= best * 4:
        warnings.warn_explicit(
            "The test results are likely unreliable. "
            f"The worst time ({format_time(worst)}) was more than four times "
            f"slower than the best time ({format_time(best)}).",
            UserWarning,
            "",
            0,
        )

    # Print formatted output
    s = "s" if loops != 1 else ""  # Correct plural grammar
    printfunc(f"{loops} loop{s}, best of {repeat}: {format_time(best)} per loop")

    return raw_timings
