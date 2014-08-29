# -*- coding: utf-8 -*-
'''
Tests to try out keeping. Potentially ephemeral

'''
# pylint: skip-file
# pylint: disable=C0103
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import os
import time
import tempfile
import shutil

from ioflo.base.odicting import odict
from ioflo.base.aiding import Timer, StoreTimer
from ioflo.base import storing
from ioflo.base.consoling import getConsole
console = getConsole()

from raet import raeting, nacling
from raet.road import estating, keeping, stacking


def setUpModule():
    console.reinit(verbosity=console.Wordage.concise)

def tearDownModule():
    pass

class BasicTestCase(unittest.TestCase):
    """"""

    def setUp(self):
        self.store = storing.Store(stamp=0.0)
        self.timer = StoreTimer(store=self.store, duration=1.0)

        self.base = tempfile.mkdtemp(prefix="raet",  suffix="base", dir='/tmp')

    def tearDown(self):
        if os.path.exists(self.base):
            shutil.rmtree(self.base)

    def createRoadData(self, name, base, auto=None):
        '''
        Creates odict and populates with data to setup road stack
        {
            name: stack name local estate name
            dirpath: dirpath for keep files
            sighex: signing key
            verhex: verify key
            prihex: private key
            pubhex: public key
        }
        '''
        data = odict()
        data['name'] = name
        data['dirpath'] = os.path.join(base, 'road', 'keep', name)
        signer = nacling.Signer()
        data['sighex'] = signer.keyhex
        data['verhex'] = signer.verhex
        privateer = nacling.Privateer()
        data['prihex'] = privateer.keyhex
        data['pubhex'] = privateer.pubhex
        data['auto'] = auto

        return data

    def createRoadStack(self, data, uid=None, main=None, auto=None, ha=None):
        '''
        Creates stack and local estate from data with
        local estate.uid = uid
        stack.main = main
        stack.auto = auto
        stack.name = data['name']
        local estate.name = data['name']
        local estate.ha = ha

        returns stack

        '''
        stack = stacking.RoadStack(name=data['name'],
                                   uid=uid,
                                   ha=ha,
                                   sigkey=data['sighex'],
                                   prikey=data['prihex'],
                                   auto=auto if auto is not None else data['auto'],
                                   main=main,
                                   dirpath=data['dirpath'],
                                   store=self.store)

        return stack

    def join(self, initiator, correspondent, deid=None, duration=1.0,
                cascade=False):
        '''
        Utility method to do join. Call from test method.
        '''
        console.terse("\nJoin Transaction **************\n")
        if not initiator.remotes:
            initiator.addRemote(estating.RemoteEstate(stack=initiator,
                                                      fuid=0, # vacuous join
                                                      sid=0, # always 0 for join
                                                      ha=correspondent.local.ha))
        initiator.join(uid=deid, cascade=cascade)
        self.service(correspondent, initiator, duration=duration)

    def allow(self, initiator, correspondent, deid=None, duration=1.0,
                cascade=False):
        '''
        Utility method to do allow. Call from test method.
        '''
        console.terse("\nAllow Transaction **************\n")
        initiator.allow(uid=deid, cascade=cascade)
        self.service(correspondent, initiator, duration=duration)

    def alive(self, initiator, correspondent, deid=None, duration=1.0,
                cascade=False):
        '''
        Utility method to do alive. Call from test method.
        '''
        console.terse("\nAlive Transaction **************\n")
        initiator.alive(uid=deid, cascade=cascade)
        self.service(correspondent, initiator, duration=duration)

    def message(self, main, other, mains, others, duration=2.0):
        '''
        Utility to send messages both ways
        '''
        for msg in mains:
            main.transmit(msg)
        for msg in others:
            other.transmit(msg)

        self.service(main, other, duration=duration)

    def service(self, main, other, duration=1.0):
        '''
        Utility method to service queues. Call from test method.
        '''
        self.timer.restart(duration=duration)
        while not self.timer.expired:
            other.serviceAll()
            main.serviceAll()
            if not (main.transactions or other.transactions):
                break
            self.store.advanceStamp(0.1)
            time.sleep(0.1)

    def serviceStack(self, stack, duration=1.0):
        '''
        Utility method to service queues for one stack. Call from test method.
        '''
        self.timer.restart(duration=duration)
        while not self.timer.expired:
            stack.serviceAll()
            if not (stack.transactions):
                break
            self.store.advanceStamp(0.1)
            time.sleep(0.1)

    def serviceStacks(self, stacks, duration=1.0):
        '''
        Utility method to service queues for list of stacks. Call from test method.
        '''
        self.timer.restart(duration=duration)
        while not self.timer.expired:
            for stack in stacks:
                stack.serviceAll()
            if all([not stack.transactions for stack in stacks]):
                break
            self.store.advanceStamp(0.1)
            time.sleep(0.1)

    def serviceManageStacks(self, stacks, duration=1.0, cascade=False):
        '''
        Utility method to service queues and manage presence for list of stacks.
        Call from test method.
        '''
        self.timer.restart(duration=duration)
        while not self.timer.expired:
            for stack in stacks:
                stack.serviceAllRx()
                stack.manage(cascade=cascade)
                stack.serviceAllTx()
            if all([not stack.transactions for stack in stacks]):
                break
            self.store.advanceStamp(0.1)
            time.sleep(0.1)



    def testAlive(self):
        '''
        Test basic alive transaction
        '''
        console.terse("{0}\n".format(self.testAlive.__doc__))

        mainData = self.createRoadData(name='main',
                                       base=self.base,
                                       auto=raeting.autoModes.once)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     #uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     #uid=1,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        self.join(other, main)
        remotes = []
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            remotes.append(remote)
            self.assertIs(remote.joined, True)
            self.assertNotEqual(remote.nuid, 0)
            self.assertNotEqual(remote.fuid, 0)

        self.assertEqual(remotes[0].fuid, remotes[1].nuid)
        self.assertEqual(remotes[1].fuid, remotes[0].nuid)

        for stack in [main, other]:
            self.assertIs(stack.remotes.values()[0].allowed, None)
        self.allow(other, main)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)

        console.terse("\nAlive Other to Main *********\n")
        for stack in [main, other]:
            self.assertIs(stack.remotes.values()[0].alived, None)
        self.alive(other, main, deid=other.remotes.values()[0].uid)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)

        console.terse("\nAlive Main to Other *********\n")
        for stack in [main, other]:
            stack.remotes.values()[0].alived = None
            self.assertIs(stack.remotes.values()[0].alived, None)
        self.alive(main, other, deid=main.remotes.values()[0].uid)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)

        console.terse("\nDead Other from Main *********\n")
        # start alive from main to other but do not service responses from other
        # so main alive trans times out and other  appears dead to main
        for stack in [main, other]:
            self.assertIs(stack.remotes.values()[0].alived, True)
        main.alive()
        self.serviceStack(main, duration=3.0) # only service main
        self.assertEqual(len(main.transactions), 0) # timed out
        self.assertIs(main.remotes.values()[0].alived,  False)
        self.serviceStack(other, duration=3.0) # now service other side
        self.assertEqual(len(other.transactions), 0) # gets queued requests
        self.assertIs(other.remotes.values()[0].alived,  True)
        self.assertIs(main.remotes.values()[0].alived,  False)

        console.terse("\nDead Main from Other *********\n")
        # start alive from other to main but do not service responses from main
        # so other alive trans times out and main  appears dead to other
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
        self.assertIs(other.remotes.values()[0].alived, True)
        other.alive()
        self.serviceStack(other, duration=3.0) # only service other
        self.assertEqual(len(other.transactions), 0) # timed out
        self.assertIs(other.remotes.values()[0].alived, False)
        self.serviceStack(main, duration=3.0) # now service main side
        self.assertEqual(len(main.transactions), 0) # gets queued requests
        self.assertIs(main.remotes.values()[0].alived,  True)
        self.assertIs(other.remotes.values()[0].alived,  False)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

    def testAliveMultiple(self):
        '''
        Test alive transaction with multiple remotes
        '''
        console.terse("{0}\n".format(self.testAliveMultiple.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))


        self.join(other, main)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes.values()[0]
        self.assertTrue(otherRemote.joined)
        self.assertTrue(mainRemote.joined)

        self.allow(other, main)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes.values()[0]
        self.assertTrue(otherRemote.allowed)
        self.assertTrue(mainRemote.allowed)


        other1Data = self.createRoadData(name='other1', base=self.base)
        keeping.clearAllKeep(other1Data['dirpath'])
        other1 = self.createRoadStack(data=other1Data,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", 7532))


        self.join(other1, main)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other1.transactions), 0)
        other1Remote = main.remotes[other1.local.uid]
        main1Remote = other1.remotes.values()[0]
        self.assertTrue(other1Remote.joined)
        self.assertTrue(main1Remote.joined)

        self.allow(other1, main)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other1.transactions), 0)
        other1Remote = main.remotes[other1.local.uid]
        main1Remote = other1.remotes.values()[0]
        self.assertTrue(other1Remote.allowed)
        self.assertTrue(main1Remote.allowed)

        console.terse("\nAlive Other to Main *********\n")
        self.assertIs(otherRemote.alived, None)
        self.assertIs(mainRemote.alived, None)

        self.alive(other, main, deid=main.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertTrue(otherRemote.alived)
        self.assertTrue(mainRemote.alived)

        console.terse("\nAlive Main to Other *********\n")
        otherRemote.alived = None
        mainRemote.alived = None
        self.assertIs(otherRemote.alived, None)
        self.assertIs(mainRemote.alived, None)

        self.alive(main, other, deid=other.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertTrue(otherRemote.alived)
        self.assertTrue(mainRemote.alived)

        console.terse("\nAlive Other1 to Main *********\n")
        self.assertIs(other1Remote.alived, None)
        self.assertIs(main1Remote.alived, None)

        self.alive(other1, main, deid=main.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other1.transactions), 0)
        self.assertTrue(other1Remote.alived)
        self.assertTrue(main1Remote.alived)

        console.terse("\nAlive Main to Other1 *********\n")
        other1Remote.alived = None
        main1Remote.alived = None
        self.assertIs(other1Remote.alived, None)
        self.assertIs(main1Remote.alived, None)

        self.alive(main, other1, deid=other1.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other1.transactions), 0)
        self.assertTrue(other1Remote.alived)
        self.assertTrue(main1Remote.alived)

        console.terse("\nDead Other Alive Other1, from Main *********\n")
        self.assertTrue(main.remotes[other.local.uid].alived)
        self.assertTrue(main.remotes[other1.local.uid].alived)
        main.alive(uid=other.local.uid)
        main.alive(uid=other1.local.uid)
        # don't service other stack so it appears to be dead
        self.serviceStacks([main, other1], duration=3.0)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other1.transactions), 0)
        #self.assertTrue(other.local.uid not in main.remotes)
        self.assertIs(main.remotes[other.local.uid].alived, False)
        self.assertTrue(main.remotes[other1.local.uid].alived)

        self.serviceStacks([other, main], duration=3.0) #clean up
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertEqual(len(other1.transactions), 0)

        #bring it back to life
        console.terse("\nReliven other *********\n")
        other.alive(uid=main.local.uid, cascade=True)
        self.serviceStacks([other, main], duration=3.0)
        self.assertIs(main.remotes[other.local.uid].alived, True)
        self.assertIs(other.remotes[main.local.uid].alived, True)

        console.terse("\nAlive Other Dead Other 1 from Main *********\n")
        main.alive(uid=other.local.uid)
        main.alive(uid=other1.local.uid)
        self.serviceStacks([main, other], duration=3.0)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertFalse(other1Remote.alived)
        self.assertTrue(otherRemote.alived)

        self.serviceStacks([other1,  main], duration=3.0)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertEqual(len(other1.transactions), 0)

        #bring it back to life
        console.terse("\nReliven other1 *********\n")
        other1.alive(uid=main.local.uid, cascade=True)
        self.serviceStacks([other1, main], duration=3.0)
        self.assertIs(main.remotes[other1.local.uid].alived, True)
        self.assertIs(other1.remotes[main.local.uid].alived, True)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

        other1.server.close()
        other1.clearLocalKeep()
        other1.clearRemoteKeeps()


    def testAliveUnjoinedUnallowedBoth(self):
        '''
        Test alive transaction for other to main unjoined on main
        '''
        console.terse("{0}\n".format(self.testAliveUnjoinedUnallowedBoth.__doc__))

        mainData = self.createRoadData(name='main',
                                       base=self.base,
                                       auto=raeting.autoModes.once)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     #uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     #uid=1,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        self.join(other, main) # bootstrap channel
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)

        console.terse("\nAllow Other to Main *********\n")
        # force unjoined already unallowed unalived
        for stack in [main, other]:
            stack.remotes.values()[0].joined = None

        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.allow(other, main) # will join instead since unjoined
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, None)

        self.allow(other, main) # now try to allow again
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)

        console.terse("\nAllow Main to Other *********\n")
        # force unjoined already unallowed unalived
        for stack in [main, other]:
            stack.remotes.values()[0].joined = None
            stack.remotes.values()[0].allowed = None

        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.allow(main, other) # will join instead since unjoined
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, None)

        self.allow(main, other) # now try to allow again
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)

        console.terse("\nAlive Other to Main *********\n")
        # force unjoined unallowed already unalived
        for stack in [main, other]:
            stack.remotes.values()[0].joined = None
            stack.remotes.values()[0].alllowed = None

        # alive checks for joined and if not then joins
        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.alive(other, main)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)

        # Alive checks for allowed and if not allows
        self.alive(other, main)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, None)

        # Alive should complete now
        self.alive(other, main)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)

        console.terse("\nAlive Main to Other *********\n")
        # now do same from main to other
        # force unjoined unallowed unalived
        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            remote.joined = None
            remote.allowed = None
            remote.alived = None

        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.alive(main, other)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)

        # Alive checks for allowed and if not allows
        self.alive(main, other)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, None)

        # Alive should complete now
        self.alive(main, other)
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

    def testJoinAllowAliveCascadeBoth(self):
        '''
        Test allow transaction for other to main unjoined on both
        '''
        console.terse("{0}\n".format(self.testJoinAllowAliveCascadeBoth.__doc__))

        mainData = self.createRoadData(name='main',
                                       base=self.base,
                                       auto=raeting.autoModes.once)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other',
                                        base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        console.terse("\nJoin Other to Main Cascade *********\n")
        for stack in [main, other]:
            self.assertEqual(len(stack.remotes), 0)

        self.join(other, main, cascade=True) # now join cascade w
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True) # cascade will include alive
            self.assertIs(remote.alived, True)  # cascade will include alive

        console.terse("\Join Main to Other Cascade *********\n")
        main.server.close()
        other.server.close()
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        for stack in [main, other]:
            self.assertEqual(len(stack.remotes), 0)

        self.join(main, other) # bootstrap channel fails because other not main
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 0)

        # now fix it so other can accept vacuous joins
        other.main = True
        other.keep.auto = raeting.autoModes.once

        self.join(main, other) # bootstrap channel
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)

        # force unjoined already unallowed unalived
        for stack in [main, other]:
            stack.remotes.values()[0].joined = None

        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.join(main, other, cascade=True) # now alive cascade
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)  # cascade will include alive

        console.terse("\nAllow Other to Main Cascade *********\n")
        main.server.close()
        other.server.close()
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        for stack in [main, other]:
            self.assertEqual(len(stack.remotes), 0)

        self.join(other, main) # bootstrap channel since allow requires remote
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)

        # force unjoined already unallowed unalived
        for stack in [main, other]:
            stack.remotes.values()[0].joined = None

        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.allow(other, main, cascade=True) # now allow cascade so join then allow
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)  # cascade will include alive

        console.terse("\nAllow Main to Other Cascade *********\n")
        main.server.close()
        other.server.close()
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        for stack in [main, other]:
            self.assertEqual(len(stack.remotes), 0)

        self.join(main, other) # bootstrap channel fails because other not main
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 0)

        # now fix it so other can accept vacuous joins
        other.main = True
        other.keep.auto = raeting.autoModes.once

        self.join(main, other) # bootstrap channel since allow requires remote
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)

        # force unjoined already unallowed unalived
        for stack in [main, other]:
            stack.remotes.values()[0].joined = None

        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.allow(main, other, cascade=True) # now allow cascade so join then allow
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)  # cascade will include alive

        console.terse("\nAlive Other to Main Cascade *********\n")
        main.server.close()
        other.server.close()
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        for stack in [main, other]:
            self.assertEqual(len(stack.remotes), 0)

        self.join(other, main) # bootstrap channel
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)

        # force unjoined already unallowed unalived
        for stack in [main, other]:
            stack.remotes.values()[0].joined = None

        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.alive(other, main, cascade=True) # now alive cascade
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)  # cascade will include alive

        console.terse("\nAlive Main to Other Cascade *********\n")
        main.server.close()
        other.server.close()
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        for stack in [main, other]:
            self.assertEqual(len(stack.remotes), 0)

        self.join(main, other) # bootstrap channel fails because other not main
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 0)

        # now fix it so other can accept vacuous joins
        other.main = True
        other.keep.auto = raeting.autoModes.once

        self.join(main, other) # bootstrap channel
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)

        # force unjoined already unallowed unalived
        for stack in [main, other]:
            stack.remotes.values()[0].joined = None

        for stack in [main, other]:
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, None)
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)
        self.alive(main, other, cascade=True) # now alive cascade
        for stack in [main, other]:
            self.assertEqual(len(stack.transactions), 0)
            self.assertEqual(len(stack.remotes), 1)
            remote = stack.remotes.values()[0]
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)  # cascade will include alive

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

    def testAliveFromOtherUnjoinedOnMain(self):
        '''
        Test alive transaction for other to main unjoined on main
        '''
        console.terse("{0}\n".format(self.testAliveFromOtherUnjoinedOnMain.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        # join and allow
        self.join(other, main)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes[main.local.uid]
        self.assertIs(otherRemote.joined, True)
        self.assertIs(mainRemote.joined,  True)

        self.allow(other, main)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertIs(otherRemote.allowed, True)
        self.assertIs(mainRemote.allowed,  True)

        console.terse("\nOther unjoined Alive Other to Main *********\n")
        # set main's remote of other to not joined or allowed
        otherRemote.alived = None
        otherRemote.joined = None
        otherRemote.allowed = None

        self.alive(other, main)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes[main.local.uid]
        self.assertIs(otherRemote.joined, True)
        self.assertIs(mainRemote.joined,  True)
        self.assertIs(otherRemote.alived,  None)
        self.assertIs(mainRemote.alived,  None)

        self.alive(other, main, deid=main.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertIs(otherRemote.allowed, True)
        self.assertIs(mainRemote.allowed,  True)
        self.assertIs(otherRemote.alived,  None)
        self.assertIs(mainRemote.alived,  None)

        self.alive(other, main, deid=main.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertIs(otherRemote.alived,  True)
        self.assertIs(mainRemote.alived,  True)

        console.terse("\nAlive Main to Other *********\n")
        otherRemote.alived = None
        mainRemote.alived = None
        self.assertIs(otherRemote.alived, None)
        self.assertIs(mainRemote.alived, None)

        self.alive(main, other, deid=other.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertTrue(otherRemote.alived)
        self.assertTrue(mainRemote.alived)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()


    def testManageJoinedAllowed(self):
        '''
        Test stack manage remotes
        '''
        console.terse("{0}\n".format(self.testManageJoinedAllowed.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        other1Data = self.createRoadData(name='other1', base=self.base)
        keeping.clearAllKeep(other1Data['dirpath'])
        other1 = self.createRoadStack(data=other1Data,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", 7532))

        self.join(other, main)
        self.join(other1, main)
        self.allow(other, main)
        self.allow(other1, main)

        console.terse("\nTest manage remotes presence *********\n")
        console.terse("\nMake all alive *********\n")
        stacks = [main, other, other1]
        for remote in main.remotes.values(): #make all alive
            main.alive(uid=remote.uid)
        self.serviceStacks(stacks, duration=3.0)
        for remote in main.remotes.values():
            self.assertTrue(remote.alived)

        main.manage()
        for stack in stacks: # no alive transactions started
            self.assertEqual(len(stack.transactions), 0)

        console.terse("\nMake all expired so send alive *********\n")
        # advance clock so remote keep alive timers expire
        self.store.advanceStamp(stacking.RoadStack.Period + stacking.RoadStack.Offset)
        main.manage()
        for remote in main.remotes.values(): # should start
            self.assertIs(remote.alived, True)

        self.assertEqual(len(main.transactions), 2) # started 2 alive transactions

        self.serviceStacks(stacks, duration=3.0)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        for remote in main.remotes.values():
            self.assertTrue(remote.alived)


        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

        other1.server.close()
        other1.clearLocalKeep()
        other1.clearRemoteKeeps()


    def testJoinFromMain(self):
        '''
        Test join,initiated by main
        '''
        console.terse("{0}\n".format(self.testJoinFromMain.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        console.terse("\nJoin Main to Other *********\n")
        # create remote at mha=('127.0.0.1', other.local.ha[1])
        self.join(main, other)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        remote = main.remotes.values()[0]
        self.assertIs(remote.joined, None) # vacuous join from main is rejected
        main.removeRemote(remote)
        self.assertEqual(len(main.remotes), 0)
        self.assertEqual(len(main.nameRemotes), 0)
        self.assertEqual(len(main.haRemotes), 0)

        self.assertEqual(len(other.remotes), 0)
        self.assertEqual(len(other.nameRemotes), 0)
        self.assertEqual(len(other.haRemotes), 0)

        #now create remote for other and add to main
        main.addRemote(estating.RemoteEstate(stack=main,
                                             uid=2,
                                             name=otherData['name'],
                                             ha=('127.0.0.1', other.local.ha[1]),
                                             verkey=otherData['verhex'],
                                             pubkey=otherData['pubhex'], ))

        console.terse("\nJoin Main to Other Again *********\n")
        self.join(main, other, deid=2)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        remote = main.remotes.values()[0]
        self.assertIs(remote.joined, None) # non vacuous join from main is rejected

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

    def testYokeFromMain(self):
        '''
        Test join, allow, alive initiated by main
        '''
        console.terse("{0}\n".format(self.testYokeFromMain.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        console.terse("\nYoke Main to Other *********\n")
        self.yoke(main, other, mha=('127.0.0.1', other.local.ha[1]))
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertEqual(len(main.remotes), 0) # no remotes to yoke so fails
        self.assertEqual(len(main.nameRemotes), 0)
        self.assertEqual(len(main.haRemotes), 0)

        self.assertEqual(len(other.remotes), 0)
        self.assertEqual(len(other.nameRemotes), 0)
        self.assertEqual(len(other.haRemotes), 0)

        #now create remote for other and add to main
        main.addRemote(estating.RemoteEstate(stack=main,
                                             uid=2,
                                             name=otherData['name'],
                                             ha=('127.0.0.1', other.local.ha[1]),
                                             verkey=otherData['verhex'],
                                             pubkey=otherData['pubhex'],))

        console.terse("\nYoke Main to Other Again *********\n")
        self.yoke(main, other, deid=2)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes[main.local.uid]
        self.assertIs(otherRemote.joined, True)
        self.assertIs(mainRemote.joined, True)

        console.terse("\nAllow Main to Other *********\n")
        self.allow(main, other)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes.values()[0]
        self.assertTrue(otherRemote.allowed)
        self.assertTrue(mainRemote.allowed)

        console.terse("\nAlive Main to other *********\n")
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes[main.local.uid]
        self.assertIs(otherRemote.alived, None)
        self.assertIs(mainRemote.alived, None)
        self.alive(main, other, deid=other.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertTrue(otherRemote.alived)
        self.assertTrue(mainRemote.alived)

        console.terse("\nAlive Other to Main *********\n")
        otherRemote.alived = None
        mainRemote.alived = None
        self.assertIs(otherRemote.alived, None)
        self.assertIs(mainRemote.alived, None)
        self.alive(other, main, deid=main.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertTrue(otherRemote.alived)
        self.assertTrue(mainRemote.alived)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

    def testAllowFromMainUnjoinedOnMain(self):
        '''
        Test allow transaction for main to other unjoined on other
        '''
        console.terse("{0}\n".format(self.testAllowFromMainUnjoinedOnMain.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        #now create remote for other and add to main
        main.addRemote(estating.RemoteEstate(stack=main,
                                             uid=2,
                                             name=otherData['name'],
                                             ha=('127.0.0.1', other.local.ha[1]),
                                             verkey=otherData['verhex'],
                                             pubkey=otherData['pubhex'],))

        console.terse("\nBoth unjoined Allow Main to Other *********\n")
        self.assertEqual(len(main.remotes), 1)
        self.assertEqual(len(other.remotes), 0)

        self.allow(main, other)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes[main.local.uid]
        self.assertIs(otherRemote.joined, True)
        self.assertIs(mainRemote.joined,  True)
        self.assertIs(otherRemote.allowed,  None)
        self.assertIs(mainRemote.allowed,  None)

        self.allow(main, other, deid=other.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertIs(otherRemote.allowed, True)
        self.assertIs(mainRemote.allowed,  True)

        console.terse("\nAllow Other to Main *********\n")
        otherRemote.alived = None
        mainRemote.alived = None
        self.assertIs(otherRemote.alived, None)
        self.assertIs(mainRemote.alived, None)

        self.allow(other, main, deid=main.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertTrue(otherRemote.allowed)
        self.assertTrue(mainRemote.allowed)

        console.terse("\nBoth unjoined Allow Main to Other Cascade *********\n")
        main.server.close()
        other.server.close()
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        #now create remote for other and add to main
        main.addRemote(estating.RemoteEstate(stack=main,
                                             uid=2,
                                             name=otherData['name'],
                                             ha=('127.0.0.1', other.local.ha[1]),
                                             verkey=otherData['verhex'],
                                             pubkey=otherData['pubhex'],))

        self.assertEqual(len(main.remotes), 1)
        self.assertEqual(len(other.remotes), 0)

        self.allow(main, other, cascade=True)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes[main.local.uid]
        self.assertIs(otherRemote.joined, True)
        self.assertIs(mainRemote.joined,  True)
        self.assertIs(otherRemote.allowed,  True)
        self.assertIs(mainRemote.allowed,  True)
        self.assertIs(otherRemote.alived,  True)
        self.assertIs(mainRemote.alived,  True)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()


    def testAliveFromMainUnjoinedBoth(self):
        '''
        Test alive transaction for unjoined main to other
        '''
        console.terse("{0}\n".format(self.testAliveFromMainUnjoinedBoth.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        console.terse("\nBoth unjoined Alive Main to Other *********\n")
        self.assertEqual(len(main.remotes), 0)
        self.assertEqual(len(other.remotes), 0)

        #now create remote for other and add to main
        main.addRemote(estating.RemoteEstate(stack=main,
                                             uid=2,
                                             name=otherData['name'],
                                             ha=('127.0.0.1', other.local.ha[1]),
                                             verkey=otherData['verhex'],
                                             pubkey=otherData['pubhex'],))

        self.alive(main, other)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        otherRemote = main.remotes[other.local.uid]
        mainRemote = other.remotes[main.local.uid]
        self.assertIs(otherRemote.joined, True)
        self.assertIs(mainRemote.joined,  True)
        self.assertIs(otherRemote.alived,  None)
        self.assertIs(mainRemote.alived,  None)

        self.alive(main, other, deid=other.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertIs(otherRemote.allowed, True)
        self.assertIs(mainRemote.allowed,  True)
        self.assertIs(otherRemote.alived,  None)
        self.assertIs(mainRemote.alived,  None)

        self.alive(main, other, deid=other.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertIs(otherRemote.alived,  True)
        self.assertIs(mainRemote.alived,  True)

        console.terse("\nAlive Other to Main *********\n")
        otherRemote.alived = None
        mainRemote.alived = None
        self.assertIs(otherRemote.alived, None)
        self.assertIs(mainRemote.alived, None)

        self.alive(other, main, deid=main.local.uid)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 0)
        self.assertTrue(otherRemote.alived)
        self.assertTrue(mainRemote.alived)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()


    def testManageBothSides(self):
        '''
        Test stack manage remotes main and others
        '''
        console.terse("{0}\n".format(self.testManageBothSides.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        other1Data = self.createRoadData(name='other1', base=self.base)
        keeping.clearAllKeep(other1Data['dirpath'])
        other1 = self.createRoadStack(data=other1Data,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", 7532))

        self.join(other, main)
        self.join(other1, main)
        self.allow(other, main)
        self.allow(other1, main)

        console.terse("\nTest manage remotes presence both ways *********\n")
        console.terse("\nMake all alive *********\n")
        stacks = [main, other, other1]
        for remote in main.remotes.values(): #make all alive
            main.alive(uid=remote.uid)
        self.serviceStacks(stacks, duration=3.0)
        for remote in main.remotes.values():
            self.assertTrue(remote.alived)

        main.manage()
        other.manage()
        other1.manage()
        for stack in stacks: # no alive transactions started
            self.assertEqual(len(stack.transactions), 0)

        console.terse("\nMake all expired so send alive *********\n")
        # advance clock so remote keep alive timers expire
        self.store.advanceStamp(estating.RemoteEstate.Period + estating.RemoteEstate.Offset)
        main.manage()
        other.manage()
        other1.manage()

        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.alived, True)

        self.assertEqual(len(main.transactions), 2) # started 2 alive transactions
        self.assertEqual(len(other.transactions), 1) # started 1 alive transactions
        self.assertEqual(len(other1.transactions), 1) # started 1 alive transactions

        self.serviceManageStacks(stacks, duration=3.0)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)

        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.alived, True)


        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

        other1.server.close()
        other1.clearLocalKeep()
        other1.clearRemoteKeeps()

    def testManageMainRebootCascade(self):
        '''
        Test stack manage remotes as if main were rebooted
        '''
        console.terse("{0}\n".format(self.testManageMainRebootCascade.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        mainDirpath = mainData['dirpath']
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        otherDirpath = otherData['dirpath']
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        other1Data = self.createRoadData(name='other1', base=self.base)
        other1Dirpath = other1Data['dirpath']
        keeping.clearAllKeep(other1Data['dirpath'])
        other1 = self.createRoadStack(data=other1Data,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", 7532))


        self.join(other, main)
        self.join(other1, main)
        self.allow(other, main)
        self.allow(other1, main)

        console.terse("\nTest manage remotes presence *********\n")
        console.terse("\nMake all alive *********\n")
        stacks = [main, other, other1]
        for remote in main.remotes.values(): #make all alive
            main.alive(uid=remote.uid)
        self.serviceStacks(stacks, duration=3.0)
        for remote in main.remotes.values():
            self.assertTrue(remote.alived)

        main.manage(immediate=True)
        self.assertEqual(len(main.transactions), 2) # started 2 alive transactions
        for remote in main.remotes.values():
            self.assertIs(remote.alived, True)

        self.serviceStacks(stacks, duration=3.0)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        for remote in main.remotes.values():
            self.assertTrue(remote.alived)

        # now close down main and reload from saved data and manage
        console.terse("\nMake all alive with cascade after main reboots *********\n")
        main.server.close()
        main = stacking.RoadStack(dirpath=mainDirpath, store=self.store)
        stacks = [main, other, other1]

        for remote in main.remotes.values():
            self.assertIs(remote.joined, True) #joined status is persisted
            self.assertIs(remote.allowed, None)
            self.assertIs(remote.alived, None)

        main.manage(immediate=True, cascade=True)
        self.assertEqual(len(main.transactions), 2) # started 2 alive transactions
        for remote in main.remotes.values(): # should reset alive to None
            self.assertIs(remote.alived, None)
        self.serviceStacks(stacks, duration=3.0)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        for remote in main.remotes.values():
            self.assertIs(remote.joined, True)
            self.assertIs(remote.allowed, True)
            self.assertIs(remote.alived, True)

        # Now test as if others are rebooted
        console.terse("\nMake all alive with cascade after others reboot *********\n")
        other.server.close()
        other1.server.close()
        other = stacking.RoadStack(dirpath=otherDirpath, store=self.store)
        other1 = stacking.RoadStack(dirpath=other1Dirpath, store=self.store)
        stacks = [main, other, other1]

        self.assertIs(other.remotes[main.local.uid].joined, True)
        self.assertIs(other.remotes[main.local.uid].allowed, None)
        self.assertIs(other.remotes[main.local.uid].alived, None)
        self.assertIs(other1.remotes[main.local.uid].joined, True)
        self.assertIs(other1.remotes[main.local.uid].allowed, None)
        self.assertIs(other1.remotes[main.local.uid].alived, None)

        main.manage(immediate=True, cascade=True)
        self.assertEqual(len(main.transactions), 2) # started 2 alive transactions
        for remote in main.remotes.values():
            self.assertIs(remote.alived, True)
        self.serviceStacks(stacks, duration=3.0)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        self.assertIs(other.remotes[main.local.uid].joined, True)
        self.assertIs(other.remotes[main.local.uid].allowed, True)
        self.assertIs(other.remotes[main.local.uid].alived, True)
        self.assertIs(other1.remotes[main.local.uid].joined, True)
        self.assertIs(other1.remotes[main.local.uid].allowed, True)
        self.assertIs(other1.remotes[main.local.uid].alived, True)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

        other1.server.close()
        other1.clearLocalKeep()
        other1.clearRemoteKeeps()

    def testManageRebootCascadeBothSides(self):
        '''
        Test stack manage remotes as if main were rebooted
        '''
        console.terse("{0}\n".format(self.testManageRebootCascadeBothSides.__doc__))

        mainData = self.createRoadData(name='main', base=self.base, auto=True)
        mainDirpath = mainData['dirpath']
        keeping.clearAllKeep(mainData['dirpath'])
        main = self.createRoadStack(data=mainData,
                                     uid=1,
                                     main=True,
                                     auto=mainData['auto'],
                                     ha=None)

        otherData = self.createRoadData(name='other', base=self.base)
        otherDirpath = otherData['dirpath']
        keeping.clearAllKeep(otherData['dirpath'])
        other = self.createRoadStack(data=otherData,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", raeting.RAET_TEST_PORT))

        other1Data = self.createRoadData(name='other1', base=self.base)
        other1Dirpath = other1Data['dirpath']
        keeping.clearAllKeep(other1Data['dirpath'])
        other1 = self.createRoadStack(data=other1Data,
                                     uid=0,
                                     main=None,
                                     auto=None,
                                     ha=("", 7532))


        self.join(other, main)
        self.join(other1, main)
        self.allow(other, main)
        self.allow(other1, main)

        console.terse("\nTest manage remotes presence *********\n")
        console.terse("\nMake all alive *********\n")
        stacks = [main, other, other1]
        for remote in main.remotes.values(): #make all alive
            main.alive(uid=remote.uid)
        self.serviceStacks(stacks, duration=3.0)
        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.alived, True)

        main.manage(immediate=True)
        other.manage(immediate=True)
        other1.manage(immediate=True)
        self.assertEqual(len(main.transactions), 2) # started 2 alive transactions
        self.assertEqual(len(other.transactions), 1) # started 1 alive transactions
        self.assertEqual(len(other1.transactions), 1) # started 1 alive transactions

        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.alived, True)

        self.serviceManageStacks(stacks, duration=3.0)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.alived, True)

        # now test if main rebooted
        console.terse("\nMake all alive with cascade after main reboots *********\n")
        main.server.close()
        main = stacking.RoadStack(dirpath=mainDirpath, store=self.store)
        stacks = [main, other, other1]

        for stack in [main]:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, True) #joined status is persisted
                self.assertIs(remote.allowed, None)
                self.assertIs(remote.alived, None)

        for stack in [other, other1]:
            for remote in stack.remotes.values():
                 self.assertIs(remote.joined, True) #joined status is persisted
                 self.assertIs(remote.allowed, True)
                 self.assertIs(remote.alived, True)

        main.manage(immediate=True, cascade=True)
        other.manage(cascade=True)
        other1.manage(cascade=True)
        self.assertEqual(len(main.transactions), 2)
        self.assertEqual(len(other.transactions), 0)
        self.assertEqual(len(other1.transactions), 0)

        for stack in [main]:
            for remote in stack.remotes.values():
                self.assertIs(remote.alived, None)

        for stack in [other, other1]:
             for remote in stack.remotes.values():
                self.assertIs(remote.alived, True)

        self.serviceManageStacks(stacks, duration=3.0, cascade=True)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, True) #joined status is persisted
                self.assertIs(remote.allowed, True)
                self.assertIs(remote.alived, True)

        # Now test as if others are rebooted but not main
        console.terse("\nMake all alive with cascade after others reboot *********\n")
        other.server.close()
        other1.server.close()
        other = stacking.RoadStack(dirpath=otherDirpath, store=self.store)
        other1 = stacking.RoadStack(dirpath=other1Dirpath, store=self.store)
        stacks = [main, other, other1]

        for stack in [main]:
            for remote in stack.remotes.values():
                self.assertIs(remote.alived, True)

        for stack in [other, other1]:
             for remote in stack.remotes.values():
                self.assertIs(remote.joined, True)
                self.assertIs(remote.allowed, None)
                self.assertIs(remote.alived, None)

        main.manage(cascade=True)
        other.manage(immediate=True,cascade=True)
        other1.manage(immediate=True,cascade=True)
        self.assertEqual(len(main.transactions), 0)
        self.assertEqual(len(other.transactions), 1)
        self.assertEqual(len(other1.transactions), 1)

        for stack in [main]:
            for remote in stack.remotes.values():
                self.assertIs(remote.alived, True)

        for stack in [other, other1]:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, True)
                self.assertIs(remote.allowed, None)
                self.assertIs(remote.alived, None)

        self.serviceManageStacks(stacks, duration=3.0, cascade=True)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, True)
                self.assertIs(remote.allowed, True)
                self.assertIs(remote.alived, True)

        # now close down all and reload from saved data and manage
        console.terse("\nMake all alive with cascade after all reboot *********\n")
        main.server.close()
        main = stacking.RoadStack(dirpath=mainDirpath, store=self.store)
        other.server.close()
        other = stacking.RoadStack(dirpath=otherDirpath, store=self.store)
        other1.server.close()
        other1 = stacking.RoadStack(dirpath=other1Dirpath, store=self.store)

        stacks = [main, other, other1]

        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, True) #joined status is persisted
                self.assertIs(remote.allowed, None) # None on reload from file
                self.assertIs(remote.alived, None) # None on reload from file

        main.manage(immediate=True, cascade=True)
        other.manage(immediate=True, cascade=True)
        other1.manage(immediate=True, cascade=True)
        self.assertEqual(len(main.transactions), 2) # started 2 alive transactions
        self.assertEqual(len(other.transactions), 1) # started 1 alive transactions
        self.assertEqual(len(other1.transactions), 1) # started 1 alive transactions
        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, True) #joined status is persisted
                self.assertIs(remote.allowed, None) # None on reload from file
                self.assertIs(remote.alived, None) # None on reload from file

        self.serviceManageStacks(stacks, duration=3.0)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, True)
                self.assertIs(remote.allowed, True)
                self.assertIs(remote.alived, True)

        # now close down all and reload from saved data but loose joined status
        console.terse("\nMake all alive with cascade after all reboot and lose join *********\n")
        main.server.close()
        main = stacking.RoadStack(dirpath=mainDirpath, store=self.store)
        other.server.close()
        other = stacking.RoadStack(dirpath=otherDirpath, store=self.store)
        other1.server.close()
        other1 = stacking.RoadStack(dirpath=other1Dirpath, store=self.store)

        stacks = [main, other, other1]

        for stack in stacks:
            for remote in stack.remotes.values():
                remote.joined = None
                self.assertIs(remote.joined, None) #joined status is persisted
                self.assertIs(remote.allowed, None) # None on reload from file
                self.assertIs(remote.alived, None) # None on reload from file

        main.manage(immediate=True, cascade=True)
        other.manage(immediate=True, cascade=True)
        other1.manage(immediate=True, cascade=True)
        self.assertEqual(len(main.transactions), 2) # started 2 alive transactions
        self.assertEqual(len(other.transactions), 1) # started 1 alive transactions
        self.assertEqual(len(other1.transactions), 1) # started 1 alive transactions
        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, None) #joined status is persisted
                self.assertIs(remote.allowed, None) # None on reload from file
                self.assertIs(remote.alived, None) # None on reload from file

        self.serviceManageStacks(stacks, duration=3.0)
        for stack in stacks:
            self.assertEqual(len(stack.transactions), 0)
        for stack in stacks:
            for remote in stack.remotes.values():
                self.assertIs(remote.joined, True)
                self.assertIs(remote.allowed, True)
                self.assertIs(remote.alived, True)

        main.server.close()
        main.clearLocalKeep()
        main.clearRemoteKeeps()

        other.server.close()
        other.clearLocalKeep()
        other.clearRemoteKeeps()

        other1.server.close()
        other1.clearLocalKeep()
        other1.clearRemoteKeeps()

def runOne(test):
    '''
    Unittest Runner
    '''
    test = BasicTestCase(test)
    suite = unittest.TestSuite([test])
    unittest.TextTestRunner(verbosity=2).run(suite)

def runSome():
    '''
    Unittest runner
    '''
    tests =  []
    names = ['testAlive',
             'testAliveMultiple',
             'testAliveUnjoinedUnallowedBoth',
             'testJoinAllowAliveCascadeBoth',
             'testManageJoinedAllowed',
             'testJoinFromMain',
             'testYokeFromMain',
             'testAllowFromMainUnjoinedOnMain',
             'testAliveFromMainUnjoinedBoth',
             'testManageBothSides',
             'testManageMainRebootCascade',
             'testManageRebootCascadeBothSides', ]

    tests.extend(map(BasicTestCase, names))

    suite = unittest.TestSuite(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

def runAll():
    '''
    Unittest runner
    '''
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(BasicTestCase))

    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__' and __package__ is None:

    #console.reinit(verbosity=console.Wordage.concise)

    #runAll() #run all unittests

    runSome()#only run some

    #runOne('testJoinAllowAliveCascadeBoth')
