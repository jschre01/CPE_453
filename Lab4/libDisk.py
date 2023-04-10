import os.path

BLOCKSIZE = 256
Disks = []
Disk = 0

class Disk:
    
    def __init__(self, name, stream):
        self.name = name
        self.stream = stream
        self.open = True
        self.Dynamic_Resource_Table = []
        self.File_Pointer_Table = []

class libDisk:

    #Initializes libDisk
    def __init__(self):
        self.BLOCKSIZE = 256
        self.Disks = []
        self.Disk = 0
        self.Mounted = -1

    #Interface function opens a disk
    def openDisk(self, filename, nBytes):
        d = self.Disk
        if nBytes > 0:
            if os.path.exists(filename):
                f = open(filename, "w+")
                for i in range(len(self.Disks)):
                    if self.Disks[i].name == filename:
                        self.Disks[i].open = True
                        self.Disks[i].stream = f
                        return i
            else:
                f = open(filename, "w+")
        else:
            if os.path.exists(filename):
                f = open(filename, "r+")
                for i in range(len(self.Disks)):
                    if self.Disks[i].name == filename:
                        self.Disks[i].open = True
                        self.Disks[i].stream = f
                        return i
            else:
                return -1
        newDisk = Disk(filename, f)
        self.Disks.append(newDisk)
        self.Disk += 1
        return d

    #Interface function reads a block from disk
    def readBlock(self, disk, bNum, block):
        if disk >= self.Disk:
            return -2
        curr = self.Disks[disk].stream
        curr.seek(bNum*self.BLOCKSIZE)
        block.contents = curr.read(self.BLOCKSIZE)
        return 0

    #Interface function writes a block to disk
    def writeBlock(self, disk, bNum, block):
        if disk >= self.Disk:
            return -2
        curr = self.Disks[disk].stream
        curr.seek(bNum*self.BLOCKSIZE)
        w = block.contents[:self.BLOCKSIZE]
        curr.write(w)
        return 0

    #Interface function that closes disk
    def closeDisk(disk):
        self.Disks[disk].stream.close()
        self.Disks[disk].open = False

