import filecmp
import subprocess
import sys
import os
from datetime import datetime
from os import path
from timeit import default_timer as timer
from shutil import which
from shutil import copy2

NewNameFile = '{year}{month}{day}_{hour}{minute}{second}{filetype}'
NewNameFolder = '{year}-{month}-{day}'
Output = ''
FolderList = []
Order = ''

NFilesProcessed = 0
NFilesConverted = 0
NFolders = 0

delete = ['changedFiles.txt', 'notChangedFiles.txt', 'error.txt']
videoFiletype = ['.3gp', '.mp4', '.avi', '.mov']
imageFiletype = ['.jpg', '.jpeg', '.png']


# Method that is called if the user wants to delete the log files. There are two options: all log files or all log files
# with nothing inside of it. Searches in all directories.
def delete_all(option):
    for folder in FolderList:
        for file in os.listdir(folder):
            if path.isfile(os.path.join(folder, file)) and file in delete \
                    and ((option == 1 and os.path.getsize(os.path.join(folder, file)) == 0) or option == 0):
                os.remove(os.path.join(folder, file))


# Manage the string received and change it to a name, considering the syntax above defined
def create_name(string, filetype):
    first, second = string.split(' ', 1)
    y, m, d = first.split(':', 2)
    h, mn, s = second.split(':', 2)
    return NewNameFile.format(year=y, month=m, day=d, hour=h, minute=mn, second=s, filetype=filetype)


# If 'exiftool.exe' file exists, this will execute this file with the media file to see its properties
# If a specific property of the media file exists, this will call another method to create a name
# If 'exiftool.exe' doesn't exist, this will send an error to stderr
def exiftool_process(filepath, filename, filetype):
    global Command
    if os.path.exists(Command) or which(Command) is not None:
        process = subprocess.Popen([Command, os.path.join(filepath, filename)], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        line = next((x for x in process.stdout.readlines() if x.decode('ISO-8859-1').startswith('Create Date')
                     or x.decode('ISO-8859-1').startswith('Date/Time Original')), None)
        if line is not None:
            name = line.decode('ISO-8859-1')[-21:-1].replace('\r', '').replace('\t', '').replace('\n', '')
            if len(name) == 19 and name.count(':') == 4 and name.count(' ') == 1:
                return create_name(name, filetype)
            else:
                return ''
        else:
            return ''
    else:
        sys.stderr.write('An error occurred: Exiftool program/Command missing. Please install it.')
        print("Check error.txt file")
        quit()


# This method will rename the media file, in case of the file has not the correct syntax.
# It checks if the name already exists and, if yes, will add parenthesis and a number until this name be unique
def change_name(changedfiles, notchangedfiles, filepath, filename, name):
    global NFilesConverted
    NFilesConverted += 1
    counter = 0

    while os.path.isfile(os.path.join(filepath, name)) and \
            not filecmp.cmp(os.path.join(filepath, filename), os.path.join(filepath, name), shallow=False):
        counter += 1
        pointIndex = name.rfind('.')
        filetype = name[pointIndex:]
        name = name[:pointIndex]

        if counter != 1:
            name = name[:name.rfind(' ')]
        name = name + ' (' + str(counter) + ')' + filetype

    if os.path.isfile(os.path.join(filepath, name)) and filecmp.cmp(os.path.join(filepath, filename),
                                                                    os.path.join(filepath, name), shallow=False):
        notchangedfiles.write(datetime.now().strftime('%H:%M:%S') + ' - ' + filename + ' has the correct syntax\n')
    else:
        os.rename(os.path.join(filepath, filename), os.path.join(filepath, name))
        changedfiles.write(datetime.now().strftime('%H:%M:%S') + ' - ' + filename + ' changed to ' + name + '\n')


# This method checks if some folder exists and, if not, creates. Alo return folder's name.
def create_folder(filename):
    filename = filename[:8]
    foldername = os.path.join('Output', NewNameFolder.format(year=filename[:4], month=filename[4:6], day=filename[6:8]))

    if not os.path.isdir(foldername):
        os.mkdir(foldername)

    return foldername


# This method manages the media files received, call methods to get file properties
# and to change its name. Moreover, it creates two logs about files with name changed or not.
# Also counts the number of files processed.
def file_properties(filepath, filename, filetype):
    global NFilesProcessed
    changedfiles = open(os.path.join(filepath, 'changedFiles.txt'), 'a+')
    notchangedfiles = open(os.path.join(filepath, 'notChangedFiles.txt'), 'a+')
    NFilesProcessed += 1

    name = exiftool_process(filepath, filename, filetype)
    if name != '':
        if Order.lower() == 'y':
            if not os.path.isdir('Output'):
                os.mkdir('Output')
            newfilepath = create_folder(name)
            copy2(os.path.join(filepath, filename), newfilepath)
            filepath = newfilepath
        change_name(changedfiles, notchangedfiles, filepath, filename, name)
    else:
        notchangedfiles.write(
            datetime.now().strftime('%H:%M:%S') + ' - ' + "WARNING: There's no metadata in " + filename + '\n')

    changedfiles.close()
    notchangedfiles.close()


# Method that manages the files of every folder of a folder's list
def process_folders(folderlist):
    global NFolders
    for foldername in folderlist:
        NFolders += 1
        print('\nProcessing ' + foldername)
        for file in os.listdir(foldername):
            if path.isfile(os.path.join(foldername, file)):
                try:
                    filetype = '.' + file.lower().rsplit('.', 1)[1]
                    if filetype in imageFiletype or filetype in videoFiletype:
                        file_properties(foldername, file, filetype)
                except IndexError:
                    pass
        print(foldername + ' processed')


# Delete any folder of the list. Subdirectories of that folder are also deleted.
def delete_subdirectories(foldername):
    global FolderList
    FolderList = [x for x in FolderList if foldername not in x]


# Return a string with all elements of a folder's list
def makelist(flist):
    ans = ''
    counter = 0
    for k in flist:
        ans = ans + '*-> ' + str(counter) + ': ' + k + '\n'
        counter += 1
    return ans


# Using a folder's list and a title, creates a string with a specific format
def listtostring(flist, tt):
    tt = tt.center(98)
    return ('*___________________________________________________________________________________________________'
            '_*\n*|' + tt + '|*\n*‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾'
                            '‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾*\n' + makelist(flist))


# Creates a dictionary about subdirectories. Each key is a path to every directory and its value is subdirectories of
# that directory
def subdirectories(foldername):
    subflist = list(filter(lambda subf: os.path.isdir(os.path.join(foldername, subf)), os.listdir(foldername)))
    for x in subflist:
        x = os.path.join(foldername, x)
        subdirectories(x)
        FolderList.append(x)


# Gets options from the user. He can choose if he wants to select or discard folders and, writing its number,
# builds a list of path to directories to process.
def selDisc_Folders():
    global FolderList
    os.system('cls' if os.name == 'nt' else 'clear')

    option = ''
    while option != '1' and option != '2':
        option = input('What do you prefer?\n1 - Select file directories to change its name ;  '
                       "2 - Discard file directories to change its name (If you want to select all, just type '2' and "
                       "then 'done')\n-> ")

    aux1 = ' select' if option == '1' else ' discard'
    aux3 = 'selected' if option == '1' else 'discarded'
    aux4 = ' ' if option == '1' else ''
    aux2 = '\nWarning: if you' + aux1 + ' a folder, all its subdirectories are ' + aux3 + '\n'

    os.system('cls' if os.name == 'nt' else 'clear')

    folderlist_backup = list(FolderList)

    folderlist = []
    foldrs = ''
    while foldrs.lower() != 'done' and len(FolderList) > 0 and FolderList != folderlist:
        print(listtostring(FolderList, 'Folder List'))
        print('\nPlease write the numbers of the directories you want to' + aux1 + '.\n' +
              'If you want to see the folders you' + aux1 + " write 'show'.\n" +
              "If you don't want to" + aux1 + " more directories, write 'done'." + aux2)
        foldrs = input('-> ')
        if foldrs.lower() == 'show':
            os.system('cls' if os.name == 'nt' else 'clear')
            print(listtostring(folderlist, 'Directories ' + aux3 + aux4))

            input('\nWrite anything to continue...\n-> ')
            print()
        elif foldrs.lower() != 'done':
            try:
                if int(foldrs) < len(FolderList):
                    delete_subdirectories(FolderList[int(foldrs)])
                    folderlist = list(set(folderlist_backup) - set(FolderList))
                    os.system('cls' if os.name == 'nt' else 'clear')
                else:
                    print("Invalid Number.")
            except ValueError:
                pass

    FolderList = folderlist if option == '1' else FolderList

    if len(FolderList) == 0 and option == '2':
        prepare = ''
        while prepare.lower() != 'y' and prepare.lower() != 'n':
            prepare = input('You discarded all directories, want to redo? Y - Yes ; N - No\n-> ')
        if prepare.lower() == 'y':
            FolderList = folderlist_backup
            selDisc_Folders()


# Turn elements of video and image filetypes list in string
def string_filetypes(video, image):
    videostring = 'Video filetypes: '
    imagestring = 'Image filetypes: '
    index = 0
    while index < len(video) or index < len(image):
        if index < len(video):
            videostring = videostring + str(index) + '. ' + video[index] + "   "
        if index < len(image):
            imagestring = imagestring + str(index + len(video)) + '. ' + image[index] + "   "
        index += 1

    return videostring + '\n' + imagestring


# Gets options from the user. He can choose if he wants to select or discard filetypes and, writing its number,
# builds a list of filetypes to process.
def selDisc_Filetypes():
    global videoFiletype, imageFiletype
    videolist = []
    imagelist = []

    os.system('cls' if os.name == 'nt' else 'clear')

    seldisc = ''
    while seldisc != '1' and seldisc != '2':
        seldisc = input("What do you prefer?\n1 - Select the types of file you want to process  ;  2 - Discard the "
                        "types of file you want to process (If you want to select all, just type '2' and then "
                        "'done')\n-> ")
    print()

    aux1 = ' select' if seldisc == '1' else ' discard'

    option = ''
    while option.lower() != 'done' and (len(videoFiletype) > 0 or len(imageFiletype) > 0) and \
            (videoFiletype != videolist or imageFiletype != imagelist):
        print('What types of file do you want to' + aux1 + "? Write 'done' when you finish\n" +
              string_filetypes(videoFiletype, imageFiletype))
        option = input('-> ')

        if option.lower() == 'show':
            os.system('cls' if os.name == 'nt' else 'clear')

            if seldisc == '1':
                print('\t\t\tSelected:\n' + string_filetypes(videolist, imagelist) + '\n')
            else:
                print('\t\t\tDiscarded:\n' + string_filetypes(videolist, imagelist) + '\n')

            input('\nWrite anything to continue...\n-> ')
            print()
        else:
            try:
                index = int(option)
                if index < 10:
                    if index == 8:
                        videolist.extend(videoFiletype)
                        videoFiletype.clear()
                    elif index == 9:
                        imagelist.extend(imageFiletype)
                        imageFiletype.clear()
                    elif index < len(videoFiletype):
                        videolist.append(videoFiletype[index])
                        del videoFiletype[index]
                    elif index - len(videoFiletype) < len(imageFiletype) \
                            and index - len(videoFiletype) < len(imageFiletype):
                        imagelist.append(imageFiletype[index - len(videoFiletype)])
                        del imageFiletype[index - len(videoFiletype)]
                    print()
            except ValueError:
                option = 'done'

    if seldisc == '1':
        videoFiletype = videolist
        imageFiletype = imagelist
    elif len(videoFiletype) == 0 and len(imageFiletype) == 0:
        prepare = ''
        while prepare.lower() != 'y' and prepare.lower() != 'n':
            prepare = input('You discarded all filetypes, want to redo? Y - Yes ; N - No\n-> ')
        if prepare.lower() == 'y':
            videoFiletype = videolist
            imageFiletype = imagelist
            selDisc_Filetypes()


# Gets options from the user. He can choose if he wants to create folders according to file's name.
def selOrder():
    global Order
    while Order.lower() != 'y' and Order.lower() != 'n':
        Order = input("\nDo you want to create folders according to creation date's photos?  Y - Yes    ;  N - No\n"
                      '\tExample: in folder 2021-12-01 there are only photos taken in 2021-12-01\n-> ')


def main():
    print("Hi! I am a tool that changes '.3gp', '.mp4', '.avi', '.mov', '.jpg', '.jpeg' and '.png' name's file "
          'according to its creation date.')
    print('\tI give you an example: helloIamAnImage.jpg ----- if it has creation date ------> 20211205_042000.jpg')

    selOrder()
    selDisc_Filetypes()
    selDisc_Folders()
    os.system('cls' if os.name == 'nt' else 'clear')

    if len(FolderList) > 0 and (len(videoFiletype) > 0 or len(imageFiletype) > 0):
        print('\nList of folders to process created. Changing the names...')
        sys.stderr = open('error.txt', 'a+')

        tic = timer()
        process_folders(FolderList)
        toc = timer()
        t = toc - tic

        sys.stderr.close()
        os.system('cls' if os.name == 'nt' else 'clear')

        print('Folders: ' + str(NFolders) + '. Files processed: ' + str(NFilesProcessed) + '. File with name changed: '
              + str(NFilesConverted) + ('. Time spent: %.2f ' % t) + 'seconds')

        print('\nDeleting empty logs...')
        delete_all(1)
        print('Deleted')

        ans2 = ''
        while ans2.lower() != 'y' and ans2.lower() != 'n':
            ans2 = input('\nDo you want to remove the log files and error files of all folders (You can come here '
                         'after read every log)? Y - Yes ; N - No\n-> ')

        if ans2.lower() == 'y':
            delete_all(0)
            print('All logs deleted.')

    else:
        print("No folders to process. Shutting down program.") if len(FolderList) > 0 else print("No files to "
                                                                                                 "process. Shutting "
                                                                                                 "down program.")

    print('\nMade by Henrique Alvelos.'
          '\nCheck my Github profile: https://github.com/Henrique-190'
          '\nBuy me a coffee: https://www.paypal.com/paypalme/henriquealvelos'
          '\nBye! ')


os.system('cls' if os.name == 'nt' else 'clear')
if os.path.exists('exiftool.exe') or which('exiftool') is not None:
    subdirectories(os.getcwd())
    if which('exiftool') is not None:
        Command = 'exiftool'
    else:
        Command = 'exiftool.exe'
    main()
else:
    print('Please download or install exiftool.')
