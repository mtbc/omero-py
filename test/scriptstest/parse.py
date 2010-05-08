#!/usr/bin/env python

"""
   Test of the omero.scripts.parse functionality

   Copyright 2009 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""

import os
import sys
import uuid
import logging
import unittest

from path import path

import omero
from omero.scripts import *
from omero.util.temp_files import create_path

SCRIPTS = path(".") / "scripts" / "omero"

class TestParse(unittest.TestCase):

    def testParse(self):
        try:
            class mock(object):
                def setAgent(self, *args):
                    pass
                def createSession(self, *args):
                    return self
                def detachOnDestroy(self, *args):
                    pass
                def getProperty(self, *args):
                    return "true"
                def setOutput(self, *args):
                    pass
            script_client = client("testParse", "simple ping script", Long("a").inout(), String("b").inout(), client = mock())
            print "IN CLIENT: " + script_client.getProperty("omero.scripts.parse")
            self.fail("Should have raised ParseExit")
        except ParseExit, pe:
            pass

    def testMinMaxTicket2318(self):
        # Duplicating from some of the scripts to reproduce problem
        def makeParam(paramClass, name, description=None, optional=True, min=None, max=None, values=None):
             param = paramClass(name, optional, description=description, min=min, max=max, values=values)
             return param
        p = makeParam(Long, "thumbSize", "The dimension of each thumbnail. Default is 100", True, 10, 250)
        self.assertEquals(10, p.min.val)
        self.assertEquals(250, p.max.val)

    def testTicket2323(self):
        SCRIPT = """if True:
            import omero
            from omero.rtypes import rstring, rlong
            import omero.scripts as scripts
            client = scripts.client('HelloWorld.py', 'Hello World example script',
            scripts.Long('longParam', True, description='theDesc', min=long(1), max=long(10), values=[rlong(5)]) )
            client.setOutput('returnMessage', rstring('Script ran OK!'))"""
        params = parse_text(SCRIPT)
        longParam = params.inputs["longParam"]
        self.assertEquals(1, unwrap(longParam.min), str(longParam.min))
        self.assertEquals(10, unwrap(longParam.max), str(longParam.max))
        self.assertEquals([5], unwrap(longParam.values), str(longParam.values))

    def testListOfType(self):
        SCRIPT = """if True:
            import omero
            import omero.all
            from omero.rtypes import rstring, rlong
            import omero.scripts as scripts
            client = scripts.client('HelloWorld.py', 'Hello World example script',
                scripts.List('Image_List').ofType(omero.model.ImageI))
            client.setOutput('returnMessage', rstring('Script ran OK!'))"""
        params = parse_text(SCRIPT)
        listParam = params.inputs["Image_List"]
        self.assertTrue(isinstance(listParam.prototype.val[0].val, omero.model.Image))

    def testGrouping(self):
        SCRIPT = """if True:
            from omero.scripts import *
            c = client('testGrouping',
                Long('these', grouping="A.1"),
                Long('belong', grouping="A.2"),
                Long('together', grouping="A.3"))"""
        params = parse_text(SCRIPT)

        groupings = group_params(params)
        self.assertEquals("these", groupings["A"]["1"], str(groupings))
        self.assertEquals("belong", groupings["A"]["2"], str(groupings))
        self.assertEquals("together", groupings["A"]["3"], str(groupings))

    def testGroupingWithMain(self):
        SCRIPT = """if True:
            from omero.scripts import *
            c = client('testGrouping',
                Bool('checkbox', grouping="A"),
                Long('these', grouping="A.1"),
                Long('belong', grouping="A.2"),
                Long('together', grouping="A.3"))"""
        params = parse_text(SCRIPT)

        groupings = group_params(params)
        try:
            self.assertEquals("checkbox", groupings["A"][""], str(groupings))
            self.assertEquals("these", groupings["A"]["1"], str(groupings))
            self.assertEquals("belong", groupings["A"]["2"], str(groupings))
            self.assertEquals("together", groupings["A"]["3"], str(groupings))
        except KeyError:
            self.fail(str(groupings))

    def testGroupingWithMainExtraDot(self):
        SCRIPT = """if True:
            from omero.scripts import *
            c = client('testGrouping',
                Bool('checkbox', grouping="A."),
                Long('these', grouping="A.1"),
                Long('belong', grouping="A.2"),
                Long('together', grouping="A.3"))"""
        params = parse_text(SCRIPT)

        groupings = group_params(params)
        self.assertEquals("checkbox", groupings["A"][""], str(groupings))
        self.assertEquals("these", groupings["A"]["1"], str(groupings))
        self.assertEquals("belong", groupings["A"]["2"], str(groupings))
        self.assertEquals("together", groupings["A"]["3"], str(groupings))

    def testParseAllOfficialScripts(self):
        for script in SCRIPTS.walk("*.py"):
            try:
                params = parse_file(str(script))
            except exceptions.Exception, e:
                self.fail("%s\n%s" % (script, e))

    def testValidateRoiMovieCall(self):
        script = SCRIPTS / "figure_scripts" / "roiMovieFigure.py"
        params = parse_file(str(script))
        inputs = {
            "Merged_Colours": wrap(['red', 'green']),
            "Image_Labels": wrap("Datasets")
        }
        errors = validate_inputs(params, inputs)
        self.assertEquals("", errors, errors)

if __name__ == '__main__':
    logging.basicConfig()
    unittest.main()
