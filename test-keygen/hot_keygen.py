#!/usr/bin/python

import os
import math
import random
from hashlib import sha256 as SHA256
import hmac as HMAC
from LMS_func import *   # Byteprint, bytstr, calc_p, and calc_ls

def LMS_genprvkey():

   if os.path.exists("keyfile") or os.path.exists("statefile"):
      print "\nSignature scheme already initialized.\n"
      os._exit(1)
   else:
      # Generate LMS private key
      prvkeyfile = open("prvkeyfile","wb",0)
      LMSprvkey = bytstr(random.getrandbits(256),32)
      prvkeyfile.write(LMSprvkey)
      # Initialize state file
      statefile = open("statefile","w",0)
      statefile.write('\x00')
      # Cleanup and return
      prvkeyfile.close()
      statefile.close()
      return LMSprvkey

def calc_LMOTSprvkey(LMSprvkey, LMID, n, MPRT, MNUM):
   '''Calculate one LMOTS private key (list) from the LMS private key (seed)'''

   # Generate per-message LMOTS seed from LMS private key

   string = "LMOTS"+bytstr(0,1)+LMID+bytstr(MNUM,4)+bytstr(n*8,2)
   OTSprvseed = HMAC.new(LMSprvkey, string, SHA256).digest()
   Byteprint("\nLMOTS seed: ", OTSprvseed)     # debug

   # Generate per-message p-element LMOTS private key

   LMOTSprvkey = []
   for i in xrange(0, MPRT):
     string = bytstr(i,4)+"LMS"+bytstr(0,1)+LMID+bytstr(MNUM,4)+bytstr(n*8,2)
     LMOTSprvkey.append(SHA256(OTSprvseed+string).digest())
     Byteprint("\nX["+str(i)+"] = ", LMOTSprvkey[i])     # debug

   return LMOTSprvkey


def calc_LMOTSpubkey(LMSprvkey, LMID, n, w, MNUM):
   '''Calculate one LMOTS public key from the LMS private key (seed).'''

   D_ITER = '\x00'
   D_PBLC = '\x01'

   # Generate per-message LMOTS seed from LMS private key

   MPRT = calc_p(n, w)
   LMOTSprvkey = calc_LMOTSprvkey(LMSprvkey, LMID, n, MPRT, MNUM)

   # Generate per-message p-element LMOTS public key vector

   y = []
   for i in xrange(0, MPRT):
     tmp = LMOTSprvkey[i]
     for j in xrange(0, 2**w-1):
       tmp = SHA256(tmp+LMID+bytstr(MNUM,4)+bytstr(i,2)+bytstr(j,2)+D_ITER).digest()
     y.append(tmp)

   # Generate per-message n-byte LMOTS public key

   Y = SHA256()
   Y.update(LMID+bytstr(MNUM,4))
   for i in xrange(0, MPRT):
     Y.update(y[i])
   Y.update(D_PBLC)
   return Y.digest()


def calc_LMS_pub(h, LMID, OTSpubkeys):
   '''Calculate the n-byte LMS public key from a set n-byte LMOTS public keys.'''

   nodefile = open("nodefile", "wb", 0)

   D_LEAF = '\x03'
   D_INTR = '\x04'

   D = []   # data stack
   I = []   # integer stack
   NODES = []

   for i in xrange(0, 2**h, 2):
      level = 0
      for j in xrange(0, 2):
         NODN = 2**h+i+j
         print "\ni = ", i,"j = ",j,"Leaf node number = ", NODN     # debug
         NODV = SHA256(OTSpubkeys[i+j]+LMID+bytstr(NODN)+D_LEAF).digest()
         Byteprint("NODV: ",NODV)     # debug
         NODES.append([NODN, NODV])
         D.append(NODV)
         print "   Leaf ",i+j," pushed onto data stack."     # debug
         
         I.append(level)
         print "j loop: I, len(I) = ",I, len(I)     # debug
      while len(I) >= 2:
         if I[-2] == I[-1]:
            TMP = SHA256()
            siblings = ""
            for k in (1, 2):
               siblings = D.pop()+siblings
               print "Child value popped from data stack."     #debug
               level = I.pop()
               print "I = ",I, "level = ", level     # debug
            TMP.update(siblings)
            NODN = (2**h+i)/(2**(level+1))
            print "Tree node number: ", NODN     # debug
            TMP.update(LMID+bytstr(NODN)+D_INTR)
            NODV = TMP.digest()
            NODES.append([NODN, NODV])
            D.append(NODV)
            print "Two child values hashed and pushed on data stack."     # debug
            I.append(level+1)
            print "while loop: I, len(I) = ", I, len(I)     # debug
         else:
            break
   NODES.sort()
   for i in NODES:
      nodefile.write(bytstr(i[0],1)+':'+i[1])
   nodefile.close()
   return D.pop()


def LMS_genpubkey(LMSprvkey, h, n, w, LMID):

   OTSpubkeys = []

   for i in xrange(0, 2**h):
      OTSpubkeys.append(calc_LMOTSpubkey(LMSprvkey, LMID, n, w, i))

   #---------- Print statements for debug ----------
   for i in xrange(0, 2**h):
      Byteprint("\nLMOTS public key ["+str(i)+"] = ", OTSpubkeys[i])
   #---------- Print statements for debug ----------


   # Generate LMS public key (calc hash tree)

   LMSpubkey = calc_LMS_pub(h, LMID, OTSpubkeys)
   return LMSpubkey

# ===== BEGIN MAIN PROGRAM ===== # ===== BEGIN MAIN PROGRAM ===== #

from LMOTS_SHA256_N32_W4 import *

h = 4
LMID = "LMS_SHA256_N32_W4_H5\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e"

LMSprvkey = LMS_genprvkey()
Byteprint("\nLMS private key: ", LMSprvkey)     # debug

LMSpubkey = LMS_genpubkey(LMSprvkey, h, n, w, LMID)
Byteprint("\nLMS public key: ", LMSpubkey)     #debug

# Write out LMS public key (u32str(type)||I||T[1])

pubkeyfile = open("pubkeyfile", "wb")
pubkeyfile.write(typecode+LMID+LMSpubkey)
pubkeyfile.close()

