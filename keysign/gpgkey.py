#!/usr/bin/env python
#    Copyright 2016 Tobias Mueller <muelli@cryptobitch.de>
#
#    This file is part of GNOME Keysign.
#
#    GNOME Keysign is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    GNOME Keysign is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with GNOME Keysign.  If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple
from datetime import datetime
import warnings

def parse_uid(uid):
    "Parses a GnuPG UID into it's name, comment, and email component"
    # remove the comment from UID (if it exists)
    com_start = uid.find('(')
    if com_start != -1:
        com_end = uid.find(')')
        uid = uid[:com_start].strip() + uid[com_end+1:].strip()

    # FIXME: Actually parse the comment...
    comment = ""
    # split into user's name and email
    tokens = uid.split('<')
    name = tokens[0].strip()
    email = 'unknown'
    if len(tokens) > 1:
        email = tokens[1].replace('>','').strip()
    
    return (name, comment, email)


def parse_expiry(value):
    """Takes either a string, an epoch, or a datetime and converts
    it to a datetime.
    If the string is empty (or otherwise evaluates to False)
    then this function returns None, meaning that no expiry has been set.
    An edge case is the epoch value "0".
    """
    if not value:
        expiry = None
    else:
        try:
            expiry = datetime.fromtimestamp(int(value))
        except TypeError:
            expiry = value

    return expiry




class Key(namedtuple("Key", "expiry fingerprint uidslist")):
    "Represents an OpenPGP Key to extent we care about"

    def __init__(self, expiry, fingerprint, uidslist,
                       *args, **kwargs):
        exp_date = parse_expiry(expiry)
        super(Key, self).__init__(exp_date, fingerprint, uidslist)

    def __format__(self, arg):
        s  = "{fingerprint}\r\n"
        s += '\r\n'.join(("  {}".format(uid) for uid in self.uidslist))
# This is what original output looks like:
# pub  [unknown] 3072R/1BF98D6D 1336669781 [expiry: 2017-05-09 19:09:41]
#    Fingerprint = FF52 DA33 C025 B1E0 B910  92FC 1C34 19BF 1BF9 8D6D
# uid 1      [unknown] Tobias Mueller <tobias.mueller2@mail.dcu.ie>
# uid 2      [unknown] Tobias Mueller <4tmuelle@informatik.uni-hamburg.de>
# sub   3072R/3B76E8B3 1336669781 [expiry: 2017-05-09 19:09:41]
        return s.format(**self._asdict())

    @property
    def fpr(self):
        "Legacy compatibility, use fingerprint instead"
        warnings.warn("Legacy fpr, use the fingerprint property",
                      DeprecationWarning)
        return self.fingerprint

    @classmethod
    def from_monkeysign(cls, key):
        "Creates a new Key from an existing monkeysign key"
        uids = [UID.from_monkeysign(uid) for uid in  key.uidslist]
        expiry = parse_expiry(key.expiry)
        fingerprint = key.fpr
        return cls(expiry, fingerprint, uids)

    @classmethod
    def from_gpgme(cls, key):
        "Creates a new Key from an existing monkeysign key"
        uids = [UID.from_gpgme(uid) for uid in  key.uids]
        expiry = parse_expiry(key.subkeys[0].expires)
        fingerprint = key.fpr
        return cls(expiry, fingerprint, uids)



class UID(namedtuple("UID", "expiry name comment email")):
    "Represents an OpenPGP UID - at least to the extent we care about it"

    @classmethod
    def from_monkeysign(cls, uid):
        "Creates a new UID from a monkeysign key"
        uidstr = uid.uid
        name, comment, email = parse_uid(uidstr)
        expiry = parse_expiry(uid.expire)

        return cls(expiry, name, comment, email)

    @classmethod
    def from_gpgme(cls, uid):
        "Creates a new UID from a monkeysign key"
        uidstr = uid.uid
        name = uid.name
        comment = '' # FIXME: uid.comment
        email = uid.email
        expiry = None  #  FIXME: Maybe UIDs don't expire themselves but via the binding signature

        return cls(expiry, name, comment, email)


    def __format__(self, arg):
        if self.comment:
            s = "{name} ({comment}) <{email}>"
        else:
            s = "{name} <{email}>"
        return s.format(**self._asdict())

    def __str__(self):
        return "{}".format(self)

    @property
    def uid(self):
        "Legacy compatibility, use str() instead"
        warnings.warn("Legacy uid, use '{}'.format() instead",
                      DeprecationWarning)
        return str(self)

