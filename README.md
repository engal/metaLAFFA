Tutorial for running metaLAFFA
================

-   [Quick Start Summary](#quick-start-summary)
-   [Full-length Tutorial](#full-length-tutorial)
    -   [Overview and Objectives](#overview-and-objectives)
    -   [In-depth metaLAFFA step descriptions](#in-depth-metalaffa-step-descriptions)
    -   [Download, configuration, and setup](#download-configuration-and-setup)
    -   [Input Data](#input-data)
    -   [Running metaLAFFA](#running-metalaffa)

**Repository:** <https://github.com/engal/metaLAFFA>

**Publication:** TBD

Quick Start Summary
-------------------

Follow these steps to annotate two example gut microbiome samples using metaLAFFA.

1.  If not already installed, install [**Python3**](https://www.python.org/downloads/) (version 3.7 or greater is required).

2.  Download and set up the metaLAFFA.

To download metaLAFFA, first navigate to the directory in which you would like to save the pipeline. You can then clone the git repository as follows:

``` bash
# Make a local clone of the metaLAFFA git repository.
git clone git@github.com:engal/metaLAFFA.git
```

Complete pipeline setup by running the setup.py script:

``` bash
# Perform pipeline setup.
cd metaLAFFA
python3 setup.py
```

Note that it can take a few hours to install all third-party tools and download and process all default databases, and takes ~10G of RAM.

(TODO: Figure out what KEGG BRITE mappings we can download and process without making use of the license. For testing purposes, please run the following in the pipeline directory:

``` bash
# Manual setup for ortholog-to-grouping mappings
mkdir ortholog_to_grouping_maps
cp /net/borenstein/vol1/DATA_REFERENCE/KEGG/KEGG_2018_02_23/KEGG_PARSED_2018_02_23/ko_to_module_prokaryotes.tab ortholog_to_grouping_maps/brite_ko_to_prokaryotic_module
cp /net/borenstein/vol1/DATA_REFERENCE/KEGG/KEGG_2018_02_23/KEGG_PARSED_2018_02_23/ko_to_pathway_prokaryotes.tab ortholog_to_grouping_maps/brite_ko_to_prokaryotic_pathway
```

)

1.  Download the example data by downloading and unzipping [**this file**]() (TODO: Point to example files hosted somewhere, for in-house testing use files at /net/borenstein/vol2/annotation\_pipeline\_testing/pipeline\_test\_data.tar.gz).

2.  Create a data directory and place the example data inside the data directory.

``` bash
# Create a data directory for inputs to the pipeline
mkdir data

# Expand the archive and put the sample data files int the data directory
tar -zxf pipeline_test_data.tar.gz
mv test_sample* data
```

1.  Run the pipeline to create BRITE module and pathway profiles for the two samples.

The pipeline is, by default, set up to run on a cluster using the Sun Grid Engine (SGE) cluster management system. Default settings request 10G of RAM per job, though ~220G RAM and 22 cores are requested per cluster node for running DIAMOND (Buchfink, Xie, and Huson 2015), 200G /tmp/ disk space for hit filtering, and 250G /tmp/ disk space for combining hit-filtered read mapping outputs. See full-length tutorial for changes required to adjust these settings.

``` bash
# Run Snakemake on an SGE cluster, with 50 jobs submitted at a time
snakemake -p -c "qsub {params.cluster}" -j 50 --latency-wait 60
```

Full-length Tutorial
--------------------

### Overview and Objectives

metaLAFFA is a pipeline for annotating shotgun metagenomic data with abundances of functional orthology groups. This process consists of several steps to go from raw FASTQs (with sequencing adapters removed) to functional profiles:

1.  Host read filtering (e.g. removing human DNA)
2.  Duplicate read filtering
3.  Quality trimming and filtering
4.  Mapping reads to genes
5.  Mapping genes to functional orthology groups (e.g. KOs)
6.  Aggregating orthologs into higher-level groupings (e.g. pathways)

In this tutorial, you will:

-   Install and set up metaLAFFA
-   Annotate two example human gut microbiome samples

### In-depth metaLAFFA step descriptions

##### 1. Host read filtering

The first step in metaLAFFA is host read filtering. Host reads should be removed to ensure that later analyses are only considering the functional potential of the microbial community of interest. This is particularly important in cases where samples might consist of a majority of host reads, as in human fecal samples from hosts with certain gastrointestinal disorders that cause excessive shedding of epithelial cells (e.g. ulcerative colitis). Host read filtering is usually performed by aligning reads to one or more reference genomes for the host species and removing reads with match qualities above a certain threshold. Based on the original Human Microbiome Project (Huttenhower et al. 2012) study protocols, metaLAFFA defaults to using BMTagger (Rotmistrovsky and Agarwala 2011) for host read filtering. The default host database is the human reference hs37.

##### 2. Duplicate read filtering

The second step in metaLAFFA is duplicate read filtering. Duplicate read filtering aims to remove reads that erroneously appear in a sample multiple times due to artifacts of sequencing (PCR duplicates or optical duplicates). An explanation of the cause for PCR duplicates can be found [**here**](http://www.cureffi.org/2012/12/11/how-pcr-duplicates-arise-in-next-generation-sequencing/). However, PCR duplicate filtering may not always be appropriate for metagenomic studies because the (correct and biologically meaningful) presence of highly similar/equivalent reads is possible in metagenomics, especially when a given species or strain is at high abundance (Nayfach and Pollard 2016). In these scenarios, there are in fact more copies of the same sequence present, and filtering out duplicate reads may dampen the signal of this higher copy number within the community. Optical duplicates instead arise when, after amplification on a flowcell, a large cluster of duplicated reads registers as two separate clusters, and these are safe to remove. The default duplicate filtering program is MarkDuplicates from the Picard set of bioinformatics tools (“Picard,” n.d.), and by default only optical duplicates are removed.

##### 3. Quality trimming and filtering

The final pre-processing step in metaLAFFA is quality trimming and filtering. The aim of quality trimming and filtering is to reduce sequencing noise by trimming bases with quality below a certain threshold from one or both ends of a read, as well as removing any reads that fall below a specific length threshold. For this step, metaLAFFA uses Trimmomatic (Bolger, Lohse, and Usadel 2014) by default, trimming reads based on Trimmomatic's maximum information criterion and filtering out trimmed reads shorter than 60bp.

##### 4. Mapping reads to gene IDs

Given filtered and quality-controlled FASTQs, metaLAFFA next maps these reads against a database of protein sequences corresponding to identified genes. Note that this (read-based annotation) method is one of two main annotation approaches, the other being assembly-based annotation, such as performed by MOCAT2 (Kultima et al. 2016). Read-based annotation works by assigning functional annotations to individual reads rather than by assembling contigs from reads, assigning functional annotations to ORFs identified in the contigs, and then mapping reads to the ORFs to get counts.

Read annotations are most often performed by aligning reads to a database of gene sequences that have prior functional associations. These alignments are often performed as translated alignments, i.e. doing a 6-frame translation of a read's nucleotide sequence to possible amino acid sequences and then aligning those amino acid sequences to the protein sequences associated with genes. metaLAFFA uses DIAMOND (Buchfink, Xie, and Huson 2015) as its default aligner due to its speed and built-in parallelization. The UniRef90 reference database of gene sequences (from UniProt (Consortium 2018)) is used by default, though other databases of annotated gene sequences could be used if available (e.g. KEGG).

##### 5. Filtering read mapping hits

After mapping reads to gene sequences, metaLAFFA filters these hits to improve annotation quality. There are several ways to filter hits that depend on how many best hits are kept per read and whether hits to genes without functional annotations are kept. The differences in these methods are discussed in Carr et al. (Carr and Borenstein 2014), which analyzes the trade-offs in sensitivity and specificity that come from different choices in hit filtering. By default, metaLAFFA uses a custom Python script to filter hits and uses the highest specificity hit filtering method, keeping only hits with the best e-value for each read and allowing best hits to include genes without functional annotations.

##### 6. Gene counting

Once the hits are filtered, metaLAFFA counts gene abundances based on the number of reads that map to each gene in the sequence database. There are two important considerations when counting gene abundances based on mapped reads. The first is count normalization based on gene length, i.e. longer genes are more likely to be sequenced than shorter genes, and so a longer gene will be more likely to have more reads map to it than a shorter gene even though both genes might be at the same abundance and so the counts of reads mapping to a gene should be normalized by the length of the gene. The second consideration is how to count genes when a read maps to more than one gene. This can be done in one of two ways, either by giving a count of 1 to each gene a read maps to or by having each read contribute a count of 1 in total but dividing a read's count among the genes a read maps to. The former method can lead to double-counting issues and so metaLAFFA uses a fractional gene counting method by default. Gene length normalization and fractional counting are performed by a custom Python script in default metaLAFFA operation.

##### 7. Ortholog counting

The next step after calculating gene abundances is to convert those gene abundances to abundances of annotated functions. Usually, these come in the form of functional orthology group abundances as defined by various functional annotation systmes (e.g. KEGG (Kanehisa et al. 2018), MetaCyc (Caspi et al. 2007), etc.). These functional orthology groups usually correspond to the function a protein corresponding to a single gene may perform. Similar to the gene counting step, some genes may map to multiple orthology groups in a given system, and so each gene can either contribute its whole abundance to each associated orthology group or fractional contributions of its abundance to each associated orthology group. Again, due to double-counting issues, by default metaLAFFA uses a fraction contribution method when counting ortholog abundances based on gene abundances. Also, metaLAFFA calculates abundances of KEGG orthology groups (KOs) from UniProt gene functional annotations by default. By default, orthology group abundance calculations are performed using a custom Python script.

##### 8. Correcting orthology group abundances

Once initial orthology group abundances have been calculated, it is usually necessary to correct them to allow for comparisons between samples. Specifically, orthology group abundances based on read counts from standard shotgun metagenomic seuqencing are inherently compositional in nature (i.e. read count-based abundances reflect relative, rather than absolute, orthology group abundances). To account for this issue and convert orthology group abundances into a form that allows for valid standard statistical comparisons between samples, metaLAFFA uses MUSiCC (Manor and Borenstein 2015) during default operation. MUSiCC uses genes identified as universally single-copy across bacterial genomes to transform read-based relative orthology group abundances into average orthology group copy number across genomes within a sample. By default, metaLAFFA uses MUSiCC's intra-sample correction with learned models for incorporating universal single-copy gene abundances into the correction process.

##### 9. Aggregating orthology groups into higher-level functional descriptions

The final step in metaLAFFA is to aggregate functional orthology group abundances into abundances at higher-level functional descriptions (e.g. modules or pathways). This can help with interpretability of results, since initial orthology group counting can often result in thousands of unique functions. One way to handle this issue is to aggregate initial functional orthology groups into higher-level functional classifications based on their functional similarity or shared membership in a biological process (e.g. carbohydrate metabolism). This can result in a more manageable number of functions to analyze and can also reveal interesting trends in higher-level functional categories. By default, metaLAFFA uses a similar counting scheme to gene and orthology group counting when aggregating orthology groups, assigning an orthology group's abundance fractionally among all of the functional categories it belongs to at a given functional resolution. Associations between KOs and higher-level functional descriptions (modules and pathways) are determined from the KEGG BRITE hierarchy (Kanehisa et al. 2018) under default settings. During default operation, this is performed using a custom Python script.

##### 10. Summarizing results of steps in metaLAFFA

Another important component of metaLAFFA is the automatic summary statistic generation that accompanies each step in the pipeline. Default summary statistics include number of reads, average read length, and average base quality for input FASTQs and the resulting FASTQs after each FASTQ filtering step, as well as number of hits, number of mapped reads, number of associated genes, and number of annotated orthology groups as determined after each step in the pipeline. These summary statistics are merged at the end into a single table summarizing the results of each step of the pipeline.

### Download, configuration, and setup

metaLAFFA is a Snakemake pipeline configured via Python scripts that manages the functional annotation of shotgun metagenomic data via various Python scripts and third-party tools.

First, if you do not have Python3 (version 3.7 or greater) installed, download the installation executable from [**here**](https://www.python.org/downloads/) and run it.

#### Download and set up the metaLAFFA.

To download metaLAFFA, first navigate to the directory in which you would like to save the pipeline. You can then clone the git repository as follows:

``` bash
# Make a local clone of the metaLAFFA git repository.
git clone git@github.com:engal/metaLAFFA.git
```

This contains the Snakemake file defining the pipeline, various Python scripts for pipeline operation and custom processing for some pipeline steps, and a Python module that configures how the steps of the pipeline are run. This does not include various third-party tools or default databases used by the pipeline.

#### Configuring metaLAFFA

metaLAFFA is configured via a Python module partitioned into various submodules targeted at specific aspects of the pipeline and defined in the "config" directory. For example, the "config/file\_organization.py" submodule defines where inputs to the pipeline are located, where output files should be saved, and where various databases used by the pipeline are located.

#### Installing third-party tools and processing default databases

By the default, metaLAFFA is built to use several third-party tools and a couple of default databses used in host read filtering and read mapping. To complete pipeline setup by installing these third-party tools and default databases, run the setup.py script (note that if you run Python3 using "python" rather than "python3" from the command line, you will need to modify the "config/operation.py" submodule to use "python" instead of "python3" for the setup script and other metaLAFFA scripts to work):

``` bash
# Perform pipeline setup.
cd metaLAFFA
python3 setup.py
```

(TODO: Figure out what KEGG BRITE mappings we can download and process without making use of the license. For testing purposes, please run the following in the pipeline directory:

``` bash
# Manual setup for ortholog-to-grouping mappings
mkdir ortholog_to_grouping_maps
cp /net/borenstein/vol1/DATA_REFERENCE/KEGG/KEGG_2018_02_23/KEGG_PARSED_2018_02_23/ko_to_module_prokaryotes.tab ortholog_to_grouping_maps/brite_ko_to_prokaryotic_module
cp /net/borenstein/vol1/DATA_REFERENCE/KEGG/KEGG_2018_02_23/KEGG_PARSED_2018_02_23/ko_to_pathway_prokaryotes.tab ortholog_to_grouping_maps/brite_ko_to_prokaryotic_pathway
```

)

### Input Data

metaLAFFA can take un-filtered FASTQs as input. By default, this input data should be located in a directory named "data" within the pipeline directory. You can create this directory as follows:

``` bash
# Create a data directory for inputs to the pipeline
mkdir data
```

Alternatively, if you want to work with data located elsewhere and don't want to copy it to the pipeline directory, you can modify the directory used for input data in the file organization submodule by opening "config/file\_organization.py" in a text editor and changing the value of the "initial\_data\_directory" variable. Note that, by default, input FASTQs are expected to be named {sample}.{type}.fastq.gz, where:

-   {sample} is the sample ID (this cannot include any "."s)
-   {type} is the type of FASTQ ("R1" for paired forward reads, "R2" for paired reverse reads, and "S" for unpaired singleton reads)

The IDs used for FASTQ types ("R1", "R2", and "S") can be changed in the "config/operation.py" submodule by modifying the "fastq\_types" variable.

You can download example data by downloading [**this file**]() (TODO: Point to example files hosted somewhere, for in-house testing use files at /net/borenstein/vol2/annotation\_pipeline\_testing/pipeline\_test\_data.tar.gz). Unzip these example files and put them in the data directory:

``` bash
# Expand the archive and put the sample data files int the data directory
tar -zxf pipeline_test_data.tar.gz
mv test_sample* data/
```

#### (Advanced) Using a different step in metaLAFFA as a starting point

While metaLAFFA defaults to taking in unfiltered FASTQs, it is also possible for metaLAFFA to take input files appropriate for any step in the pipeline. For example, if you have already processed and filtered your FASTQ files, you can use those as input to the pipeline as long as they follow the correct naming scheme (e.g. {sample}.{type}.fastq.gz for FASTQs). To find the naming scheme for input files for different steps in the pipeline, you can open the configuration submodule associated with the step and look at the "input" variable definition.

You must indicate which intermediate step you want metaLAFFA to start from by appropriately modifying the "pipeline\_steps.txt" file. This file tells the pipeline what the input to each step in the pipeline is (either initial input data or the output of previous steps). For example, by default the host filtering step takes in the initial input data as its input, and this is indicated by the line "host\_filter:INPUT" (step name on the left, followed by a colon and then a comma-separated list of where the input to the step comes from). If you want to start from FASTQs that you have already filtered, you would make the following changes to "pipeline\_steps.txt":

-   Change the reading mapping step input to be the initial input data (i.e. changing "map\_reads\_to\_genes:quality\_filter" -&gt;; "map\_reads\_to\_genes:INPUT").
-   Comment-out or delete steps that you don't want to run (i.e. for all lines for steps starting with "host\_filter", "duplicate\_filter", or "quality\_filter", either put a "\#" at the front of the line or delete the line).

Once you've made those changes, metaLAFFA will start from the read mapping step and use files in the "data" directory as input. Further explanation of the "pipeline\_steps.txt" file and ways to mark certain steps are explained in the "config/operation.py" submodule.

### Running metaLAFFA

metaLAFFA is run using Snakemake, which has built-in tools for cluster integration. By default, metaLAFFA is set up to run on a cluster using the Sun Grid Engine (SGE) cluster management and job scheduling system.

The pipeline is, by default, set up to run on a cluster using the Sun Grid Engine (SGE) cluster management system. Default settings request 10G of RAM per job, ~220G RAM and 22 cores are requested per cluster node for running DIAMOND, 200G /tmp/ disk space for hit filtering, and 250G /tmp/ disk space for combining hit-filtered read mapping outputs. These defaults were set with 10's to 100's of millions of reads in each FASTQ in mind. You can start metaLAFFA and have it submit jobs to an SGE cluster via the following command (recommended you begin this in a terminal that can be left open to run, e.g. via a [**screen session**](https://ss64.com/bash/screen.html), because the Snakemake will need to be running during the entire process):

``` bash
# Run Snakemake on an SGE cluster, with 50 jobs submitted at a time
snakemake -p -c "qsub {params.cluster}" -j 50 --latency-wait 60
```

The default cluster job requests for each step can be changed in the "config/cluster.py" submodule, DIAMOND's specific memory and core requests can be changed in the "config/steps/map\_reads\_to\_genes.py" submodule, and the hit filtering disk space requests can be changed in their associated configuration submodules as well. By default, metaLAFFA performs most operations in the /tmp/ directory, which means that cluster jobs will make use of the local space on a node, where available disk space may be higher. Importantly, if you need to reduce the memory request for DIAMOND, you will also need to adjust the "block\_size" and "index\_chunks" settings in the read mapping configuration submodule as these control how much of the reference database DIAMOND loads into memory at a time. For more information on adjusting these DIAMOND parameters, see the DIAMOND manual [**here**](https://github.com/bbuchfink/diamond/raw/master/diamond_manual.pdf).

It is possible to run the pipeline locally, though this is normally prohibited by DIAMOND's large memory requirements. If you have appropriately adjused the "block\_size" and "index\_chunks" parameters for DIAMOND such that you have enough memory to run locally, then the pipeline can be operated simply by running:

``` bash
# Run Snakemake locally
snakemake
```

Note that you can stop the pipeline at any point (e.g. CTRL-C while running Snakemake) and if you rerun the same Snakemake command, the pipeline will pick up where it left off.

Once the pipeline has finished running, you can find your desired output files in the default final output directory, "output/final/". If you ran the pipeline with the example data, these should include:

``` bash
output/final/brite_ko_to_prokaryotic_module.aggregated_orthologs.tab
output/final/brite_ko_to_prokaryotic_pathway.aggregated_orthologs.tab
output/final/summary.txt
```

Bolger, Anthony M, Marc Lohse, and Bjoern Usadel. 2014. “Trimmomatic: A Flexible Trimmer for Illumina Sequence Data.” *Bioinformatics* 30 (15). Oxford University Press: 2114–20.

Buchfink, Benjamin, Chao Xie, and Daniel H Huson. 2015. “Fast and Sensitive Protein Alignment Using Diamond.” *Nature Methods* 12 (1). Nature Publishing Group: 59.

Carr, Rogan, and Elhanan Borenstein. 2014. “Comparative Analysis of Functional Metagenomic Annotation and the Mappability of Short Reads.” *PLoS One* 9 (8). Public Library of Science: e105776.

Caspi, Ron, Hartmut Foerster, Carol A Fulcher, Pallavi Kaipa, Markus Krummenacker, Mario Latendresse, Suzanne Paley, et al. 2007. “The Metacyc Database of Metabolic Pathways and Enzymes and the Biocyc Collection of Pathway/Genome Databases.” *Nucleic Acids Research* 36 (suppl\_1). Oxford University Press: D623–D631.

Consortium, UniProt. 2018. “UniProt: A Worldwide Hub of Protein Knowledge.” *Nucleic Acids Research* 47 (D1). Oxford University Press: D506–D515.

Huttenhower, Curtis, Dirk Gevers, Rob Knight, Sahar Abubucker, Jonathan H Badger, Asif T Chinwalla, Heather H Creasy, et al. 2012. “Structure, Function and Diversity of the Healthy Human Microbiome.” *Nature* 486 (7402). Nature Publishing Group: 207.

Kanehisa, Minoru, Yoko Sato, Miho Furumichi, Kanae Morishima, and Mao Tanabe. 2018. “New Approach for Understanding Genome Variations in Kegg.” *Nucleic Acids Research* 47 (D1). Oxford University Press: D590–D595.

Kultima, Jens Roat, Luis Pedro Coelho, Kristoffer Forslund, Jaime Huerta-Cepas, Simone S Li, Marja Driessen, Anita Yvonne Voigt, Georg Zeller, Shinichi Sunagawa, and Peer Bork. 2016. “MOCAT2: A Metagenomic Assembly, Annotation and Profiling Framework.” *Bioinformatics* 32 (16). Oxford University Press: 2520–3.

Manor, Ohad, and Elhanan Borenstein. 2015. “MUSiCC: A Marker Genes Based Framework for Metagenomic Normalization and Accurate Profiling of Gene Abundances in the Microbiome.” *Genome Biology* 16 (1). BioMed Central: 53.

Nayfach, Stephen, and Katherine S Pollard. 2016. “Toward Accurate and Quantitative Comparative Metagenomics.” *Cell* 166 (5). Elsevier: 1103–16.

“Picard.” n.d. <http://broadinstitute.github.io/picard/>.

Rotmistrovsky, Kirill, and Richa Agarwala. 2011. “BMTagger: Best Match Tagger for Removing Human Reads from Metagenomics Datasets.” *Unpublished*.