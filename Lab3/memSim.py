import sys

#Jonathan Schreiber
#Lab 3

#Class for pages in page table and tlb
class Page:

    def __init__(self, page_num, frame_num, present):
        self.page_num = page_num
        self.frame_num = frame_num
        self.present = present

#Class to store all key memory data structures and variables
class Memory:

    def __init__(self, addresses, frames, pra):
        self.addresses = addresses
        self.frames = frames
        self.pra = pra
        self.tlb = [None]* 16
        self.page_table = [None]*256
        self.memory = [None]*self.frames
        self.backing_store = open("BACKING_STORE.bin", "rb")
        self.size = 0
        self.mem_index = 0
        self.full = False
        self.tlb_index = 0
        self.tlb_full = False
        self.add_index = -1

#Function that parses command line and initializes Memory Object
def initialize_memory():
    addresses = parse_addresses(sys.argv[1])
    frames = None
    pra = None
    for i in range(2, len(sys.argv)):
        if frames == None:
            try:
                frames = int(sys.argv[i])
                if frames < 1 or frames > 256:
                    frames = 256
            except:
                frames = 256
        elif pra == None:
            if sys.argv[i] == 'LRU':
                pra = 'LRU'
            elif sys.argv[i] == 'OPT':
                pra = 'OPT'
            else:
                pra = 'FIFO'
    if frames == None:
        frames = 256
    if pra == None:
        pra = 'FIFO'
    memory = Memory(addresses, frames, pra)
    return memory

#Function that opens and reads from address file, parsing it into list of addresses
def parse_addresses(reference):
    addresses = []
    ref = open(reference, "r")
    for line in ref:
        addresses.append(int(line))
    return addresses    

#Helper function to compute page number and offset given address
def compute_page_num(address):
    masked = address & 0xFFFF
    page_num = masked >> 8
    page_offset = masked & 0xFF
    return page_num, page_offset

#Function that deals with page faults
def page_fault(memory, page_number):
    memory.backing_store.seek(page_number*256)
    data = memory.backing_store.read(256)
    if memory.full == False:
        frame = memory.size
        memory.size += 1
        if memory.size == memory.frames:
            memory.full = True
    else:
        frame = evict(memory)
    new_page = Page(page_number, frame, True)
    memory.page_table[page_number] = new_page
    memory.memory[frame] = data
    memory.tlb[memory.tlb_index] = new_page
    memory.tlb_index += 1
    if memory.tlb_index == 16:
        memory.tlb_index = 0
        memory.tlb_full = True
    return frame, 1, 0

#Helper function to set evicted pages present bit to false, and remove it from tlb
def eviction_paperwork(memory, victim, page_num):
    if page_num == None:
        for entry in memory.page_table:
            if entry is not None and entry.frame_num == victim and entry.present:
                page_number = entry.page_num
                break
    else:
        page_number = page_num
    memory.page_table[page_number].present = False
    for i in range(len(memory.tlb)):
        if memory.tlb[i].page_num == page_number:
            tlb_evict(memory, i)
            break

#Helper function to remove evicted page from tlb, and update tlb accordingly
def tlb_evict(memory, tlb_evict):
    if memory.tlb_full:
        new_tlb = [None] * 16
        new_index = 0
        for i in range(len(memory.tlb)):
            index = (memory.tlb_index + i)%16
            if index != tlb_evict:
                new_tlb[new_index] = memory.tlb[index]
                new_index += 1
        memory.tlb = new_tlb
        memory.tlb_index = 15
        memory.tlb_full = False
    else:
        passed = False
        for i in range(memory.tlb_index):
            if i == tlb_evict:
                passed = True
            if passed:
                memory.tlb[i] = memory.tlb[i+1]
        memory.tlb_index -= 1

#Eviction function if pra is FIFO
def evict_fifo(memory):
    victim = memory.mem_index
    eviction_paperwork(memory, victim, None)
    memory.mem_index += 1
    if memory.mem_index == memory.frames:
        memory.mem_index = 0
    return victim

#Eviction function if pra is LRU
def evict_lru(memory):
    lru = 0
    seen = []
    for i in range(memory.add_index -1, -1, -1):
        page_num, d = compute_page_num(memory.addresses[i])
        if page_num not in seen and memory.page_table[page_num].present:
            seen.append(page_num)
            lru = page_num
    victim = memory.page_table[lru].frame_num
    eviction_paperwork(memory, victim, lru)
    return victim

#Eviction function if pra is OPT
def evict_opt(memory):
    opt = 0
    seen = []
    for i in range(memory.add_index + 1, len(memory.addresses)):
        page_num, d = compute_page_num(memory.addresses[i])
        if page_num not in seen and memory.page_table[page_num] is not None and memory.page_table[page_num].present:
            seen.append(page_num)
            opt = page_num
    if len(seen) != memory.frames:
        for entry in memory.page_table:
            if entry is not None and entry.page_num not in seen and entry.present:
                opt = entry.page_num
                break
    victim = memory.page_table[opt].frame_num
    eviction_paperwork(memory, victim, opt)
    return victim

#Function that chooses frame to be evicted and evicts it
def evict(memory):
    if memory.pra == 'FIFO':
        return evict_fifo(memory)
    if memory.pra == 'LRU':
        return evict_lru(memory)
    if memory.pra == 'OPT':
        return evict_opt(memory)

#Helper function to determine if desired page already in tlb
def check_tlb(memory, page_number):
    for entry in memory.tlb:
        if entry is not None and entry.page_num == page_number:
            return True, entry.frame_num
    return False, 0

#Function to get frame number for new address
def get_frame_num(memory, page_number):
    flag, frame = check_tlb(memory, page_number)
    if flag:
        return frame, 0, 1
    elif memory.page_table[page_number] == None or memory.page_table[page_number].present == False:
        return page_fault(memory, page_number)
    else:
        memory.tlb[memory.tlb_index] = memory.page_table[page_number]
        memory.tlb_index += 1
        if memory.tlb_index == 16:
            memory.tlb_index = 0
            memory.tlb_full = True
        frame = memory.page_table[page_number].frame_num
        return frame, 0, 0

#Helper function that prints information for a specific address
def print_address(memory, address, page_offset, frame):
    data = memory.memory[frame][page_offset]
    if data > 127:
        data = (256-data) *-1
    print(str(address) + ", " + str(data) + ", " + str(frame) + ", " + memory.memory[frame].hex().upper())


#Helper function that prints page fault and tlb statistics at end
def print_statistics(memory, page_fault, tlb_hit):
    pfr = float(page_fault)/len(memory.addresses)
    tlbr = float(tlb_hit)/len(memory.addresses)
    print("Number of Translated Addresses =", len(memory.addresses))
    print("Page Faults =", page_fault)
    print("Page Fault Rate =", "{:.3f}".format(pfr))
    print("TLB Hits =", tlb_hit)
    print("TLB Misses =", len(memory.addresses) - tlb_hit)
    print("TLB Hit Rate =", "{:.3f}".format(tlbr))

#Driver function that runs simulation
def simulate_memory(memory):
    page_fault = tlb_hit = 0
    for address in memory.addresses:
        memory.add_index += 1
        page_number, page_offset = compute_page_num(address)
        frame, pf, tlb = get_frame_num(memory, page_number)
        page_fault += pf
        tlb_hit += tlb
        print_address(memory, address, page_offset, frame)
    print_statistics(memory, page_fault, tlb_hit)

#Main driver 
def main():
    memory = initialize_memory()
    simulate_memory(memory)

if __name__ == "__main__":
    main()
