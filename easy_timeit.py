#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Copyright 2020 louie-github
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__all__ = ["timeit"]

import os
import sys
import warnings

from functools import partial
from typing import List, Tuple
from timeit import default_repeat, Timer


# Source: Lib/timeit.py
def _format_time(
    seconds: int,
    units: List[Tuple[int, str]] = [
        (1.0, "sec"),
        (0.001, "msec"),
        (1e-06, "µsec"),
        (1e-09, "nsec"),
    ],
    precision: int = 3,
):
    """Format a time in seconds to the nearest seconds unit.

    Taken from Lib/timeit.py:main with some simplifications and Python 3
    conversions. Underlying functionality is still the same.

    Args:
        seconds (int): The time, in seconds, to be formatted.
        units (List[Tuple[int, str]], optional):
            The scales and units to use when formatting the time. Must be in
            format [(scale: float, unit: str)] and sorted beginning from the
            largest time unit to the smallest time unit, e.g.
            [(1.0, "sec"), (0.001, "msec")].
            Defaults to the one used in timeit.main, or:
            [(1.0, "sec"), (0.001, "msec"), (1e-06, "µsec"), (1e-09, "nsec")],
        precision (int, optional):
            The number of decimal places to use when formatting the output.
            Defaults to 3.

    Returns:
        str:
            The formatted output string consisting of the scaled output and
            the seconds unit used, separated by a space. Similar to
            "0.251 msec" or "1.037 sec."
    """
    # Main code: so short, right? :>
    for scale, unit in units:
        if seconds >= scale:
            break
    return f"{(seconds / scale):.{precision}g} {unit}"


# Default settings from Lib/timeit.py
def timeit(
    number=None,
    repeat=default_repeat,
    units=None,
    precision=None,
    print_output=True,
    **timer_kwargs,
):
    """Implements timeit.timeit with extra features similar to timeit CLI.

    Implements a very similar function to timeit.timeit, except that the
    function works more similarly to running timeit on the command line, or:
    `python -m timeit [args...]`, where the number of loops is automatically
    calculated and the output is formatted to the nearest unit.

    A majority of code is grabbed straight from Lib/timeit.py.

    Example:
        $ python -m timeit -s "x = []" "x.append(1)"
        5000000 loops, best of 5: 49.1 nsec per loop

        $ python
        >>> :package:.timeit(setup="x = []", stmt="x.append(1)")
        5000000 loops, best of 5: 50.2 nsec per loop
        [0.2599583000000001, 0.2707282, 0.26281960000000004, 0.2509495999999998, 0.2524842999999999]

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
            using `python -m timeit`. Defaults to True.
        **timer_kwargs:
            All other arguments are passed along to timeit.Timer. See
            timeit.timer for more information.

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
    timer = Timer(**timer_kwargs)

    # Include the current directory, so that local imports work (sys.path
    # contains the directory of this script, rather than the current
    # directory)
    sys.path.insert(0, os.getcwd())

    # Main code, some is from Lib/timeit.py
    # Get number of loops from timer.autorange, where loops is the number of
    # loops so that the cumulative time taken reaches 0.2 seconds, if the
    # number of loops was not specified as an argument.
    if number is None:
        try:
            loops, _ = timer.autorange()
        except Exception:
            timer.print_exc()
            return False
    else:
        loops = number

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
