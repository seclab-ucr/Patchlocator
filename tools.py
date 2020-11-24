import os,sys

def group_matchresults():
    cve_result = {}
    with open(sys.argv[1]) as f:
        s_buf = f.readlines()
    for line in s_buf:
        cve,result = line[:-1].split(" ")[:2]
        if cve not in cve_result or cve_result[cve]==None:
            cve_result[cve]=result
        if result == 'P':
            cve_result[cve]='P'
    for cve in cve_result:
        print cve,cve_result[cve]

if __name__ == '__main__':
    group_matchresults()
