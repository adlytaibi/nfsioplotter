#!/usr/bin/env python3
#
# Chart Plotter of nfs-iostat output
#
# @author Adly Taibi
# @version 1.0
#

import argparse
import matplotlib.pyplot as plt
import re
import os
import time

class NFSioPlotter:
  'NFS iostat Plotter'
  def __init__(self):
    NFSioPlotter.debug = False
    NFSioPlotter.header = ''
    NFSioPlotter.extension = 'svg'
    NFSioPlotter.outfile = ''
    NFSioPlotter.transparent = False
    NFSioPlotter.xlabel = 'Time (seconds)'
    NFSioPlotter.d1 = 'Read'
    NFSioPlotter.d2 = 'Write'

  class RegEx:
    _reg_device = re.compile(r'(.*)mounted on (.*)\n')
    _reg_ops = re.compile(r'(.*)rpc(.*)\n')
    _reg_read = re.compile(r'read:(.*)\n')
    _reg_write = re.compile(r'write:(.*)\n')
    _reg_dvalues = re.compile(r'([0-9]*\.?[0-9]%)')
    _reg_blank = re.compile(r'^$')
    __slots__ = ['device', 'ops', 'read', 'write', 'dvalues', 'blank']

    def __init__(self, line):
      self.device = self._reg_device.match(line)
      self.ops = self._reg_ops.match(line)
      self.read = self._reg_read.match(line)
      self.write = self._reg_write.match(line)
      self.dvalues = self._reg_dvalues.search(line)
      self.blank = self._reg_blank.search(line)

  def devlist(self, infile, interval):
    pattern = re.compile("\s+")
    devices = []
    with open(infile, 'r') as file:
        line = next(file)
        while line:
          reg_match = self.RegEx(line)
          if reg_match.device:
            device = reg_match.device.group(2).replace(':','')
            if not device in devices:
              devices.append(device)
            else:
              break
          line = next(file, None)
    return devices

  def dataparse(self, infile, interval):
    numdev = len(self.devlist(infile, interval))
    pattern = re.compile("\s+")
    data = dict()
    devices = []
    atimes = []
    avops = {}
    avread = {}
    avwrite = {}
    inc = 0
    ldata = 0
    t0 = (2018, 7, 22, 8, 0, 0, 6, 203, 0) # Time as a reference point, everything else is relative with interval delta
    with open(infile, 'r') as file:
        line = next(file)
        while line:
          reg_match = self.RegEx(line)

          # Device name section
          if reg_match.device:
            if inc%numdev == 0:
              mltpy = 1
            else:
              mltpy = 0
            t = time.mktime(t0) + interval * mltpy
            t0 = time.localtime(t)
            timeline = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t))
            inc = inc + 1
            device = reg_match.device.group(2)
            ldata = ldata + 1
            if self.debug: print('device', device)

          # OPS section
          if reg_match.ops:
            ops = reg_match.ops.group()
            if self.debug: print('ops', ops)
            line = next(file, None)
            if self.debug: print('opsv', line)
            vops = [v for v in pattern.split(line.strip())]
            ldata = ldata + 1

          # Read section
          if reg_match.read:
            read = reg_match.read.group(1)
            if self.debug: print('read', read)
            line = next(file, None)
            if self.debug: print('readv', line)
            vread = [v.strip() for v in pattern.split(line.strip())]
            ldata = ldata + 1

          # Write section
          if reg_match.write:
            write = reg_match.write.group(1)
            if self.debug: print('write', write)
            line = next(file, None)
            if self.debug: print('writev', line)
            vwrite = [v.strip() for v in pattern.split(line.strip())]
            ldata = ldata + 1

          # Record data when the full set has been collected
          if ldata == 4:
            avops[inc] = {device: vops}
            avread[inc] = vread
            avwrite[inc] = vwrite
            dict_of_data = {
                'ops': vops,
                'read': vread,
                'write': vwrite
            }
            if device in data:
              data[device].append(dict_of_data)
            else:
              data[device] = [dict_of_data]
            if inc%numdev == 0:
              atimes.append(timeline)
            if not device in devices:
              devices.append(device)
            ldata = 0
    
          line = next(file, None)
    if self.debug: print(atimes)
    if self.debug: print(devices)
    if self.debug: print(data)
    return atimes, devices, data
  
  def Two_Chart(self, devs, title, ylabel1, ylabel2, col):
    fsize = 8
    flegsize = 6
    expansion_box = 0.86
    ilongest = 0
    facecol = (.949019, .952941, .956862)
    selectdevs = []
    
    # x-axis
    x_seconds = []
    for i in range(0,len(self.timeline)):
       ts = time.mktime(time.strptime(self.timeline[i], '%Y-%m-%d %H:%M:%S'))
       if (i == 0):
          BeginTime = ts
          x_seconds.append(0.0)
       else:
          x_seconds.append( (ts - BeginTime) )
    
    # Markers
    color_list = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    line_style = ['o-', '^--', 's-.', '*-', '<--', '>-.', 'v-', 'o--']
    line_list = []
    for line_type in line_style:
      for color in color_list:
        line_list.append(color + line_type)
    
    # Expansion box
    for item in self.devices:
       if (len(self.d1) > ilongest):
          ilongest = len(self.d1)
       d11 = item + " " + self.d1
       if (len(d11) > ilongest):
          ilongest = len(d11)
       if (len(self.d2) > ilongest):
          ilongest = len(self.d2)
       d22 = item + " " + self.d2
       if (len(d22) > ilongest):
          ilongest = len(d22)
    eratio = -0.008*ilongest + 1.03
    expansion_box = round(eratio,2)

    # Prepare the data to draw
    d1tidy = {}
    d2tidy = {}
    for item in self.devices:
      for dev in devs:
        if dev in item:
          if not item in selectdevs:
            selectdevs.append(item)
            for dd in self.data[item]:
              val = float(dd['read'][col])
              if item in d1tidy:
                d1tidy[item].append(val)
              else:
                d1tidy[item] = [val]
              val = float(dd['write'][col])
              if item in d2tidy:
                d2tidy[item].append(val)
              else:
                d2tidy[item] = [val]
    
    if self.extension in ['pdf', 'onepdf']:
      fig = plt.figure(figsize=(11,8.5))

    # Graph #1
    ax1 = plt.subplot(211)
    i = 0
    #for item in self.devices:
    for item in selectdevs:
      d11 = item+' '+self.d1
      plt.plot(x_seconds, d1tidy[item], line_list[i], label=d11, markersize=1)
      i = i + 1
    #ax1.yaxis.set_major_locator(plt.MaxNLocator(4))
    #ax1.yaxis.set_major_formatter(plt.FormatStrFormatter("%.02f"))
    ax1.set_facecolor(facecol)
    ax1.set_xticklabels([])
    plt.title(title)
    if self.header: plt.suptitle(self.header, fontsize=8)
    plt.ylabel(ylabel1, fontsize=fsize)
    plt.yticks(fontsize=fsize)
    plt.xticks(fontsize=fsize)
    plt.grid()
    
    # Graph #1 Legend
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width * expansion_box, box.height])
    leg = plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0., labelspacing=0, borderpad=0.15, handletextpad=0.2)
    frame1 = leg.get_frame()
    frame1.set_facecolor("0.80")
    for t in leg.get_texts():
       t.set_fontsize(flegsize)
    
    # Graph #2
    ax2 = plt.subplot(212)
    i = 0
    for item in selectdevs:
      d22 = item+' '+self.d2
      plt.plot(x_seconds, d2tidy[item], line_list[i], label=d22, markersize=1)
      i = i + 1
    
    #ax2.yaxis.set_major_locator(plt.MaxNLocator(4))
    #ax2.yaxis.set_major_formatter(plt.FormatStrFormatter("%.02f"))
    ax2.set_facecolor(facecol)
    plt.ylabel(ylabel2, fontsize=fsize)
    plt.yticks(fontsize=fsize)
    plt.xticks(fontsize=fsize)
    plt.xlabel(self.xlabel)
    plt.grid()
    
    # Graph #2 Legend
    box = ax2.get_position()
    ax2.set_position([box.x0, box.y0, box.width * expansion_box, box.height])
    leg = plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0., labelspacing=0, borderpad=0.15, handletextpad=0.2)
    frame1 = leg.get_frame()
    frame1.set_facecolor("0.80")
    for t in leg.get_texts():
       t.set_fontsize(flegsize)
    
    # Show graph or save to file
    if (len(self.outfile) == 0):
      plt.show()
    else:
      if self.extension == 'onepdf':
        self.pdfpages.savefig(fig)
      else:
        plt.savefig(self.outfile, dpi=200, transparent=self.transparent)
      plt.close()

  def main(self):
    # Parse input arguments
    parser = argparse.ArgumentParser(description='Plot NFS iostat data.')
    parser.add_argument('nfsiostat', metavar='input', type=str, nargs=1, help='nfs-iostat file.')
    parser.add_argument('interval', metavar='interval', type=int, nargs=1, help='Interval in seconds.')
    parser.add_argument('--devs', metavar='dev', type=str, nargs='+', help='Select NFS mounts to graph (partial names suffice).')
    parser.add_argument('--format', metavar='ext', type=str, help='png, ps, eps, svg, pdf and onepdf. (default: png)\nonepdf: produces one file that contains all charts.')
    parser.add_argument('--devlist', action="store_true", help='List the devices.')
    parser.add_argument('--header', metavar='title', help='Title that appears at the top of each chart.')
    parser.add_argument('--debug', action="store_true", help='Run with debug output.')
    args = parser.parse_args()
    infile = args.nfsiostat[0]
    self.header = args.header
    if not os.path.isfile(infile):
      print('File "{}" does not exist.'.format(infile))
      exit(1)

    # Lookup and print the devices in the input file
    if args.devlist:
      devices = self.devlist(infile, args.interval[0])
      print('\n'.join(devices))
      exit(0)

    # Check for the requested output file extension
    if args.format:
      if args.format in ['png', 'ps', 'eps', 'svg', 'pdf', 'onepdf']:
        self.extension = args.format
      else:
        print('File extension "{}" does is not supported.'.format(args.format))
        exit(1)
    else:
      self.extension = 'png'

    # Debug option
    if args.debug:
      self.debug = True

    # Parse the data from file
    self.timeline, self.devices, self.data = self.dataparse(infile, args.interval[0])
    pid = os.getpid()

    # Selected volumes or all
    if args.devs:
      devs = args.devs
    else:
      devs = self.devices

    # Multi-page PDF to contain all graphs
    if self.extension == 'onepdf':
      import datetime
      from matplotlib.backends.backend_pdf import PdfPages
      self.pdfpages = PdfPages('{}_charts.pdf'.format(pid))
      # PDF Metadata
      md = self.pdfpages.infodict()
      md['Title'] = self.header or 'NFS iostat charts'
      md['Author'] = u'Adly Taibi'
      md['Subject'] = 'nfsioplotter (NFS iostat charts)'
      md['Keywords'] = 'NFS iostat, IOPS, Throughput, Request size, Average RTT'
      md['CreationDate'] = datetime.datetime.today()
      md['ModDate'] = datetime.datetime.today()

    # Plot IOPS
    self.outfile = '{}_iops.{}'.format(pid, self.extension)
    self.Two_Chart(devs, 'IOPS', 'Read\nops/s', 'Write\nops/s', 0)

    # Plot Throughput
    self.outfile = '{}_throughput.{}'.format(pid, self.extension)
    n.Two_Chart(devs, 'Throughput', 'Read throughput\nkB/s', 'Write throughput\nkB/s', 1)

    # Plot Request size
    self.outfile = '{}_requestsize.{}'.format(pid, self.extension)
    n.Two_Chart(devs, 'Request size', 'Read\nkB/op', 'Write\nkB/op', 2)

    # Plot Average RTT
    self.outfile = '{}_avgrtt.{}'.format(pid, self.extension)
    n.Two_Chart(devs, 'Average Round-Trip Time', 'Read avg RTT\n(ms)', 'Write avg RTT\n(ms)', 5)

    # Save Multi-page PDF file
    if self.extension == 'onepdf':
      self.pdfpages.close()

if __name__ == '__main__':
  n = NFSioPlotter()
  n.main()
