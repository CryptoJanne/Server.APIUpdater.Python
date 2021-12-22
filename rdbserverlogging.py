from pyravendb.store import document_store
import psutil
from psutil._common import bytes2human
import subprocess
import datetime
import configparser


class SystemStats(object):
    def __init__(self, Cpu, Gpu, Memory, HardDrive1, HardDrive2, tid):
        self.Cpu = Cpu
        self.Gpu = Gpu
        self.Memory = Memory
        self.HardDrive1 = HardDrive1
        self.HardDrive2 = HardDrive2
        self.tid = tid


class Cpu(object):
    def __init__(self, core1, core2, core3, core4, core5, core6, core7, core8):
        self.core1 = core1
        self.core2 = core2
        self.core3 = core3
        self.core4 = core4
        self.core5 = core5
        self.core6 = core6
        self.core7 = core7
        self.core8 = core8


class Gpu(object):
    def __init__(self, gpuname, fanspeed, memutil, gpuutil, gputemp, poweruse):
        self.name = gpuname
        self.fanspeed = fanspeed
        self.memoryutilization = memutil
        self.gpuutilization = gpuutil
        self.gputemperature = gputemp
        self.poweruse = poweruse


class Memory(object):
    def __init__(self, totalmem, availablemem, percentmem):
        self.totalmemory = totalmem
        self.availablememory = availablemem
        self.percentused = percentmem


class HardDrive(object):
    def __init__(self, totalspace, used, free, percent):
        self.totalspace = totalspace
        self.used = used
        self.free = free
        self.percent = percent


class RunTheLogging:
    def __init__(self):
        cpudata = psutil.cpu_percent(0.1, percpu=True)
        cpu = Cpu(cpudata[0], cpudata[1], cpudata[2], cpudata[3], cpudata[4], cpudata[5], cpudata[6], cpudata[7])

        getallproperties = subprocess.run(["nvidia-smi", "--query-gpu=fan.speed,utilization.memory,utilization.gpu,temperature.gpu,power.draw", "--format=csv,noheader"], stdout=subprocess.PIPE, text=True)
        getname = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], stdout=subprocess.PIPE, text=True)
        splitproperties = getallproperties.stdout.split()
        gpuname = getname.stdout.strip()
        gpu = Gpu(gpuname, splitproperties[0], splitproperties[2], splitproperties[4], splitproperties[6], splitproperties[7])

        mem = psutil.virtual_memory()
        for name in mem._fields:
            value = getattr(mem, name)
            if name == 'percent':
                percent = value
            if name == 'total':
                value = bytes2human(value)
                total = value
            if name == 'available':
                value = bytes2human(value)
                available = value
        memory = Memory(total, available, percent)

        for part in psutil.disk_partitions(all=False):
            if part.device == "/dev/sda2":
                disk1usage = psutil.disk_usage(part.mountpoint)
                disk1part = part
            if part.device == "/dev/sdb1":
                disk2usage = psutil.disk_usage(part.mountpoint)
                disk2part = part
        disk1 = HardDrive(bytes2human(disk1usage.total), bytes2human(disk1usage.used), bytes2human(disk1usage.free), disk1usage.percent)
        disk2 = HardDrive(bytes2human(disk2usage.total), bytes2human(disk2usage.used), bytes2human(disk2usage.free), disk2usage.percent)

        now = datetime.datetime.now()
        time_string = now.isoformat()
        deletedate = now + datetime.timedelta(hours=5)
        DateTime_in_ISOFormat = deletedate.isoformat()

        dataentry = SystemStats(cpu, gpu, memory, disk1, disk2, time_string)

        config = configparser.ConfigParser()
        config.read('config.ini')
        dburl = config['ravendb']['url']
        certpath = config['certification']['path']
        certpw = config['certification']['password']
        certdbname = config['certification']['dbname']

        cert = {"pfx": certpath, "password": certpw}
        store = document_store.DocumentStore(urls=dburl, database=certdbname, certificate=cert)
        store.initialize()

        with store.open_session() as session:
            session.store(dataentry)
            metadata = session.advanced.get_metadata_for(dataentry)
            metadata["@collection"] = "SystemStats"
            metadata["@expires"] = DateTime_in_ISOFormat
            session.save_changes()
