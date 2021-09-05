import subprocess
import os
from timeit import default_timer as timer
import sys
from os import path

sys.stderr = open('error.txt', 'a+')

newname = '{year}{month}{day}-{hour}{minute}{second}{filetype}'
output = ''
folderDict = {}

nfilesprocessed = 0
nfilesconverted = 0
nfolders = 0

delete = ['changedFiles.txt', 'notChangedFiles.txt', 'error.txt']
videofiletype = ['.3gp', '.mp4', '.avi']
imagefiletype = ['.jpg', '.jpeg', '.png']


# Method that is called if the user wants to delete all the log files.
# It searches in all directories.
def delete_all(foldername):
    for file in os.listdir(foldername):
        if path.isfile(os.path.join(foldername, file)):
            if file in delete:
                os.remove(os.path.join(foldername, file))
        elif path.isdir(os.path.join(foldername, file)):
            delete_all(os.path.join(foldername, file))


# Method in charge of manage the string received and change it to a name, considering the syntax above defined
def create_name(string, filetype):
    first, second = string.split(' ', 1)
    y, m, d = first.split(':', 2)
    h, mn, aux = second.split(':', 2)
    s = aux[:-1]
    return newname.format(year=y, month=m, day=d, hour=h, minute=mn, second=s, filetype=filetype)


# If 'exiftool.exe' file exists, this will execute this file with the media file to see its properties
# If a specific property of the media file exists, this will call another method to create a name
# If it doesn't exists, this will send an error to stderr
def exiftool_process(filepath, filename, filetype):
    if os.path.exists('exiftool.exe'):
        process = subprocess.Popen(['exiftool.exe', os.path.join(filepath, filename)], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, universal_newlines=True)
        for otp in process.stdout:
            if otp.startswith('Create Date') and filetype in videofiletype:
                return create_name(otp[-20:], filetype)
            elif otp.startswith('Date/Time Original') and filetype in imagefiletype:
                return create_name(otp[-20:], filetype)
    else:
        sys.stderr.write('ERROR: exiftool.exe file missing.')
    return ''


# This method will rename the media file. It checks if the name already exists and,
# if yes, will add parenthesis and a number until this name be unique
def change_name(outputfile, filepath, filename, name):
    global nfilesconverted
    nfilesconverted += 1
    counter = 0
    while os.path.isfile(os.path.join(filepath, name)):
        counter += 1
        filetype = name[-4:]
        if counter != 1:
            name = name[:-7]
        else:
            name = name[:-4]
        name = name + '(' + str(counter) + ')' + filetype
    os.rename(os.path.join(filepath, filename), os.path.join(filepath, name))
    outputfile.write(filename + ' changed to ' + name + '\n')


# This method manages the media files received, call methods to get file properties
# and to change its name. Moreover, it creates two logs about files with name changed or not.
# Also counts the number of files processed.
def file_properties(filepath, filename):
    changedfiles = open(os.path.join(filepath, 'changedFiles.txt'), 'a+')
    notchangedfiles = open(os.path.join(filepath, 'notChangedFiles.txt'), 'a+')
    global nfilesprocessed
    nfilesprocessed += 1

    if filename.lower()[-4:] in imagefiletype:
        name = exiftool_process(filepath, filename, filename.lower()[-4:])
        if name != '':
            change_name(changedfiles, filepath, filename, name)
        else:
            notchangedfiles.write("WARNING: There's no metadata in " + filename + '\n')
    elif filename.lower()[-5:] in imagefiletype:
        name = exiftool_process(filepath, filename, filename.lower()[-5:])
        if name != '':
            change_name(changedfiles, filepath, filename, name)
        else:
            notchangedfiles.write("WARNING: There's no metadata in " + filename + '\n')
    elif filename.lower()[-4:] in videofiletype:
        name = exiftool_process(filepath, filename, filename.lower()[-4:])
        if name != '':
            change_name(changedfiles, filepath, filename, name)
        else:
            notchangedfiles.write("WARNING: There's no metadata in " + filename + '\n')

    changedfiles.close()
    notchangedfiles.close()


# Method that manages the files of every folder of a folder list
def process_folders(folderlist):
    global nfolders
    for foldername in folderlist:
        nfolders += 1
        for file in os.listdir(foldername):
            if path.isfile(os.path.join(foldername, file)):
                file_properties(foldername, file)


# Delete any folder of the dictionary, checking one key and every values. Subdirectories of that folder are also
# deleted.
def delete_subdirectories(foldername):
    global folderDict
    for k in folderDict:
        if foldername == k:
            for subd in list(folderDict[k]):
                delete_subdirectories(os.path.join(foldername, subd))
            folderDict = {key: val for key, val in folderDict.items() if key != k}
        elif os.path.isdir(k):
            for subd in folderDict[k]:
                if foldername == os.path.join(k, subd):
                    folderDict[k].remove(subd)


# Using the folderDict, prints with a specific format
def print_dict():
    print(
        '\n\n\n*____________________________________________________________________________________________________*\n'
        '*|                                           Folder List                                            |*\n'
        '*‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾*\n')
    counter = 0
    for k in folderDict.keys():
        subd = ""
        for v in folderDict[k]:
            subd += (v + '  ;  ')
        if len(subd) > 0:
            subd = subd[:-3]
        print(str(counter) + ' ' + k + ':\n          ' + subd)
        counter += 1


# Creates a dictionary about subdirectories. Each key is a path to every directory and its value is subdirectories of
# that directory
def subdirectories(foldername):
    subflist = list(filter(lambda subf: os.path.isdir(os.path.join(foldername, subf)), os.listdir(foldername)))
    for x in subflist:
        x = os.path.join(foldername, x)
        subdirectories(x)
    folderDict[foldername] = subflist


# Gets options from the user. He can choose if he wants to select or discard folders and, writing its number,
# builds a list of path to directories to process.
def select_discard():
    option = ''
    while option != '1' and option != '2':
        option = input('\nWhat do you prefer?\n1 - Select the directories to change the name ;  '
                       '2 - Discard the directories to change the name\n-> ')

    if option == '1':
        aux1 = ' select'
        aux2 = '\nWarning: if you select a folder, all the subdirectories are selected\n'
    else:
        aux1 = ' discard'
        aux2 = '\nWarning: if you discard a folder, all the subdirectories are discarded\n'

    folderlist = []
    folderDictBackup = list(folderDict.keys())
    print_dict()

    foldrs = '1'
    while foldrs.lower() != 'done':
        foldrs = input('\nPlease write the numbers of the directories you want to' + aux1 + '.\n' +
                       'If you want only to' + aux1 + " a subdirectory, search upper, there will be its number" +
                       ' If you want to see the folders again, write show .\n' +
                       "If you don't want to select more directories, write 'done'." + aux2 + '-> ')
        if foldrs.lower() == 'show':
            print_dict()
            if option == '1':
                print(
                    '\n\n\n*_________________________________________________________________________________________'
                    '*\n '
                    '*|                                  Directories selected                                 |*\n'
                    '*‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾*\n')
                for x in folderlist:
                    print(x)
        elif foldrs != 'done':
            try:
                if int(foldrs) < len(list(folderDict.keys())):
                    delete_subdirectories(list(folderDict.keys())[int(foldrs)])

                if option == '1':
                    folderlist = list(set(folderDictBackup) - set(list(folderDict.keys())))
                else:
                    folderlist = list(folderDict.keys())
            except ValueError:
                foldrs = ''
    if len(folderlist) == 0 and option == '2':
        folderlist = list(folderDict.keys())

    print('List of folders to process created. Changing the names...')
    return folderlist


def main():
    print("Hi! I am a tool that changes '.3gp', '.mp4', '.avi', '.jpg', '.jpeg' and '.png' name file according to its "
          "creation date.")
    print('\nI give you an example: helloIamAnImage.jpg -----------> 20211205-042000')

    folderlist = select_discard()
    tic = timer()
    process_folders(folderlist)
    toc = timer()
    t = toc - tic

    sys.stderr.close()
    print('\n\nFolders: ' + str(nfolders) + '. Files processed: ' + str(nfilesprocessed)
          + '. File with name changed: ' + str(nfilesconverted) + ('. Time spent: %.2f ' % t) + 'seconds')

    ans2 = ''
    while ans2.lower() != 'y' and ans2.lower() != 'n':
        ans2 = input('Do you want to remove the log files and error files of all folders? Y - Yes ; N - No\n-> ')

    if ans2.lower() == 'y':
        delete_all(os.getcwd())
        print('Done.')

    print('\nMade by Henrique Alvelos. '
          '\nCheck my Github profile: https://github.com/Henrique-190'
          '\nBuy me a coffee: https://www.paypal.com/paypalme/henriquealvelos'
          '\nBye! ')


subdirectories(os.getcwd())
main()
