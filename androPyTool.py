import os
import sys
import shutil
import argparse

from time import sleep
from os import listdir
from termcolor import colored
from os.path import join as join_dir
from argparse import RawTextHelpFormatter

from APT_1_filterValidApks import filter_valid_apks
from APT_2_virustotal_analyser import analyse_virustotal
from APT_3_filter_bw_mw import filter_apks
from APT_4_launch_flowdroid import run_flowdroid
from APT_5_process_flowdroid_outputs import process_flowdroid_outputs
from APT_6_feat_extraction import features_extractor
from DroidBox_AndroPyTool.fork_droidbox import analyze_with_droidbox
from DroidBox_AndroPyTool.droidboxOutputsManaging import parse_droidbox_outputs

"""
FOLDERS STRUCTURE GENERATED BY ANDROPYTOOL

# /                     --> root folder
# /samples/             --> samples, originally in the root folder
# /samples/BW           --> benignware samples
# /samples/MW           --> malware samples
# /invalid_apks/        --> invalid apks found
# /VT_analysis/         --> VirusTotal analysis reports
# /FlowDroid_outputs/   --> flowdroid results
# /FlowDroid_processed/ --> flowdroid results processed
# /DroidBox_outputs/    --> DroidBox outputs raw
# /Dynamic/Droidbox/    --> Droidbox analysis in JSON
# /Dynamic/Strace/      --> Strace analysis in CSV
# /Features_files/      --> Features files generated with AndroPyTool

"""

# PATHS USED BY ANDROPYTOOL TO SAVE ALL GENERATED FILES
APKS_DIRECTORY = "samples/"
BW_DIRECTORY = "samples/BW"
MW_DIRECTORY = "samples/MW"
INVALID_APKS_DIRECTORY = "invalid_apks/"
VIRUSTOTAL_FOLDER = "VT_analysis/"
FLOWDROID_RESULTS_FOLDER = "FlowDroid_outputs/"
FLOWDROID_PROCESSED_FOLDER = "FlowDroid_processed/"
DROIDBOX_RESULTS_FOLDER = "DroidBox_outputs/"
DYNAMIC_ANALYSIS_FOLDER = "Dynamic/"
DYNAMIC_DROIDBOX_ANALYSIS = "Droidbox/"
DYNAMIC_STRACE_ANALYSIS = "Strace/"
FEATURES_FILES = "Features_files/"

# VIRUSTOTAL_THRESHOLD = 1
OUTPUT_GLOBAL_FILE_FLOWDROID = "flowdroid_global.csv"
DROIDBOX_GUI_MODE = False

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

os.chdir(CURRENT_DIRECTORY)


def main():

    parser = argparse.ArgumentParser(description=colored("Welcome to AndroPyTool\n\n", "green") +
                                                 "[!] You must provide the source directory where apks are contained. ",
        formatter_class=RawTextHelpFormatter)

    # add the program arguments to parser
    add_parser_args(parser)
    parser.set_defaults(color=True)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    source_folder, step_analyse_virus_total, step_filter_apks, step_filter_bw_mw, step_run_droidbox, step_run_flowdroid = set_up_args(
        args)

    if step_analyse_virus_total is False and step_filter_bw_mw is True:
        print "ERROR!: Option -cl --classify requires -vt --virustotal_api_key."
        sys.exit(0)

    execute_andro_py_tool_steps(source_folder=source_folder,
                                step_filter_apks=step_filter_apks,
                                step_filter_bw_mw=step_filter_bw_mw,
                                step_run_flowdroid=step_run_flowdroid,
                                step_run_droidbox=step_run_droidbox,
                                save_single_analysis=args.single,
                                perform_nocleanup=args.nocleanup,
                                package_index=args.packageIndex,
                                class_index=args.classIndex,
                                system_commands_index=args.systemCommandsIndex,
                                export_mongodb=args.mongodbURI,
                                exportCSV=args.exportCSV,
                                with_color=args.color,
                                vt_threshold=args.virustotal_threshold,
                                droidbox_time=args.droidbox_time,
                                virus_total_api_key=step_analyse_virus_total
                                )


def set_up_args(args):
    """
    set up the parameters used in the steps
    :param args: the parameters
    :return:
    """
    source_folder = args.source
    step_filter_apks = True
    step_analyse_virus_total = args.virustotal_api_key
    step_filter_bw_mw = True
    step_run_flowdroid = True
    step_run_droidbox = True
    if not args.allsteps:
        step_filter_apks = args.filter
        step_analyse_virus_total = args.virustotal_api_key
        step_filter_bw_mw = args.classify
        step_run_flowdroid = args.flowdroid
        step_run_droidbox = args.droidbox
    return source_folder, step_analyse_virus_total, step_filter_apks, step_filter_bw_mw, step_run_droidbox, step_run_flowdroid


def add_parser_args(parser):
    """
    add the program arguments to parser
    :param parser: a parser to command line arguments
    :return:
    """
    parser.add_argument('-all', '--allsteps', help='Executes all steps of AndroPyTool (Recommended). In order to obtain'
                                                   ' a VirusTotal report, the argument -vt must be also provided '
                                                   'followed by a VirusTotal API key. If the -all option is '
                                                   'not provided, then only the last step is executed plus the '
                                                   'provided arguments. ', action='store_true')
    parser.add_argument('-s', '--source', help='Source directory for APKs', required=True)
    parser.add_argument('-S', '--single', default=True,
                        help='Save single analysis separately. Default: False.',
                        action='store_true')
    parser.add_argument('-f', '--filter', help='Filter valid and invalid Apks (Recommended).', default=False,
                        required=False, action='store_true')
    parser.add_argument('-vt', '--virustotal_api_key', help='Analyse applications with the VirusTotal service. '
                                                            'It must be followed by a VirusTotal API key.',
                        default=None,
                        required=False)
    parser.add_argument('-threshold', '--virustotal_threshold',
                        help='Minimum number of antivirus engines testing positive for malware '
                             'necessary to consider a sample as malicious.', default=1,
                        required=False)
    parser.add_argument('-cl', '--classify', help='Classify apps between malware or benignware based on the'
                                                  'VirusTotal reports. --virustotal_api_key argument has to be set',
                        default=False, required=False, action='store_true')
    parser.add_argument('-fw', '--flowdroid', help='Run flowdroid.', default=False, required=False, action='store_true')
    parser.add_argument('-dr', '--droidbox', help='Run droidbox.', default=False, required=False, action='store_true')
    parser.add_argument('-c', '--nocleanup', default=False,
                        help='Perform cleanup deleting temporary working files. Default: True', action='store_true')
    parser.add_argument('-P', '--packageIndex', default='info/package_index.txt',
                        help='TXT file with all Android API packages. Default: info/package_index.txt')
    parser.add_argument('-C', '--classIndex', default='info/class_index.txt',
                        help='TXT file with all Android API classes. Default: info/class_index.txt')
    parser.add_argument('-SC', '--systemCommandsIndex', default='info/system_commands.txt',
                        help='TXT file with all System Commands. Default: info/system_commands.txt')
    parser.add_argument('-mg', '--mongodbURI', help='Exports the report generated to a mongodb database. Requires '
                                                    'connection address following the scheme: localhost:27017')
    parser.add_argument('-csv', '--exportCSV', help='Exports the report generated to a CSV file. Only static '
                                                    'features are included.')
    parser.add_argument('-drt', '--droidbox_time', default=300, required=False,
                        help='DroidBox running time in seconds. Default is 300s.')
    parser.add_argument('--color', dest='color', action='store_true')
    parser.add_argument('--no-color', dest='color', action='store_false')


def print_message(message, with_color, color):
    """
    Uses termcolor to print text in color
    :param message: the message to be printed
    :param with_color: if color is present
    :param color: the color value
    :return:
    """
    if with_color:
        print colored(message, color)
    else:
        print message


def execute_andro_py_tool_steps(source_folder, step_filter_apks, step_filter_bw_mw,
                                step_run_flowdroid, step_run_droidbox, save_single_analysis, perform_nocleanup,
                                package_index, class_index, system_commands_index, export_mongodb, exportCSV,
                                with_color, vt_threshold, droidbox_time, virus_total_api_key=None):

    """
    This method is used to launch all the different modules implemented in AndroPyTool.
    It generates a folder tree containing all generated reports and features files

    Parameters
    ----------
    :param source_folder: Source directory containing apks to extract features and perform analysis
    :param step_filter_apks:  If apks are filtered between valid or invalid apks using Androguard
    :param virus_total_api_Key: VirusTotal service API key
    :param step_filter_bw_mw: If apks are filtered between benignware and malware according to the Virustotal report
    :param step_run_flowdroid: If flowdroid is executed with all the samples
    :param step_run_droidbox: If droidbox is executed with all the samples
    :param save_single_analysis: If an individual features report is generated for each sample
    :param perform_nocleanup: If unnecesary files generated are removed
    :param package_index: File describing Android API packages
    :param class_index: File describing Android API classes
    :param system_commands_index: File describing Android system commands
    """
    # STEP 1 - Filter valid apks
    execute_step_one(source_folder, step_filter_apks, with_color)

    # STEP 2 - Analyse with VirusTotal
    execute_step_two(source_folder, virus_total_api_key, with_color)

    # STEP 3 - Filtering BW & MW
    execute_step_three(source_folder, step_filter_bw_mw, vt_threshold, with_color)

    # NOW APKS ARE CONTAINED IN DIFFERENT SUBFOLDERS
    # STEP 4 - Launch FlowDroid
    execute_step_four(source_folder, step_run_flowdroid, with_color)

    # STEP 5 - Process FlowDroid outputs
    execute_step_five(source_folder, step_run_flowdroid, with_color)

    # STEP 6 - Execute DroidBox
    execute_step_six(droidbox_time, source_folder, step_run_droidbox, with_color)

    # STEP 7 - Features extraction
    execute_step_seven(class_index, exportCSV, export_mongodb, package_index, perform_nocleanup, save_single_analysis,
                       source_folder, system_commands_index, with_color)


def execute_step_seven(class_index, exportCSV, export_mongodb, package_index, perform_nocleanup, save_single_analysis,
                       source_folder, system_commands_index, with_color):
    """
    STEP 7 - Features extraction
    """
    print_message("\n\n>>>> AndroPyTool -- STEP 7: Execute features extraction\n", with_color, "green")
    features_extractor(apks_directory=join_dir(source_folder, APKS_DIRECTORY),
                       single_analysis=save_single_analysis,
                       dynamic_analysis_folder=join_dir(source_folder, DYNAMIC_ANALYSIS_FOLDER),
                       virus_total_reports_folder=join_dir(source_folder, VIRUSTOTAL_FOLDER),
                       flowdroid_folder=join_dir(source_folder, FLOWDROID_PROCESSED_FOLDER),
                       output_folder=join_dir(source_folder, FEATURES_FILES),
                       noclean_up=perform_nocleanup,
                       package_index_file=package_index,
                       classes_index_file=class_index,
                       system_commands_file=system_commands_index,
                       label=None,
                       avclass=True,
                       export_mongodb=export_mongodb,
                       export_csv=exportCSV)


def execute_step_six(droidbox_time, source_folder, step_run_droidbox, with_color):
    """
    STEP 6 - Execute DroidBox
    """
    if step_run_droidbox:
        print_message("\n\n>>>> AndroPyTool -- STEP 6: Execute DroidBox\n", with_color, "green")

        analyze_with_droidbox(apks_folders=join_dir(source_folder, APKS_DIRECTORY),
                              duration=droidbox_time,
                              output_directory=join_dir(source_folder, DROIDBOX_RESULTS_FOLDER),
                              gui=DROIDBOX_GUI_MODE)

        parse_droidbox_outputs(source_folder=join_dir(source_folder, DROIDBOX_RESULTS_FOLDER),
                               output_droidbox=join_dir(source_folder, DYNAMIC_ANALYSIS_FOLDER,
                                                        DYNAMIC_DROIDBOX_ANALYSIS),
                               output_strace=join_dir(source_folder, DYNAMIC_ANALYSIS_FOLDER, DYNAMIC_STRACE_ANALYSIS),
                               output_other=join_dir(source_folder, DROIDBOX_RESULTS_FOLDER))

        # DroidBox changes the working directory, so let's set again the original directory:
        os.chdir(CURRENT_DIRECTORY)


def execute_step_five(source_folder, step_run_flowdroid, with_color):
    """
    STEP 5 - Process FlowDroid outputs
    """
    if step_run_flowdroid:
        print_message("\n\n>>>> AndroPyTool -- STEP 5: Processing FlowDroid outputs\n", with_color, "green")

        process_flowdroid_outputs(flowdroid_analyses_folder=join_dir(source_folder, FLOWDROID_RESULTS_FOLDER),
                                  output_folder_individual_csv=join_dir(source_folder, FLOWDROID_PROCESSED_FOLDER),
                                  output_csv_file=join_dir(source_folder, FLOWDROID_PROCESSED_FOLDER,
                                                           OUTPUT_GLOBAL_FILE_FLOWDROID),
                                  with_color=with_color)

        sleep(1)


def execute_step_four(source_folder, step_run_flowdroid, with_color):
    """
    STEP 4 - Launch FlowDroid
    """
    if step_run_flowdroid:
        print_message("\n\n>>>> AndroPyTool -- STEP 4: Launching FlowDroid\n", with_color, "green")

        run_flowdroid(source_directory=join_dir(source_folder, APKS_DIRECTORY),
                      output_folder=join_dir(source_folder, FLOWDROID_RESULTS_FOLDER),
                      with_color=with_color)

        sleep(1)


def execute_step_three(source_folder, step_filter_bw_mw, vt_threshold, with_color):
    """
    STEP 3 - Filtering BW & MW
    """
    if step_filter_bw_mw:
        print_message("\n\n>>>> AndroPyTool -- STEP 3: Filtering BW and MW\n", with_color, "green")

        filter_apks(source_directory=join_dir(source_folder, APKS_DIRECTORY),
                    vt_analysis_directory=join_dir(source_folder, VIRUSTOTAL_FOLDER),
                    bw_directory_name=join_dir(source_folder, BW_DIRECTORY),
                    mw_directory_name=join_dir(source_folder, MW_DIRECTORY),
                    threshold=vt_threshold)

        sleep(1)


def execute_step_two(source_folder, virus_total_api_key, with_color):
    """
    STEP 2 - Analyse with VirusTotal
    """
    if virus_total_api_key is not None:
        print_message("\n\n>>>> AndroPyTool -- STEP 2: Analysing with VirusTotal\n", with_color, "green")

        analyse_virustotal(source_directory=join_dir(source_folder, APKS_DIRECTORY),
                           vt_analysis_output_folder=join_dir(source_folder, VIRUSTOTAL_FOLDER),
                           output_samples_folder=join_dir(source_folder, APKS_DIRECTORY),
                           with_color=with_color, vt_api_key=virus_total_api_key)

        sleep(1)


def execute_step_one(source_folder, step_filter_apks, with_color):
    """
    STEP 1 - Filter valid apks
    """
    if step_filter_apks:
        print_message("\n\n>>>> AndroPyTool -- STEP 1: Filtering apks\n", with_color, "green")

        filter_valid_apks(source_directory=source_folder,
                          valid_apks_directory=join_dir(source_folder, APKS_DIRECTORY),
                          invalid_apks_directory=join_dir(source_folder, INVALID_APKS_DIRECTORY),
                          with_color=with_color)

        sleep(1)

    else:
        # If this step is not executed, all samples must be moved to the /samples/ directory
        if not os.path.exists(join_dir(source_folder, APKS_DIRECTORY)):
            os.makedirs(join_dir(source_folder, APKS_DIRECTORY))

        list_apks = [f for f in listdir(source_folder) if f.endswith(".apk")]
        for apk in list_apks:
            shutil.move(join_dir(source_folder, apk), join_dir(source_folder, APKS_DIRECTORY, apk))


if __name__ == '__main__':
    main()
