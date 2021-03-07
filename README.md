# sequencing_project
Allele-specific expression (ase) analysis pipeline

This script automates everything from setting up anaconda to downloading reference genome and performing DNA and RNA analysis to get a result about ase

## Requirements
- Platform: 
    - linux-64
    - python >= 3.6
    
    
## Installation and setup instructions
Open bash (Unix shell) and type the following:

### 1. Clone the git archive:


```
git clone https://github.com/biomedswe/sequencing_project.git $HOME
```

### 2. Run main.py and follow instructions in program

```
python3 main.py (after navigating to $HOME/sequencing_project)
```
or
```
python3 $HOME/sequencing_project/main.py
```

### 3. Copy your DNA-seq/RNA-seq reads into the right folders

DNA-seq reads: (in fasta/fastq format) into $HOME/sequencing_project/dna_seq/reads 

RNA-seq reads: (in fasta.gz) into $HOME/sequencing_project/rna_seq/reads
    
 
