import time, multiprocessing
from os import sys

class ReferenceGenome():

    def __init__(self):
        pass

    def download(self, misc, shortcuts):
        '''This function downloads the human reference genome GRCh38.fa and the comprehensive gene annotations gencode.v37.primary_assembly.annotation.gtf
        from https://www.gencodegenes.org/human/'''

        try:
            misc.clear_screen()
            misc.log_to_file("Downloading GRCh38.p13.genome.fa and Comprehensive gene annotation from https://www.gencodegenes.org/human/...")
            cmd_fasta_download = f"wget ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/GRCh38.p13.genome.fa.gz -P {shortcuts.GRCh38_dir}"
            if misc.run_command(cmd_fasta_download, 'Downloading GRCh38.p13.genome.fa.gz', shortcuts.reference_genome_file, None):
                cmd_fasta_unzip = f"gunzip {shortcuts.GRCh38_dir}GRCh38.p13.genome.fa.gz"
                misc.run_command(cmd_fasta_unzip, 'Unzipping GRCh38.p13.genome.fa.gz', None, None)

            cmd_gtf_download = f"wget ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_37/gencode.v37.primary_assembly.annotation.gtf.gz -P {shortcuts.GRCh38_dir}"
            if misc.run_command(cmd_gtf_download, 'Downloading gencode.v37.primary_assembly.annotation.gtf.gz', shortcuts.annotation_gtf_file, None):
                cmd_gtf_unzip = f"gunzip {shortcuts.GRCh38_dir}gencode.v37.primary_assembly.annotation.gtf.gz"
                misc.run_command(cmd_gtf_unzip, 'Unzipping gencode.v37.primary_assembly.annotation.gtf.gz', None, None)
                misc.log_to_file("Download completed!\nGRCh38.p13.genome.fa and gencode.v37.primary_assembly.annotation.gtf are saved in the reference_genome/bwa_index/GRCh38 folder.\n")
            return input("Press any key to return to previous menu...")
        except Exception as e:
            print(f'Error with ReferenceGenome.download() in reference_genome.py: {e}')
            input('press any key to exit')
            sys.exit()
