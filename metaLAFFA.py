import argparse
from config import env
import subprocess
import config.operation as op
import config.cluster as cl

parser = argparse.ArgumentParser(description="Wrapper script to run the pipeline, ensuring that the shell environment for Snakemake is correct.")
parser.add_argument("--submission_wrapper", "-s", default=" ".join([op.python, cl.submission_wrapper]), help="The wrapper script to use to parse job settings, parse resource requests, and submit a job to the cluster (default: %(default)s)")
parser.add_argument("--jobscript", "-j", default=cl.jobscript, help="The job script to use when submitting an individual cluster job (default: %(default)s)")
parser.add_argument("--number_of_jobs", "-n", type=int, default=50, help="Number of jobs to have submitted to the cluster queue at any one time, or if running locally, the number of cores to use for running jobs in parallel (default: %(default)s).")
parser.add_argument("--wait", "-w", type=int, default=60, help="Number of seconds to wait after a job finishes before checking that the output exists. This can avoid Snakemake incorrectly marking a step as failed when a file might not be immediately visible due to network latency (default: %(default)s).")
parser.add_argument("--dryrun", "-d", action="store_true", help="If used, determine what steps would be performed and report to the user, but do not actually run the steps.")
parser.add_argument("--verbose", "-v", action="store_true", help="If used, run Snakemake in verbose mode to print the bodies of generated job scripts and additional running information.")
parser.add_argument("--local", "-l", action="store_true", help="If used, run metaLAFFA locally rather than on a cluster.")

args = parser.parse_args()

# Create the snakemake command and add options to it as specified by the arguments
command = [op.snakemake]
command += ["--snakefile", op.snakefile]
if not args.local:
    command += ["-c", args.submission_wrapper]
if not args.local:
    command += ["--js", args.jobscript]
command += ["-j", str(args.number_of_jobs)]
command += ["--latency-wait", str(args.wait)]
if args.dryrun:
    command += ["-n"]
if args.verbose:
    command += ["--verbose", "-p"]

# Run the snakemake command
subprocess.run(command, env=env)
