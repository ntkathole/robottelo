# -*- encoding: utf-8 -*-
"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import (
    run_only_on,
    tier4,
)

from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.datafactory import valid_data_list
from robottelo.decorators import (
    skip_if_not_set,
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_oscapcontent, make_oscap_tailoringfile
from robottelo.ui.session import Session


class TailoringFilesTestCase(UITestCase):
    """Implements Tailoring Files tests in UI."""

    @classmethod
    @skip_if_not_set('oscap')
    def setUpClass(cls):
        super(TailoringFilesTestCase, cls).setUpClass()
        path = settings.oscap.content_path
        cls.content_path = get_data_file(path)
        file_path = settings.oscap.tailoring_path
        cls.tailoring_path = get_data_file(file_path)
        loc = entities.Location(name=gen_string('alpha')).create()
        cls.loc_name = loc.name
        org = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = org.name
        proxy = entities.SmartProxy().search(
            query={
                u'search': u'name={0}'.format(
                    settings.server.hostname)
            }
        )[0]
        proxy.organization = [org]

    @run_only_on('sat')
    @tier4
    def test_positive_oscap_run_with_tailoring_file_and_capsule(self):
        """ End-to-End Oscap run with tailoring files and default capsule

        :id: 346946ad-4f62-400e-9390-81817006048c

        :setup: scap content, scap policy, tailoring file, host group

        :steps:

            1. Create a valid scap content
            2. Upload a valid tailoring file
            3. Create a scap policy
            4. Associate scap content with it’s tailoring file
            5. Associate the policy with a hostgroup
            6. Provision a host using the hostgroup
            7. Puppet should configure and fetch the scap content
               and tailoring file

        :CaseAutomation: automated

        :expectedresults: ARF report should be sent to satellite reflecting
                         the changes done via tailoring files

        :CaseImportance: Critical
        """
        ''' with Session(self) as session:
            for content_name in valid_data_list():
                with self.subTest(content_name):
                    make_oscapcontent(
                        session,
                        name=content_name,
                        content_path=self.content_path,
                        content_org=self.org_name,
                    )'''
        with Session(self) as session:
            for tailoringfile_name in valid_data_list():
                with self.subTest(tailoringfile_name):
                    make_oscap_tailoringfile(
                        session,
                        name=tailoringfile_name,
                        tailoring_path=self.tailoring_path,
                        tailoring_loc=self.loc_name,
                        tailoring_org=self.org_name,
                    )
                    self.assertIsNotNone(
                        self.oscaptailoringfile.search(tailoringfile_name))
