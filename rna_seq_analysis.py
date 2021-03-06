from os import listdir, getenv, sys, path
import subprocess
import multiprocessing
import time
import timeit
from miscellaneous import Misc
try:
    import vcfpy
    import numpy as np
    import pandas as pd
    from Bio import SeqIO
    from scipy.stats import binom_test
except Exception as e:
    Misc().log_to_file("info", f"importing in rna_seq_analysis.py: {e}")


class RnaSeqAnalysis():

    def __init__(self):
        pass

    #---------------------------------------------------------------------------
    def index_genome_rna(self, misc, shortcuts):
        '''This function indexes either the whole genome or the chromosomes entered'''

        try:
            ref_dir = shortcuts.reference_genome_dir
            if not misc.step_allready_completed(f"{shortcuts.star_index_dir}starIndex.complete", "Indexing genome with STAR genomeGenerate"):
                start = timeit.default_timer()
                threads = multiprocessing.cpu_count() -2
                misc.log_to_file("info", f"Starting: indexing genome with STAR using {threads} out of {threads + 2} available threads")
                cmd_StarIndex = f'''
                STAR --runThreadN {threads} \\
                --runMode genomeGenerate \\
                --genomeDir {shortcuts.star_index_dir} \\
                --genomeFastaFiles {shortcuts.reference_genome_file} \\
                --sjdbGTFfile {shortcuts.annotation_gtf_file}'''
                if misc.run_command(cmd_StarIndex, None, None, f"{shortcuts.star_index_dir}starIndex.complete"):
                    elapsed = timeit.default_timer() - start
                    misc.log_to_file("info", f'Indexing whole genome with STAR succesfully completed in {misc.elapsed_time(elapsed)} - OK!')
                    input('press any key to exit')
                    sys.exit()

        except Exception as e:
            misc.log_exception(".index_genome_rna in rna_seq_analysis.py:", e)

    #---------------------------------------------------------------------------
    def map_reads(self, options, misc, shortcuts):
        '''This function map reads to the reference genome'''



        try:
            if not misc.step_allready_completed(f"{shortcuts.star_output_dir}map.complete", f'Map reads to {options.tumor_id}'):
                reads = []
                for read in listdir(shortcuts.rna_reads_dir):
                    if options.tumor_id in read:
                        reads.append(read)
                    else:
                        misc.log_to_file("info", 'Rna reads are incorrectly named')
                        sys.exit()
                threads = multiprocessing.cpu_count() - 2
                misc.log_to_file("info", f'Starting: mapping reads ({options.tumor_id}) to genome with STAR using {threads} out of {threads + 2} available threads')

                cmd_mapReads = f'''
                STAR --genomeDir {shortcuts.star_index_dir} \\
                --readFilesIn {shortcuts.rna_reads_dir}{reads[0]} {shortcuts.rna_reads_dir}{reads[1]} \\
                --runThreadN {threads} \\
                --alignIntronMax 1000000 \\
                --alignIntronMin 20 \\
                --alignMatesGapMax 1000000 \\
                --alignSJDBoverhangMin 1 \\
                --alignSJoverhangMin 8 \\
                --alignSoftClipAtReferenceEnds Yes \\
                --chimJunctionOverhangMin 15 \\
                --chimMainSegmentMultNmax 1 \\
                --chimOutType Junctions SeparateSAMold WithinBAM SoftClip \\
                --chimSegmentMin 15 \\
                --genomeLoad NoSharedMemory \\
                --limitSjdbInsertNsj 1200000 \\
                --outFileNamePrefix {shortcuts.star_output_dir}{options.tumor_id}_ \\
                --outFilterIntronMotifs None \\
                --outFilterMatchNminOverLread 0.33 \\
                --outFilterMismatchNmax 999 \\
                --outFilterMismatchNoverLmax 0.1 \\
                --outFilterMultimapNmax 20 \\
                --outFilterScoreMinOverLread 0.33 \\
                --outFilterType BySJout \\
                --outSAMattributes NH HI AS nM NM MD XS ch vA vG vW \\
                --outSAMstrandField intronMotif \\
                --outSAMtype BAM Unsorted \\
                --outSAMunmapped Within \\
                --quantMode TranscriptomeSAM GeneCounts \\
                --readFilesCommand zcat \\
                --waspOutputMode SAMtag \\
                --varVCFfile {shortcuts.gatk_vcfFile} \\
                --outSAMattrRGline ID:{reads[0][:16]} SM:{options.tumor_id} LB:{reads[0][:16]} PL:"ILLUMINA" PU:{reads[0][:16]} \\
                --twopassMode Basic'''
                start = timeit.default_timer()
                misc.run_command(cmd_mapReads, f'Mapping reads to genome', f'{shortcuts.star_output_dir}{options.tumor_id}_Aligned.out.bam', None)
                cmd_sortsam = f"picard SortSam -I {shortcuts.star_output_dir}{options.tumor_id}_Aligned.out.bam -O {shortcuts.star_output_dir}{options.tumor_id}_Aligned_sorted.out.bam -SO coordinate"
                misc.run_command(cmd_sortsam, "Sorting BAM with Picard SortSam", f"{shortcuts.star_output_dir}{options.tumor_id}_Aligned_sorted.out.bam", None)
                cmd_samtools_index = f"samtools index {shortcuts.star_output_dir}{options.tumor_id}_Aligned_sorted.out.bam"
                misc.run_command(cmd_samtools_index, "Indexing BAM with Samtools index", f"{shortcuts.star_output_dir}{options.tumor_id}_Aligned_sorted.out.bam.bai",  None)
                cmd_wasp = f"samtools view -h {shortcuts.star_output_dir}{options.tumor_id}_Aligned_sorted.out.bam | LC_ALL=C egrep \"^@|vW:i:1\" | samtools view -bo {shortcuts.star_output_dir}{options.tumor_id}_WASP_pass.bam -"
                misc.run_command(cmd_wasp, "Applying wasp filtering", f"{shortcuts.star_output_dir}{options.tumor_id}_WASP_pass.bam", f"{shortcuts.star_output_dir}map.complete")
                elapsed = timeit.default_timer() - start
                misc.log_to_file("info", f'All steps in mapping reads to gemome with STAR succesfully completed in {misc.elapsed_time(elapsed)} - OK!')
        except Exception as e:
            misc.log_exception(".map_reads() in rna_seq_analysis.py:", e)

    #---------------------------------------------------------------------------
    def ASEReadCounter(self, options, misc, shortcuts):

        try:
            if not misc.step_allready_completed(f"{shortcuts.star_output_dir}ase.complete", f'ASEReadCounter for {options.tumor_id}'):
                ref_dir = shortcuts.reference_genome_dir
                misc.log_to_file("info", "Starting: Counting ASE reads using ASEReadCounter")
                start = timeit.default_timer()
                cmd_ase = f'''
                gatk ASEReadCounter -R {shortcuts.reference_genome_file} \\
                --min-mapping-quality 10 \\
                --min-depth-of-non-filtered-base 10 \\
                --min-base-quality 2 \\
                --disable-read-filter NotDuplicateReadFilter \\
                --variant {shortcuts.haplotypecaller_output_dir}{options.tumor_id}/{options.tumor_id}_filtered_RD10_snps_tumor_het_annotated.vcf \\
                -I {shortcuts.star_output_dir}{options.tumor_id}_Aligned_sorted.out.bam \\
                --output-format CSV \\
                --output {shortcuts.star_output_dir}{options.tumor_id}_STAR_ASE.csv'''
                misc.run_command(cmd_ase, None, f'{shortcuts.star_output_dir}{options.tumor_id}/ase.complete', f'{shortcuts.star_output_dir}ase.complete')
                elapsed = timeit.default_timer() - start
                misc.log_to_file(f'ASEReadCounter for {options.tumor_id} with STAR succesfully completed in {misc.elapsed_time(elapsed)} - OK!')
        except Exception as e:
            misc.log_exception(".ASEReadCounter() in rna_seq_analysis.py:", e)

    #---------------------------------------------------------------------------
    def add_wgs_data_to_csv(self, options, misc, shortcuts):
        '''This functions reads the CHROM and POS column of the vcf file and the allele depth 'AD' column. CHROM and POS columns are concatenated
        into a string as key in the dict and the 'AD' matching the CHROM and POS is the value. The csv file created by gatk ASEReadCounter is opened
        and 4 new columns with values are written to the file. df.apply applies the lambda function in every row in the csv file.'''

        # try:

        start = timeit.default_timer()
        misc.log_to_file(f"Starting: Creating CSV...")
        dict = {}
        vcf_reader = vcfpy.Reader.from_path(f'{shortcuts.haplotypecaller_output_dir}{options.tumor_id}/{options.tumor_id}_filtered_RD10_snps_tumor_het_annotated.vcf', 'r')
        variants_to_exclude = ['downstream_gene_variant', 'intergenic_region', 'intragenic_variant', 'intron_variant', 'splice_region_variant', 'splice_region_variant&intron_variant', 'upstream_gene_variant']

        for i, record in enumerate(vcf_reader):
            contig = record.CHROM
            position = record.POS
            refCount = record.calls[0].data.get('AD')[0]
            altCount = record.calls[0].data.get('AD')[1]
            totalCount = refCount + altCount
            geneName = record.__dict__['INFO']['ANN'][0].split('|')[3]
            variantType = record.__dict__['INFO']['ANN'][0].split('|')[1] if not record.__dict__['INFO']['ANN'][0].split('|')[1] in variants_to_exclude else None
            dict[i] = [contig, position, refCount, altCount, totalCount, geneName, variantType]

        # Make DataFrame out of dict
        df_vcf = pd.DataFrame.from_dict(dict, orient="index", columns=["contig", "position", "DNA_refCount", "DNA_altCount", "DNA_totalCount", "geneName", "variantType"])
        # read exel file with cnv information
        if not path.isfile(f'{shortcuts.star_output_dir}{options.tumor_id}_CN.xlsx'):
            misc.log_to_file(f"No file specifying copynumber, save {options.tumor_id}_CN.xlsx in {shortcuts.star_output_dir}")
            sys.exit()
        df_cn = pd.read_excel(f'{shortcuts.star_output_dir}{options.tumor_id}_CN.xlsx')
        df_cn = df_cn[['Chromosome', 'Start', 'End', 'Cn']]
        # read csv from star output
        df = pd.read_csv(f'{shortcuts.star_output_dir}{options.tumor_id}_STAR_ASE.csv')

        df['Subgroup'] = options.subgroup
        df['Sample'] = options.tumor_id.replace('-', '_')
        df_merge = pd.merge(df_vcf, df, on=["contig", "position"])
        df_merge.insert(14, 'CN', True)
        df_merge.insert(15, 'pValue_WGS_VAF', True)
        df_merge.insert(16, 'RNA/DNA_ratio_WGS_VAF', True)
        df_merge.insert(17, 'pValue_CNV', True)
        df_merge.insert(18, 'RNA/DNA_ratio_CNV', True)

        df_merge.rename(columns={'contig' : "Chromosome", 'refAllele' : 'RNA_refAllele', 'altAllele' : 'RNA_altAllele', 'refCount': 'RNA_refCount', 'altCount': 'RNA_altCount', 'totalCount': 'RNA_totalCount'}, inplace=True)
        df_merge = df_merge[['Subgroup', 'Sample', 'geneName', 'variantType', 'Chromosome', 'position', 'variantID', 'RNA_refAllele', 'RNA_altAllele', 'RNA_refCount', 'RNA_altCount', 'RNA_totalCount', 'DNA_refCount', 'DNA_altCount', 'CN', 'pValue_WGS_VAF', 'RNA/DNA_ratio_WGS_VAF', 'pValue_CNV', 'RNA/DNA_ratio_CNV']]
        #                        0           1            2             3            4          5           6               7                8                9                10               11               12              13        14          15                   16                  17                 18
        df_merge[['RNA_refCount', 'RNA_altCount']] = df_merge[['RNA_refCount', 'RNA_altCount']].apply(pd.to_numeric)
        df_merge['CN'] = df_merge.apply(lambda row: self.add_CNV(misc, df_cn, row), axis=1) # row[14]
        df_merge.dropna(inplace=True)
        df_merge['RNA_altCount'] = df_merge.apply(lambda row: 1 if int(row[10]) < 1 else int(row[10]), axis=1)
        df_merge['DNA_altCount'] = df_merge.apply(lambda row: 1 if int(row[13]) < 1 else int(row[13]), axis=1)
        df_merge['pValue_WGS_VAF'] = df_merge.apply(lambda row: f"{binom_test(int(row[9]), int(row[11]), int(row[12])/(int(row[12]) + int(row[13])))}", axis=1) #input: RNA_refCount, RNA_totalCount, DNA_refCount/(DNA_refCount + DNA_altCount)
        df_merge['RNA/DNA_ratio_WGS_VAF'] = df_merge.apply(lambda row: f"{(int(row[9])/int(row[10]))/(int(row[12])/int(row[13]))}", axis=1) # (RNA_refCount/RNA_altCount)/(DNA_refCount/DNA_altCount)
        df_merge['pValue_CNV'] = df_merge.apply(lambda row: self.calculate_pValue_CNV(misc, row), axis=1) #input: RNA_refCount, RNA_totalCount, CNV
        df_merge['RNA/DNA_ratio_CNV'] = df_merge.apply(lambda row: self.calculate_RNA_DNA_ratio_CNV(misc, row), axis=1) # RNA_refAllele_ratio/CNV_ratio
        df_merge.to_csv(f'{shortcuts.star_output_dir}{options.tumor_id}_STAR_ASE_completed.csv', sep=',', index=False)
        print(df_merge.dtypes)
        # Drop rows that have both RNA_refCount and RNA_altCount < 10
        df_merge.drop(df_merge[ (df_merge['RNA_refCount'] < 10) & (df_merge['RNA_altCount'] < 10)].index, inplace=True)
        elapsed = timeit.default_timer() - start
        misc.log_to_file(f'Creating CSV completed in {misc.elapsed_time(elapsed)} - OK!')
        sys.exit()
        # except Exception as e:
        #     misc.log_exception(".add_wgs_data_to_csv() in rna_seq_analysis.py:", e)

    # --------------------------------------------------------------------------
    # def RNA_refAllele_ratio(self, misc, row):
    #
    #     if int(row[10]) < 1: row[10] = 1 # Change RNA_altCount to 1 if 0 to avoid division with zero
    #     return f"{int(row[9])/int(row[10])}"

    # --------------------------------------------------------------------------
    # def DNA_refAllele_ratio(self, misc, row):
    #
    #     if int(row[13]) < 1: row[13] = 1 # Change DNA_altCount to 1 if 0 to avoid division with zero
    #     return f"{int(row[12])/int(row[13])}"

    # --------------------------------------------------------------------------
    def add_CNV(self, misc, df_cn, row):
        '''This function fetch the CN data from the CN.xlsx document for the specific position'''

        for i in df_cn.index:
            if row[4] == df_cn["Chromosome"].iloc[i] and df_cn["Start"].iloc[i] <= row[5] < df_cn["End"].iloc[i]:
                return df_cn["Cn"].iloc[i]

    # --------------------------------------------------------------------------
    def calculate_RNA_DNA_ratio_CNV(self, misc, row):
        '''This function determines what CN-ratio value that should be used when calculating the VAF_ratio_CNV'''


        # CN = 2 or CN = -4
        if int(row[14]) == 2 or int(row[14]) == -4:
            return f"{int(row[9])/int(row[10])}" # (RNA_refCount/RNA_altCount)/1 : CNV_ratio: 1/1

        # CN = 3
        elif int(row[14]) == 3:
            # if DNA_refCount > DNA_altCount
            if int(row[12]) > int(row[13]):
                return f"{(int(row[9])/int(row[10]))/2}" # (RNA_refCount/RNA_altCount)/2 : CNV_ratio: 2/1
            # if DNA_refCount < DNA_altCount
            else:
                return f"{(int(row[9])/int(row[10]))/0.5}" # (RNA_refCount/RNA_altCount)/0.5 : CNV_ratio: 1/2

        # CN = 4
        elif int(row[14]) == 4:
            # if DNA_refCount > DNA_altCount
            if int(row[12]) > int(row[13]):
                return f"{(int(row[9])/int(row[10]))/3}" # (RNA_refCount/RNA_altCount)/3 : CNV_ratio: 3/1
            # if DNA_refCount < DNA_altCount
            else:
                return f"{(int(row[9])/int(row[10]))/(1/3)}" # (RNA_refCount/RNA_altCount)/(1/3) : CNV_ratio: 1/3

        # CN = 5
        elif int(row[14]) == 5:
            # if DNA_refCount > DNA_altCount
            if int(row[12]) > int(row[13]):
                return f"{(int(row[9])/int(row[10]))/(3/2)}" # (RNA_refCount/RNA_altCount)/(3/2) : CNV_ratio: 3/2
            else:
                return f"{(int(row[9])/int(row[10]))/(2/3)}" # (RNA_refCount/RNA_altCount)/(2/3) : CNV_ratio: 2/3

        # CN = 1 or CN = -5
        elif int(row[14]) == 1 or int(row[14]) == -5:
            # if DNA_refCount > DNA_altCount
            if int(row[12]) > int(row[13]):
                return f"{(int(row[9])/int(row[10]))/4}" # (RNA_refCount/RNA_altCount)/4 : CNV_ratio: 4/1
            # if DNA_refCount < DNA_altCount
            else:
                return f"{(int(row[9])/int(row[10]))/0.25}" # (RNA_refCount/RNA_altCount)/0.25 : CNV_ratio: 1/4


    def calculate_pValue_CNV(self, misc, row):
        '''This function determines what CN value that should be used when calculating the pValue_CNV'''

        # -4 : AABB    4 : AAAB
		# -5 : AAABB   5 AAAAB

        # CN = 2 or CN = -4
        if int(row[14]) == 2 or int(row[14]) == -4:
            return f"{binom_test(int(row[9]), int(row[11]), 0.5)}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 1/2

        # CN = 3
        elif int(row[14]) == 3:
            # if DNA_refCount > DNA_altCount
            if int(row[12]) > int(row[13]):
                return f"{binom_test(int(row[9]), int(row[11]), float(2/3))}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 2/3
            # if DNA_refCount < DNA_altCount
            else:
                return f"{binom_test(int(row[9]), int(row[11]), float(1/3))}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 1/3

        # CN = 5
        elif int(row[14]) == 5:
            # if DNA_refCount > DNA_altCount
            if int(row[12]) > int(row[13]):
                return f"{binom_test(int(row[9]), int(row[11]), 0.6)}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 3/5
            # if DNA_refCount < DNA_altCount
            else:
                return f"{binom_test(int(row[9]), int(row[11]), 0.4)}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 2/5

        # CN = 1 or CN = -5
        elif int(row[14]) == 1 or int(row[14]) == -5:
            # if DNA_refCount > DNA_altCount
            if int(row[12]) > int(row[13]):
                return f"{binom_test(int(row[9]), int(row[11]), 0.8)}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 4/5
                # if DNA_refCount < DNA_altCount
            else:
                return f"{binom_test(int(row[9]), int(row[11]), 0.2)}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 1/5

        # CN = 4
        elif int(row[14]) == 4:
            # if DNA_refCount > DNA_altCount
            if int(row[12]) > int(row[13]):
                return f"{binom_test(int(row[9]), int(row[11]), 0.75)}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 3/4
            # if DNA_refCount < DNA_altCount
            else:
                return f"{binom_test(int(row[9]), int(row[11]), 0.25)}" # Input: RNA_refCount, RNA_totalCount, CNV_ratio: 1/4
