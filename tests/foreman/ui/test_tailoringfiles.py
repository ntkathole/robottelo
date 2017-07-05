"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import run_only_on, tier1, tier2, tier3, stubbed
from robottelo.test import UITestCase


class TailoringFilesTestCase(UITestCase):
    """Implements Tailoring Files tests in UI."""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create(self):
        """Create new Tailoring Files using different values types as name

        :id:

        :setup: tailoring file

        :steps:

        1. Navigate to Tailoring files menu
        2. Upload a valid tailoring file
        3. Give it a valid name


        :CaseAutomation: Automated

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_with_space(self):
        """Create tailoring files with space in name

        :id:

        :setup: tailoring file

        :steps:

        1. Navigate to Tailoring files menu
        2. Upload a valid tailoring file
        3. Give it a name with space

        :CaseAutomation: Automated

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_with_valid_file(self):
        """Create Tailoring files with valid file

        :id:

        :setup: tailoring file

        :steps:

        1. Navigate to Tailoring files menu
        2. With valid name ,upload a valid tailoring file


        :CaseAutomation: Automated

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_creat_with_invalid_file(self):
        """Create Tailoring files with invalid file

        :id:

        :setup: invalid tailoring file

        :steps:

        1. Navigate to Tailoring files menu
        2. With valid name ,upload  invalid tailoring file

        :CaseAutomation: Automated

        :expectedresults: Tailoring file will not be added to satellite

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_associate_tailoring_file_with_scap(self):
        """ Associate a Tailoring file with it’s scap content

        :id:

        :setup: scap content and tailoring file

        :steps:

        1. Create a valid scap content
        2. Upload a vaild tailoring file
        3. Associate scap content with it’s tailoring file

        :CaseAutomation: Automated

        :expectedresults: Association should be successful

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_associate_tailoring_file_with_different_scap(self):
        """ Associate a tailoring file with different scap content

        :id:

        :setup: scap content and tailoring file

        :steps:

        1. Create a valid scap content
        2. Upload a Mutually exclusive tailoring file
        3. Associate the scap content with tailoring file


        :CaseAutomation: Automated

        :expectedresults: Association should fail

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_download_tailoring_file(self):
        """ Download the tailoring file from satellite

        :id:

        :setup: tailoring file

        :steps:

        1. Upload a tailoring file
        2. Create tailoring file in satellite
        3. Download the uploaded tailoring file


        :CaseAutomation: Automated

        :expectedresults: The tailoring file should be downloaded

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_tailoring_file(self):
        """ Delete tailoring file

        :id:

        :setup: tailoring file

        :steps:

        1. Upload a tailoring file
        2. Create tailoring file in satellite
        3. Delete the created tailoring file.

        :CaseAutomation: Automated

        :expectedresults: Tailoring file should be deleted

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_oscap_run_with_tailoring_file_and_capsule(self):
        """ End-to-End Oscap run with tailoring files and default capsule

        :id:

        :setup: scap content, scap policy, tailoring file, host group, host

        :steps:

        1. Create a valid scap content
        2. Upload a valid tailoring file
        3. Create a scap policy
        4. Associate scap content with it’s tailoring file
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Puppet should configure and fetch the scap content and tailoring file


        :CaseAutomation: Automated

        :expectedresults: ARF report should be sent to satellite reflecting the changes done via tailoring files


        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_oscap_run_with_tailoring_file_and_external_capsule(self):
        """ End-to-End Oscap run with tailoring files and external capsule

        :id:

        :setup: scap content, scap policy, tailoring file, host group, host

        :steps:

        1. Create a valid scap content
        2. Upload a valid tailoring file
        3. Create a scap policy
        4. Associate scap content with it’s tailoring file
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Puppet should configure and fetch the scap content and tailoring file from external capsule


        :CaseAutomation: Automated

        :expectedresults: ARF report should be sent to satellite reflecting the changes done via tailoring files

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_fetch_tailoring_file_information_from_arfreports(self):
        """ Fetch Tailoring file Information from Arf-reports
        :id:

        :setup: scap content, scap policy, tailoring file, host group, host

        :steps:

        1. Create a valid scap content
        2. Upload a valid tailoring file
        3. Create a scap policy
        4. Associate scap content with it’s tailoring file
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Puppet should configure and fetch the scap content and send arf-report to satellite

        :CaseAutomation: Automated

        :expectedresults: ARF report should have information about the tailoring file used, if any

        :CaseImportance: Critical

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_tailoring_file_options_with_no_capsule_support(self):
        """ Tailoring Files Options with no capsule support(Eg. 6.2 cap)

        :id:

        :setup:

        :steps:

        1. Navigate to Tailoring Files menu.

        :CaseAutomation: Automated

        :expectedresults:  Display a message about no supported capsule

        :CaseImportance: Critical

        """
