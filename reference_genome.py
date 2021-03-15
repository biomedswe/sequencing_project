import time

class ReferenceGenome():

    def __init__(self):
        pass

    def download(self, misc, shortcuts):
        '''This function downloads the human reference genome GRCh38.fa and the comprehensive gene annotations gencode.v37.primary_assembly.annotation.gtf
        from https://www.gencodegenes.org/human/'''
 
        try:
            if misc.step_completed(shortcuts.reference_genome_file, 'Reference genome and annotation file allready downloaded.') and misc.step_completed(shortcuts.annotation_gtf_file, ''):
                time.sleep(2.5)
                pass
            else:
                misc.clear_screen()
                print("Download reference genome\n\n")
                print("Downloading:")
                print("GRCh38.p13.genome.fa and from Comprehensive gene annotation https://www.gencodegenes.org/human/...\n")

                cmd_fasta_download = "wget ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/GRCh38.p13.genome.fa.gz -P $HOME/sequencing_project/reference_genome/"
                # misc.run_command(cmd_fasta_download, 'Download of GRCh38.p13.genome.fa.gz completed')

                cmd_fasta_unzip = "gunzip $HOME/sequencing_project/reference_genome/GRCh38.p13.genome.fa.gz"
                misc.run_command(cmd_fasta_unzip, 'Unzip of GRCh38.p13.genome.fa.gz completed')

                cmd_gtf_download = "wget ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_37/gencode.v37.primary_assembly.annotation.gtf.gz -P $HOME/sequencing_project/reference_genome/"
                misc.run_command(cmd_gtf_download, 'Download of gencode.v37.primary_assembly.annotation.gtf.gz completed')

                cmd_gtf_unzip = "gunzip $HOME/sequencing_project/reference_genome/gencode.v37.primary_assembly.annotation.gtf.gz"
                misc.run_command(cmd_gtf_unzip, 'Unzip of gencode.v37.primary_assembly.annotation.gtf.gz completed')

                print("Completed!\nGRCh38.p13.genome.fa and gencode.v37.primary_assembly.annotation.gtf are saved in the reference_genome folder.\n")
                return input("Press any key to return to main menu...")
        except Exception as e:
            print(f'Error with download(): {e}')
            input("Press any key to continue...")

    #---------------------------------------------------------------------------
    def index_genome_dna(self, choice, filename, misc, shortcuts):
        '''This function indexes the reference genome so it can be used in the analysis'''

        try:
            ref_file = shortcuts.reference_genome_file
            ref_dir = shortcuts.reference_genome_dir
            # Index whole genome
            if choice == 1:
                print("\n\n1. Index whole genome\n")
                cmd_bwa_index = f"bwa index {ref_file}"
                misc.run_command(cmd_bwa_index, 'Bwa index')
                cmd_create_dict = f"samtools dict {ref_file} -o {ref_file[:-2]}dict"
                misc.run_command(cmd_create_dict, 'Creating .dict with samtools dict')
                cmd_create_fai = f"samtools faidx {ref_file} -o {ref_file}.fai"
                misc.run_command(cmd_create_fai, 'Creating .fai with samtools faidx')
                misc.create_trackFile(shortcuts.index_reference_genome_complete)
                print("\nIndexing reference genome completed!\n")


            # Index parts of genome
            if choice == 2:
                if misc.step_completed(f'{ref_dir}{filename}_index/{filename}_bwa.complete', 'Burrows Wheeler aligner index allready completed, skips step...'):
                    pass
                else:
                    print("1. Index reference genome\n")
                    cmd_bwa_index = f"bwa index {ref_dir}{filename}_index/{filename}.fa"
                    misc.run_command(cmd_bwa_index, 'Bwa index')
                    cmd_create_dict = f"samtools dict {ref_dir}{filename}_index/{filename}.fa -o {ref_dir}{filename}_index/{filename}.dict"
                    misc.run_command(cmd_create_dict, 'Creating .dict with samtools dict')
                    cmd_create_fai = f"samtools faidx {ref_dir}{filename}_index/{filename}.fa -o {ref_file}{filename}_index/{filename}.fai"
                    misc.run_command(cmd_create_fai, 'Creating .fai with samtools faidx')
                    misc.create_trackFile(f'{ref_dir}{filename}_index/{filename}_bwa.complete')
                    print("\nIndexing reference genome completed!\n")
        except Exception as e:
            print(f'Error with index_genome_dna: {e}')

    #---------------------------------------------------------------------------
    def index_genome_rna(self, choice, filename, misc, shortcuts):
        '''This function indexes either the whole genome or the chromosomes entered'''

        try:

            ref_dir = shortcuts.reference_genome_dir

            # Index whole genome
            if choice == 1:
                if misc.step_completed(shortcuts.whole_genome_indexing_complete, 'Whole genome indexing allready completed, returning...'):
                    time.sleep(2.5)
                    pass
                else:
                    misc.create_directory(shortcuts.star_index_dir_whole_genome)
                    threads = multiprocessing.cpu_count() - 2
                    cmd_StarIndex = f'''
                    STAR --runThreadN {threads} \\
                    --runMode genomeGenerate \\
                    --genomeDir {shortcuts.star_index_dir_whole_genome} \\
                    --genomeFastaFiles {shortcuts.reference_genome_file} \\
                    --sjdbGTFfile {shortcuts.annotation_gtf_file}'''
                    print(cmd_StarIndex)
                    misc.run_command(cmd_StarIndex, '\nIndexing whole genom with STAR genomeGenerate...')
                    misc.create_trackFile(shortcuts.whole_genome_indexing_complete)
                    print("\nWhole genome indexing completed!\n")
                    time.sleep(5)

            # Index parts of genome
            elif choice == 2:
                    if misc.step_completed(f'{ref_dir}{filename}_index/{filename}_starIndex.complete', f'{filename} genome indexing allready completed, returning...'):
                        time.sleep(2.5)
                        pass
                    else:
                        misc.create_directory(shortcuts.star_index_dir)
                        threads = multiprocessing.cpu_count() - 2
                        cmd_StarIndex = f'''
                        STAR --runThreadN {threads} \\
                        --genomeSAindexNbases 12 \\
                        --runMode genomeGenerate \\
                        --genomeDir {shortcuts.star_index_dir}{filename}_hg38_index \\
                        --genomeFastaFiles {ref_dir}{filename}_index/{filename}.fa \\
                        --sjdbGTFfile {ref_dir}{filename}_index/{filename}.gtf'''
                        print(cmd_StarIndex)
                        misc.run_command(cmd_StarIndex, '\nIndexing parts of genome completed')
                        misc.create_trackFile(f'{ref_dir}{filename}_index/{filename}_starIndex.complete')
        except Exception as e:
            print(f'Error with index_genome_rna: {e}')
