#!/net/borenstein/vol1/PROGRAMS/python2/bin/python
# Author: Alex Eng
# Date: 11/30/2017

NUM_LINES_PER_READ = 4
READ_NAME_LINE = 0
QUALITY_LINE = 3

import argparse,sys
from file_handling import *
from fastq_summarizing import *
from future import *

# Parse command line arguments
parser = argparse.ArgumentParser(description="Summarizes quality read filtering")
parser.add_argument("original_r1_fastq", help="Pre-quality filtered R1 fastq file to determine the origin of new singletons")
parser.add_argument("original_r2_fastq", help="Pre-quality filtered R2 fastq file to determine the origin of new singletons")
parser.add_argument("filtered_r1_fastq", help="Filtered R1 fastq file for which to summarize quality filtering")
parser.add_argument("filtered_r2_fastq", help="Filtered R2 fastq file for which to summarize quality filtering")
parser.add_argument("filtered_new_singleton_fastq", help="Filtered fastq file of new singleton reads for which to summarize quality filtering")
parser.add_argument("filtered_old_singleton_fastq", help="Filtered fastq file of old singleton reads for which to summarize quality filtering")
parser.add_argument("--output", "-o", help="File to write output to (default: print to standard output)")
args = parser.parse_args()

# Set output stream
output = sys.stdout
if args.output:
    output = open(args.output, "w")

# Print the column names for the quality filtering summary file
output.write("\t".join(["filtered_fastq_file", "post_quality_filtering_paired_reads", "post_quality_filtering_paired_average_read_length", "post_quality_filtering_paired_average_base_quality", "post_quality_filtering_singleton_reads", "post_quality_filtering_singleton_average_read_length", "post_quality_filtering_singleton_average_base_quality"]) + "\n")

# Parse the new singleton file to get the read names of the new singletons
new_singletons = set()
f = custom_read(args.filtered_new_singleton_fastq)
line = f.readline()
line_count = 0
while line != "":

    # If we're on the first line of a read, then we found another read to add to the set of new singleton read names
    if line_count == READ_NAME_LINE:
        new_singletons.add(line.strip())

    # Now update our counter for the current line in the read's info
    line_count += 1
    line_count = line_count % NUM_LINES_PER_READ
    line = f.readline()
f.close()

# Get the stats for the filtered R1 FASTQ file
r1_read_count, r1_average_read_length, r1_average_base_quality = get_fastq_stats(args.filtered_r1_fastq)

# Get the stats for the filtered R2 FASTQ file
r2_read_count, r2_average_read_length, r2_average_base_quality = get_fastq_stats(args.filtered_r2_fastq)

# Get the stats for the filtered singleton FASTQ file
old_singleton_read_count, old_singleton_average_read_length, old_singleton_average_base_quality = get_fastq_stats(args.filtered_old_singleton_fastq)

# Parse the unfiltered R1 fastq to determine how many new singletons came from the R1 fastq and their read length and base quality stats
r1_new_singleton_read_count = 0
r1_new_singleton_base_count = 0
r1_new_singleton_total_quality_score = 0
f = custom_read(args.original_r1_fastq)
line = f.readline()
line_count = 0
match = False
while line != "":

    # If we're on the read name line, then check it's name against the new singletons
    if line_count == READ_NAME_LINE:

        # If we found a match, set the flag so we know to record its read length and base quality
        if line.strip() in new_singletons:
            r1_new_singleton_read_count += 1
            match = True

    # Otherwise, if we are in a matched read and at the quality score line, record the read length and quality score info
    elif match and line_count == QUALITY_LINE:
        r1_new_singleton_base_count += len(line.strip())
        r1_new_singleton_total_quality_score += sum(get_base_quality_vector(line.strip()))

    # Now update our counter for the current line in the read's info
    line_count += 1
    line_count = line_count % NUM_LINES_PER_READ
    line = f.readline()
f.close()

# Parse the unfiltered R2 fastq to determine how many new singletons came from the R2 fastq and their read length and base quality stats
r2_new_singleton_read_count = 0
r2_new_singleton_base_count = 0
r2_new_singleton_total_quality_score = 0
f = custom_read(args.original_r2_fastq)
line = f.readline()
line_count = 0
match = False
while line != "":

    # If we're on the first line of a read, then check it's name against the new singletons
    if line_count == READ_NAME_LINE:

        # If we found a match, set the flag so we know to record its read length and base quality
        if line.strip() in new_singletons:
            r2_new_singleton_read_count += 1
            match = True

    # Otherwise, if we are in a matched read and at the quality score line, record the read length and quality score info
    elif match and line_count == QUALITY_LINE:
        r2_new_singleton_base_count += len(line.strip())
        r2_new_singleton_total_quality_score += sum(get_base_quality_vector(line.strip()))

    # Now update our counter for the current line in the read's info
    line_count += 1
    line_count = line_count % NUM_LINES_PER_READ
    line = f.readline()
f.close()

# Print the quality filtering summary for this sample
output.write("\t".join([args.filtered_r1_fastq, str(r1_read_count), str(r1_average_read_length), str(r1_average_base_quality), str(r1_new_singleton_read_count), str(float(r1_new_singleton_base_count)/float(r1_new_singleton_read_count)), str(float(r1_new_singleton_total_quality_score)/float(r1_new_singleton_base_count))]) + "\n")
output.write("\t".join([args.filtered_r2_fastq, str(r2_read_count), str(r2_average_read_length), str(r2_average_base_quality), str(r2_new_singleton_read_count), str(float(r2_new_singleton_base_count)/float(r2_new_singleton_read_count)), str(float(r2_new_singleton_total_quality_score)/float(r2_new_singleton_base_count))]) + "\n")
output.write("\t".join([args.filtered_old_singleton_fastq, "0", "0", "0", str(old_singleton_read_count), str(old_singleton_average_read_length), str(old_singleton_average_base_quality)]) + "\n")