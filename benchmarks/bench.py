"""Micro-benchmark helper for Astra build and execution timings."""

import subprocess, sys, time

def run(cmd):
    """Run a subprocess command and return elapsed wall-clock seconds.

    Parameters:
        cmd: Subprocess argument vector.

    Returns:
        Seconds elapsed while the command executed.
    """
    t=time.time(); subprocess.check_call(cmd); return time.time()-t

if __name__=='__main__':
    arixa = run([sys.executable, '-m', 'astra.cli', 'build', 'examples/fib.arixa', '-o', 'build/fib.py'])
    py = run([sys.executable, 'build/fib.py'])
    print({'arixa_build_s':arixa, 'arixa_run_s':py, 'c_estimate_note':'compile C analog separately', 'rust_estimate_note':'compile Rust analog separately'})
