__author__ = 'sushil'

from marathon import MarathonClient
from pprint import pprint, pformat   # NOQA
from mScale.lib import util
import marathon
import requests
import json
import time
import sys
import logging

l = util.createlogger('API', logging.INFO)
# l.setLevel(logging.DEBUG)


class MarathonIF(object):
    def __init__(self, marathon_addr, my_addr, mesos):
        self.mcli = MarathonClient(marathon_addr)
        self.myAddr = my_addr
        self.mesos = mesos

    def get_apps(self):
        listapps = self.mcli.list_apps()
        return listapps

    def get_app(self, app_id):
        try:
            a = self.mcli.get_app(app_id)
        except marathon.exceptions.NotFoundError as e:  # NOQA
            return None
        return a

    def delete_app(self, app_id, force=False):
        return self.mcli.delete_app(app_id, force)

    def delete_app_ifexisting(self, app_id):
        for idx in range(0, 4):
            try:
                a = self.get_app(app_id)
                if a:
                    return self.delete_app(app_id, True)
                return None
            except:
                e = sys.exc_info()[0]
                pprint("<p>Error: %s</p>" % e)
        raise

    def create_app(self, app_id, attr):
        for idx in range(0, 10):
            try:
                a = self.mcli.create_app(app_id, attr)
                return a
            except marathon.exceptions.MarathonHttpError as e:
                if str(e).find('App is locked by one or more deployments. Override with the option') > 0:
                    time.sleep(1)
                else:
                    raise
        raise

    def wait_app_removal(self, app):
        cnt = 0
        while True:
            if not self.get_app(app):
                break
            time.sleep(0.2)
            cnt += 1
            if cnt > 0:
                l.info("Stuck waiting for %s to be deleted CNT=%d" % (app, cnt))
        return True

    def wait_app_ready(self, app, running_count):
        cnt = 0
        while True:
            a1 = self.get_app(app)
            if a1.tasks_running == running_count:
                return a1
            cnt += 1
            time.sleep(1)
            l.info("[%d]Waiting for task to move to running stage, " % cnt +
                   "current stat staged=%d running=%d expected Running=%d" %
                   (a1.tasks_staged, a1.tasks_running, running_count))

    def scale_app(self, app, scale):
        return self.mcli.scale_app(app, scale)


class MesosIF(object):
    def __init__(self, addr):
        self.myaddr = addr
        self.update_slaves()

    def update_slaves(self):
        r = requests.get(self.myaddr + '/master/slaves')
        assert r.status_code == 200
        dt = json.loads(r.content)
        self.noOfSlaves = len(dt['slaves'])
        # pprint(" Slaves Found : " + str(self.noOfSlaves))
        self.slavesID = {}
        self.slavesHN = {}
        for idx in range(0, self.noOfSlaves):
            itm = dt['slaves'][idx]
            # l.info(" Slave [" + itm['hostname'] + " ID=" + itm['id'] +
            #       "  CPU = " + str(itm['used_resources']['cpus']) + '/' + str(itm['unreserved_resources']['cpus']))
            self.slavesHN[itm['hostname']] = itm
            self.slavesID[itm['id']] = itm

    def print_slaves(self):
        for slaveId in self.slavesID.keys():
            itm = self.slavesID[slaveId]
            l.info(" Slave [" + itm['hostname'] + " ID=" + itm['id'] +
                   "  CPU = " + str(itm['used_resources']['cpus']) + '/' + str(itm['unreserved_resources']['cpus']))

    def get_slave_cnt(self):
        return self.noOfSlaves

    def get_id(self, id):
        return self.slavesID[id]

    def get_hn(self, hn):
        return self.slavesHN[hn]

    def get_ip_from_pid(self, pid):
        return pid.split('@')[1].split(':')[0]

    def get_slave_ip_from_id(self, slave_id):
        pid = self.slavesID[slave_id]['pid']
        return self.get_ip_from_pid(pid)

    def get_slave_ip_from_hn(self, slave_hn):
        pid = self.slavesHN[slave_hn]['pid']
        return self.get_ip_from_pid(pid)