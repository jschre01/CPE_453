from libDisk import *

BLOCKSIZE = 256
DEFAULT_DISK_SIZE = 10240
DEFAULT_DISK_NAME = "tinyFSDisk"

libDisk = libDisk()

class Buffer:

    def __init__(self, contents):
        self.contents = contents

#Interface function creates a new disk
def tfs_mkfs(filename, nBytes):
    i = libDisk.openDisk(filename, nBytes)
    if i >= 0:
        superblock = str(1) + '\x45' + str(1) + str(0)+ str(2) + (BLOCKSIZE-5)*'\x00'
        buff = Buffer(superblock)
        j = libDisk.writeBlock(i, 0, buff)
        if j < 0: 
            return j
        root_inode = str(2) + '\x45' + (BLOCKSIZE-2)*'\x00'
        buff = Buffer(root_inode)
        j = libDisk.writeBlock(i, 1, buff)
        if j < 0:
            return j
        block_num = int(DEFAULT_DISK_SIZE/BLOCKSIZE)
        for k in range(2, block_num):
            if k + 1 < 10:
                free_block = str(4) + '\x45' + str(0) + str(k+1)
            elif k + 1 != block_num:
                free_block = str(4) + '\x45' + str(k+1)
            else:
                free_block = str(4) + '\x45' + '\x00'*2
            free_block += (BLOCKSIZE-4)*'\x00'
            buff = Buffer(free_block)
            j = libDisk.writeBlock(i, k, buff)
            if j < 0:
                return j
        return 0
    else:
        return i

#Interface function mounts a disk to the file system
def tfs_mount(filename):
    for i in range(len(libDisk.Disks)):
        if libDisk.Disks[i].name == filename:
            libDisk.Mounted = i
            numBlocks = int(DEFAULT_DISK_SIZE/BLOCKSIZE)
            for j in range(numBlocks):
                buff = Buffer("")
                r = libDisk.readBlock(libDisk.Mounted, j, buff)
                if r < 0:
                    return r
                first = int(buff.contents[0])
                second = buff.contents[1]
                if(first != 1 and first != 2 and first != 3 and first != 4) or second != '\x45':
                    return -3
            return 0
    return -4

#Interface function unmounts the currently mounted disk
def tfs_unmount():
    libDisk.Mounted = -1

#Interface function opens a file on mounted disk
def tfs_openFile(name):
    if libDisk.Mounted == -1:
        return -13
    if len(name) > 8:
        return -5
    try:
        int(name)
        return -12
    except:
        pass
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, 0, buff)
    if j < 0:
        return j
    superblock = buff.contents
    root = int(superblock[2])
    j = libDisk.readBlock(libDisk.Mounted, root, buff)
    if j < 0:
        return j
    rootblock = buff.contents
    if superblock[3] == '\x00':
        return -6
    inode = int(superblock[3] + superblock[4])
    j = libDisk.readBlock(libDisk.Mounted, inode, buff)
    if j < 0:
        return j
    inodeblock = buff.contents
    if(inodeblock[2] == '\x00'):
        return -6
    data = int(inodeblock[2] + inodeblock[3])
    j = libDisk.readBlock(libDisk.Mounted, data, buff)
    if j < 0:
        return j
    datablock = buff.contents
    if name in rootblock:
        i = rootblock.find(name)
        i = i + len(name) + 1
        if rootblock[i-1] == '\x00':
            inode = int(rootblock[i] + rootblock[i+1])
            if inode not in libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table:
                libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table.append(inode)
                libDisk.Disks[libDisk.Mounted].File_Pointer_Table.append(0)
            return inode
    if(datablock[2] == '\x00'):
        new_superblock = str(1) + '\x45' + str(1) + (BLOCKSIZE-3)*'\x00'
    else:
        new_superblock = str(1) + '\x45' + str(1) + datablock[2] + datablock[3] + (BLOCKSIZE-5)*'\x00'
    buff = Buffer(new_superblock)
    j = libDisk.writeBlock(libDisk.Mounted, 0, buff)
    if j < 0: 
        return j
    new_root = ""
    i = 0
    while(rootblock[i] != '\x00' or rootblock[i+1] != '\x00'):
        new_root += rootblock[i]
        i += 1
    new_root += '\x00'
    new_root += name
    new_root += '\x00'
    if inode < 10:
        new_root += str(0)
    new_root += str(inode)
    new_root += '\x00'
    l = len(new_root)
    new_root = new_root + '\x00'*(BLOCKSIZE - l)
    buff = Buffer(new_root)
    j = libDisk.writeBlock(libDisk.Mounted, 1, buff)
    if j < 0:
        return j
    new_inode = str(2) + '\x45' + inodeblock[2] + inodeblock[3] + str(BLOCKSIZE)
    l = len(new_inode)
    new_inode = new_inode + '\x00'*(BLOCKSIZE - l)
    buff = Buffer(new_inode)
    j = libDisk.writeBlock(libDisk.Mounted, inode, buff)
    if j < 0:
        return j
    new_data = str(3) + '\x45' + '\x00'*(BLOCKSIZE-2)
    buff = Buffer(new_data)
    j = libDisk.writeBlock(libDisk.Mounted, data, buff)
    if j < 0:
        return j
    libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table.append(inode)
    libDisk.Disks[libDisk.Mounted].File_Pointer_Table.append(0)
    return inode

#Interface function closes file 
def tfs_closeFile(FD):
    if libDisk.Mounted == -1:
        return -13
    try:
        libDisk.Disks[libDisk.Mounted].File_Pointer_Table.pop(libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table.index(FD))
        libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table.remove(FD)
        return 0
    except:
        return -7

#Helper function frees a block on disk
def free_block(block):
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, 0, buff)
    if j < 0:
        return j
    superblock = buff.contents
    new_block = str(4) + '\x45' + superblock[3] + superblock[4] + '\x00'*(BLOCKSIZE-4)
    buff = Buffer(new_block)
    j = libDisk.writeBlock(libDisk.Mounted, block, buff)
    if j < 0:
        return j
    if block < 10:
        new_superblock = str(1) + '\x45' + str(1) + str(0) + str(block) + '\x00'*(BLOCKSIZE-5)
    else:
        new_superblock = str(1) + '\x45' + str(1) + str(block) + '\x00'*(BLOCKSIZE-5)
    buff = Buffer(new_superblock)
    j = libDisk.writeBlock(libDisk.Mounted, 0, buff)
    if j < 0:
        return j

#Helper function frees extra blocks of a file
def free_blocks(block):
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, block, buff)
    front = buff.contents
    if front[2] == '\x00':
        return
    curr = int(front[2] + front[3])
    j = libDisk.readBlock(libDisk.Mounted, curr, buff)
    front = buff.contents
    while(front[2] != '\x00'):
        next_curr = int(front[2] + front[3])
        free_block(curr)
        curr = next_curr
        j = libDisk.readBlock(libDisk.Mounted, curr, buff)
        front = buff.contents
    free_block(curr)
      
#Interface function writes to a file
def tfs_writeFile(FD, Buff, size):
    if libDisk.Mounted == -1:
        return -13
    try:
        p = libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table.index(FD)
    except:
        return -8
    num_files = int(size/(BLOCKSIZE-4)) + 1
    new_blocks_needed = num_files - 1
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, FD, buff)
    if j < 0:
        return j
    inode = buff.contents
    inode_size = ""
    i = 4
    while(inode[i] != '\x00'):
        inode_size += inode[i]
        i += 1
    inode_size = int(inode_size)
    curr_num_blocks = inode_size/BLOCKSIZE
    if curr_num_blocks > 1:
        free_blocks(int(inode[2] + inode[3]))
        j = libDisk.readBlock(libDisk.Mounted, FD, buff)
        if j < 0:
            return j
        inode = buff.contents
        inode = inode[0] + inode[1] + inode[2] + inode[3] + str(256) + '\x00'*(BLOCKSIZE-7)
        buff = Buffer(inode)
        j = libDisk.writeBlock(libDisk.Mounted, FD, buff)
        if j < 0:
            return j
    data_blocks = []
    data_blocks.append(int(inode[2] + inode[3]))
    if new_blocks_needed > 0:
        j = libDisk.readBlock(libDisk.Mounted, 0, buff)
        if j < 0:
            return j
        superblock = buff.contents
        if superblock[3] == '\x00':
            return -6
        free = int(superblock[3] + superblock[4])
        data_blocks.append(free)
        for i in range(new_blocks_needed-1):
            j = libDisk.readBlock(libDisk.Mounted, free, buff)
            if j < 0:
                return j
            block = buff.contents
            if block[2] == '\x00':
                return -6
            free = int(block[2] + block[3])
            data_blocks.append(free)
        j = libDisk.readBlock(libDisk.Mounted, free, buff)
        if j < 0:
            return j
        block = buff.contents
        if block[2] == '\x00':
            new_superblock = str(1) + '\x45' + str(1) + (BLOCKSIZE-3)*'\x00'
        else:
            new_superblock = str(1) + '\x45' + str(1) + block[2] + block[3] + (BLOCKSIZE -5)*'\x00'
        buff = Buffer(new_superblock)
        j = libDisk.writeBlock(libDisk.Mounted, 0, buff)
        if j < 0:
            return j
        new_size = len(data_blocks) * BLOCKSIZE
        new_inode = str(2) + '\x45' + inode[2] + inode[3] + str(new_size) 
        l = len(new_inode)
        new_inode = new_inode + (BLOCKSIZE-l)*'\x00'
        buff = Buffer(new_inode)
        j = libDisk.writeBlock(libDisk.Mounted, FD, buff)
        if j < 0:
            return j
    libDisk.Disks[libDisk.Mounted].File_Pointer_Table[p] = data_blocks[0]*BLOCKSIZE + 4
    for i in range(len(data_blocks)):
        if i + 1 == len(data_blocks):
            new_block = str(3) + '\x45' + '\x00' + '\x00' + Buff[(BLOCKSIZE-4)*i:]
            l = len(new_block)
            new_block += '\x00' * (BLOCKSIZE-l)
        else:
            if(data_blocks[i+1] < 10):
                new_block = str(3) + '\x45' + str(0) + str(data_blocks[i+1]) + Buff[(BLOCKSIZE-4)*i:(BLOCKSIZE-4)*i+(BLOCKSIZE-4)]
            else:
                new_block = str(3) + '\x45' + str(data_blocks[i+1]) + Buff[(BLOCKSIZE-4)*i:(BLOCKSIZE-4)*i+(BLOCKSIZE-4)]
        buff = Buffer(new_block)
        j = libDisk.writeBlock(libDisk.Mounted, data_blocks[i], buff)
        if j < 0:
            return j
    return 0

#Helper function updates the root inode
def update_root(FD):
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, 1, buff)
    if j < 0:
        return j
    root = buff.contents
    target = str(FD)
    if len(target) == 1:
        target = "0"+ target
    i = root.find(target)
    j = i - 2
    while(root[j] != '\x00'):
        j -= 1
    k = i
    while(root[k] != '\x00'):
        k += 1
    new_root = root[:j]
    new_root += root[k:]
    l = len(new_root)
    new_root += '\x00'*(BLOCKSIZE-l)
    buff = Buffer(new_root)
    j = libDisk.writeBlock(libDisk.Mounted, 1, buff)
    if j < 0:
        return j
    return 0

#Interface function deletes a file
def tfs_deleteFile(FD):
    if libDisk.Mounted == -1:
        return -13
    j = tfs_closeFile(FD)
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, FD, buff)
    if j < 0:
        return j
    inode = buff.contents
    data = int(inode[2] + inode[3])
    free_blocks(data)
    free_block(data)
    free_block(FD)
    j = update_root(FD)
    return j

#Interface function reads a byte from a file
def tfs_readByte(FD):
    if libDisk.Mounted == -1:
        return -13
    try:
        index = libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table.index(FD)
        p = libDisk.Disks[libDisk.Mounted].File_Pointer_Table[index]
    except:
        return -8
    libDisk.Disks[libDisk.Mounted].stream.seek(p)
    char = libDisk.Disks[libDisk.Mounted].stream.read(1)
    if char == '\x00':
        return -9
    if (p + 1) % BLOCKSIZE == 0:
        libDisk.Disks[libDisk.Mounted].stream.seek(p+1-BLOCKSIZE)
        block = libDisk.Disks[libDisk.Mounted].stream.read(BLOCKSIZE)
        if block[2] == '\x00':
            libDisk.Disks[libDisk.Mounted].File_Pointer_Table[index] = p+1-BLOCKSIZE + 2
        else:
            libDisk.Disks[libDisk.Mounted].File_Pointer_Table[index] = int(block[2]+block[3])*BLOCKSIZE + 4
    else:
        libDisk.Disks[libDisk.Mounted].File_Pointer_Table[index] += 1
    return char

#Interface function sets file pointer
def tfs_seek(FD, offset):
    if libDisk.Mounted == -1:
        return -13
    try:
        index = libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table.index(FD)
    except:
        return -8
    file_num = int(offset/(BLOCKSIZE-4))
    file_offset = offset % (BLOCKSIZE-4)
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, FD, buff)
    if j < 0:
        return j
    inode = buff.contents
    num = int(inode[2] + inode[3])
    j = libDisk.readBlock(libDisk.Mounted, num, buff)
    if j < 0:
        return j
    block = buff.contents
    for i in range(file_num-1):
        if block[2] == '\x00':
            return -10
        num = int(block[2]+block[3])
        j = libDisk.readBlock(libDisk.Mounted, num, buff)
        if j < 0:
            return j
        block = buff.contents
    libDisk.Disks[libDisk.Mounted].File_Pointer_Table[index] = (num*BLOCKSIZE) + file_offset + 4
    return 0

#Additional function renames a file
def tfs_rename(FD, name):
    if libDisk.Mounted == -1:
        return -13
    if len(name) > 8:
        return -5
    try:
        int(name)
        return -12
    except:
        pass
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, 1, buff)
    if j < 0:
        return j
    if FD not in libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table:
        return -8
    root = buff.contents
    target = str(FD)
    if len(target) == 1:
        target = "0"+ target
    i = root.find(target)
    j = i - 2
    while(root[j] != '\x00'):
        j -= 1
    k = i -1
    new_root = root[:j]
    new_root += '\x00' + name  
    new_root += root[k:]
    l = len(new_root)
    new_root += '\x00'*(BLOCKSIZE-l)
    buff = Buffer(new_root)
    j = libDisk.writeBlock(libDisk.Mounted, 1, buff)
    if j < 0:
        return j
    return 0

#Additional function prints all files to screen
def tfs_readdir():
    if libDisk.Mounted == -1:
        return -13
    buff = Buffer("")
    j = libDisk.readBlock(libDisk.Mounted, 1, buff)
    if j < 0:
        return j
    root = buff.contents
    unfiltered = root.split('\x00')
    filtered = []
    i = 0
    while(unfiltered[i] != ""):
        if i % 2 == 1:
            filtered.append(unfiltered[i])
        i += 1
    for i in filtered:
        print(i)

#Additional function displays fragments
def tfs_displayFragments():
    if libDisk.Mounted == -1:
        return -13
    num_blocks = DEFAULT_DISK_SIZE/BLOCKSIZE
    for i in range(int(num_blocks)):
        buff = Buffer("")
        j = libDisk.readBlock(libDisk.Mounted, i, buff)
        if j < 0:
            return j
        block = buff.contents
        if int(block[0]) == 1:
            print("Block", i, "Superblock", "Contents", block[2:])
        elif int(block[0]) == 2:
            print("Block", i, "Inode", "Contents:", block[2:])
        elif int(block[0]) == 3:
            print("Block", i, "Data", "Contents:", block[2:])
        else:
            print("Block", i, "FREE", "Contents:", block[2:])

#Additional function defragments memory
def tfs_defrag():
    if libDisk.Mounted == -1:
        return -13
    num_blocks = DEFAULT_DISK_SIZE/BLOCKSIZE
    for i in range(int(num_blocks)-1, 0, -1):
        buff = Buffer("")
        j = libDisk.readBlock(libDisk.Mounted, i, buff)
        if j < 0:
            return j
        block = buff.contents
        if int(block[0]) != 4:
            free = -1 
            for k in range(i, 1, -1):
                j = libDisk.readBlock(libDisk.Mounted, k, buff)
                if j < 0:
                    return j
                b = buff.contents
                if int(b[0]) == 4:
                    free = k
            if free == -1:
                return 0
            j = libDisk.readBlock(libDisk.Mounted, free, buff)
            if j < 0:
                return j
            free_block = buff.contents
            blockBuff = Buffer(block)
            freeBuff = Buffer(free_block)
            j = libDisk.writeBlock(libDisk.Mounted, free, blockBuff)
            if j < 0:
                return j
            j = libDisk.writeBlock(libDisk.Mounted, i, freeBuff)
            if j < 0:
                return j
            if int(block[0]) == 3:
                for k in range(2, i):
                    j = libDisk.readBlock(libDisk.Mounted, k, buff)
                    if j < 0:
                        return j
                    b = buff.contents
                    if b[2] != '\x00' and int(b[2] + b[3]) == i:
                        if free < 10:
                            new = b[:2] + str(0) + str(free) + b[4:]
                        else:
                            new = b[:2] + str(free) + b[4:]
                        buff = Buffer(new)
                        j = libDisk.writeBlock(libDisk.Mounted, k, buff)
                        if j < 0:
                            return j
            elif int(block[0]) == 2:
                j = libDisk.readBlock(libDisk.Mounted, 1, buff)
                if j < 0:
                    return j
                root = buff.contents
                unfiltered = root.split('\x00')
                filtered = []
                j = 0
                while(unfiltered[j] != ""):
                    filtered.append(unfiltered[j])
                    j += 1
                for k in range(len(filtered)):
                    try:
                        if int(filtered[k]) == i:
                            print("FILE DESCRIPTOR", i, "HAS CHANGED TO", free)
                            index = libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table.index(i)
                            libDisk.Disks[libDisk.Mounted].Dynamic_Resource_Table[index] = free
                            libDisk.Disks[libDisk.Mounted].File_Pointer_Table[index] = (free*BLOCKSIZE)+4
                            if free < 10:
                                filtered[k] = "0" + str(free)
                            else:
                                filtered[k] = str(free)
                    except:
                        pass
                new_root = filtered[0]
                for k in range(1, len(filtered)):
                    new_root += '\x00'
                    new_root += filtered[k]
                l = len(new_root)
                new_root = new_root + '\x00'*(BLOCKSIZE-l)
                buff = Buffer(new_root)
                j = libDisk.writeBlock(libDisk.Mounted, 1, buff)
                if j < 0:
                    return j
            for k in range(int(num_blocks)):
                j = libDisk.readBlock(libDisk.Mounted, k, buff)
                if j < 0:
                    return j
                b = buff.contents
                if k == 0:
                    if int(b[3]+b[4]) == free:
                        if i < 10:
                            new = b[:3] + str(0) + str(i) + b[5:]
                        else:
                            new = b[:3] + str(i) + b[5:]
                        buff = Buffer(new)
                        j = libDisk.writeBlock(libDisk.Mounted, k, buff)
                        if j < 0:
                            return j
                elif int(b[0]) == 4:
                    if b[2] != '\x00' and int(b[2] + b[3]) == free:
                        if i < 10:
                            new = b[:2] + str(0) + str(i) + b[4:]
                        else:
                            new = b[:2] + str(i) + b[4:]
                        buff = Buffer(new)
                        j = libDisk.writeBlock(libDisk.Mounted, k, buff)
                        if j < 0:
                            return j
