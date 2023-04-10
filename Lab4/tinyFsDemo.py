from libTinyFS import *

DEFAULT_DISK_SIZE = 10240

#Function that displays user options
def displayOptions():
    print("t - create tfs disk")
    print("m - mount tfs disk")
    print("u - unmount tfs disk")
    print("o - open a file")
    print("c - close a file")
    print("w - write to a file")
    print("d - delete a file")
    print("r - read a single byte")
    print("f - read an entire file")
    print("s - set file pointer to new offset")
    print("n - rename a file")
    print("p - print all files on disk")
    print("b - display fragments")
    print("e - defragment disk system")
    print("i - display options")
    print("q - quit")

#Function that handles error codes and displays corresponding message
def displayErrorMessage(i):
    if i == -1:
        print("Error: Attempting to open existing file that doesnt exist")
    if i == -2:
        print("Error: Attempting to access disk that does not exist")
    if i == -3:
        print("Error: Disk not of the correct type")
    if i == -4:
        print("Error: Attempting to mount disk that does not exist")
    if i == -5:
        print("Error: Filename must be 8 characters or shorter")
    if i == -6:
        print("Error: Disk has already reached capacity")
    if i == -7:
        print("Error: Failed to close file")
    if i == -8:
        print("Error: File descriptor does not exist")
    if i == -9:
        print("Error: Reached end of file")
    if i == -10:
        print("Error: Offset out of bound of file")
    if i == -11:
        print("Error: Input must be an int")
    if i == -12:
        print("Error: File name cannot be integer")
    if i == -13:
        print("Error: No disk mounted to system")

#Driver function for demo program
def main():
    print("Welcome to Tiny FS Demo!")
    displayOptions()
    option = input("Enter option: ")
    while option != 'q':
        if option == 't':
            name = input("Enter disk name: ")
            i = tfs_mkfs(name, DEFAULT_DISK_SIZE)
            if i < 0:
                displayErrorMessage(i)
            else:
                print("Successfully created disk")
        elif option == 'm':
            name = input("Enter disk to mount: ")
            i = tfs_mount(name)
            if i < 0:
                displayErrorMessage(i)
            else:
                print("Successfully mounted disk")
        elif option == 'u':
            tfs_unmount()
            print("Successfully unmounted disk")
        elif option == 'o':
            name = input("Enter name of file: ")
            i = tfs_openFile(name)
            if i < 0:
                displayErrorMessage(i)
            else:
                print("Succesfully opened file with FD", i)
        elif option == 'c':
            try:
                fd = int(input("Enter FD: "))
                i = tfs_closeFile(fd)
                if i < 0:
                    displayErrorMessage(i)
                else:
                    print("Successfully closed file")
            except:
                displayErrorMessage(-11)

        elif option == 'w':
            try:
                fd = int(input("Enter FD: "))
                buff = input("Enter data to write to file: ")
                i = tfs_writeFile(fd, buff, len(buff))
                if i < 0:
                    displayErrorMessage(i)
                else:
                    print("Successfully wrote to file")
            except:
                displayErrorMessage(-11)
        elif option == 'd':
            try:
                fd = int(input("Enter FD: "))
                i = tfs_deleteFile(fd)
                if i < 0:
                    displayErrorMessage(i)
                else:
                    print("Successfully deleted file")
            except:
                displayErrorMessage(-11)
        elif option == 'r':
            try:
                fd = int(input("Enter FD: "))
                i = tfs_readByte(fd)
                if type(i) is int and i < 0:
                    displayErrorMessage(i)
                else:
                    print("Successfully read byte: ", i)
            except:
                displayErrorMessage(-11)
        elif option == 'f':
            try:
                fd = int(input("Enter FD: "))
                string = ""
                char = tfs_readByte(fd)
                if char == -8:
                    displayErrorMessage(-8)
                else:    
                    while(char != -9):
                        string += char
                        char = tfs_readByte(fd)
                    print(string)
            except:
                displayErrorMessage(-11)
        elif option == 's':
            try:
                fd = int(input("Enter FD: "))
                offset = int(input("Enter offset: "))
                i = tfs_seek(fd, offset)
                if i < 0:
                    displayErrorMessage(i)
                else:
                    print("Successfully set file pointer")
            except:
                displayErrorMessage(-11)
        elif option == 'n':
            try:
                fd = int(input("Enter FD: "))
                name = input("Enter new name: ")
                i = tfs_rename(fd, name)
                if i < 0:
                    displayErrorMessage(i)
                else:
                    print("Successfully renamed file")
            except:
                displayErrorMessage(-11)
        elif option == 'p':
            tfs_readdir()
        elif option == 'b':
            tfs_displayFragments()
        elif option == 'e':
            i = tfs_defrag()
            if i < 0:
                displayErrorMessage(i)
            else:
                print("Successfully defragmented file system")
        elif option == 'i':
            displayOptions()
        option = input("Enter option: ")

if __name__ == "__main__":
    main()
