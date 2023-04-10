import sys

class Scheduler:

    def __init__(self, jobfile, algorithm, quantum):
        self.jobfile = jobfile
        if algorithm == 'SRTN' or algorithm == 'FIFO' or algorithm == 'RR':
            self.algorithm = algorithm
        else:
            self.algorithm = 'FIFO'
        if quantum == None:
            self.quantum = 1
        else:
            try:
                qa = int(quantum)
                if qa >= 1:
                    self.quantum = qa
                else:
                    self.quantum = 1
            except ValueError:
                self.quantum = 1


class Job:

    def __init__(self, number, arrival, length):
        self.number = number
        self.arrival = arrival
        self.length = length
        self.wait = 0
        self.turnaround = 0
        self.active = False


def set_scheduler():
    j = sys.argv[1]
    a = None
    q = None
    pf = False
    qf = False
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == '-p':
            pf = True
            qf = False
        elif sys.argv[i] == '-q':
            qf = True
            pf = False
        elif pf == True:
            a = sys.argv[i]
            pf = False
        elif qf == True:
            q = sys.argv[i]
            qf = False
    return Scheduler(j, a, q)


def parse_jobs(fname):
    jobs = {}
    f = open(fname, "r")
    for line in f:
        l = line.split(" ")
        if int(l[1]) in jobs:
            jobs[int(l[1])].append(int(l[0]))
        else:
            jobs[int(l[1])] = [int(l[0])]
    f.close()
    return jobs


def initialize_jobs(jobs, keys):
    i = 0
    jobs_table = []
    for key in keys:
        for job in jobs[key]:
            new = Job(i, key, job)
            jobs_table.append(new)
            i += 1
    return jobs_table


def schedule(scheduler, jobs_table):
    if scheduler.algorithm == "FIFO":
        return fifo(jobs_table)
    elif scheduler.algorithm == "RR":
        return rr(jobs_table, scheduler.quantum)
    elif scheduler.algorithm == "SRTN":
        return srtn(jobs_table)


def fifo(jobs_table):
    time = 0
    for job in jobs_table:
        if job.number == 0:
            job.wait = 0
            job.turnaround = job.length
            time = job.arrival + job.length
        else:
            job.wait = time - job.arrival
            job.turnaround = job.wait + job.length
            time = time + job.length
    return jobs_table


def check_done(jobs_table):
    for job in jobs_table:
        if job.length != 0:
            return False
    return True


def rr(jobs_table, quantum):
    time = 0
    current_quantum = quantum
    active_jobs = []
    while(not check_done(jobs_table)):
        jobs_table = activate_jobs(time, jobs_table)
        for job in jobs_table:
            if job.active and job.number not in active_jobs:
                active_jobs.append(job.number)
        if len(active_jobs) != 0:
            job = jobs_table[active_jobs[0]]
            job.length -= 1
            job.turnaround += 1
            current_quantum -= 1
            for i in range(1, len(active_jobs)):
                jobs_table[active_jobs[i]].wait += 1
                jobs_table[active_jobs[i]].turnaround += 1
            if job.length == 0:
                job.active = False
                active_jobs.pop(0)
                current_quantum = quantum
            elif current_quantum == 0:
                active_jobs.pop(0)
                active_jobs.append(job.number)
                current_quantum = quantum
        time += 1
    return jobs_table

                    
def activate_jobs(time, jobs_table):
    for job in jobs_table:
        if job.arrival == time:
            job.active = True
    return jobs_table


def update_table(current_job, jobs_table, active_jobs):
    prev_curr = current_job
    job = jobs_table[current_job]
    job.length -= 1
    job.turnaround += 1
    if job.length == 0:
        job.active = False
        current_job = -1
    for i in range(len(active_jobs)):
        if active_jobs[i] != prev_curr:
            jobs_table[active_jobs[i]].wait += 1
            jobs_table[active_jobs[i]].turnaround += 1
    return jobs_table, current_job


def srtn(jobs_table):
    time = 0
    current_job = -1
    while(not check_done(jobs_table)):
        jobs_table = activate_jobs(time, jobs_table)
        active_jobs = []
        for job in jobs_table:
            if job.active:
                active_jobs.append(job.number)
                if current_job == -1:
                    current_job = job.number
                    current_min = job.length
                elif job.length < current_min:
                    current_job = job.number
                    current_min = job.length
        if current_job != -1:
            jobs_table, current_job = update_table(current_job, jobs_table, active_jobs)
        time += 1
    return jobs_table


            

def print_jobs(jobs_table):
    num_jobs = len(jobs_table)
    total_turn = 0
    total_wait = 0
    for job in jobs_table:
        t = float(job.turnaround)
        w = float(job.wait)
        print("Job  ", job.number, "-- Turnaround {:.2f}".format(t), " Wait {:.2f}".format(w))
        total_turn += t
        total_wait += w
    average_t = total_turn/num_jobs
    average_w = total_wait/num_jobs
    print("Average -- Turnaround {:.2f}".format(average_t), " Wait {:.2f}".format(average_w))


def main():
    scheduler = set_scheduler()
    jobs = parse_jobs(scheduler.jobfile)
    keys = list(jobs.keys())
    keys.sort()
    jobs_table = initialize_jobs(jobs, keys)
    jobs_table = schedule(scheduler, jobs_table)
    print_jobs(jobs_table)


if __name__ == "__main__":
    main()
