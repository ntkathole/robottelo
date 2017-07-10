# -*- encoding: utf-8 -*-
"""Test class for Login Message UI

:Requirement: loginmessage

:CaseAutomation: notautomated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:upstream: No
"""

from robottelo.decorators import run_only_on, tier1, stubbed
from robottelo.test import UITestCase


class LoginMessageTestCase(UITestCase):

    """Implements Login Message tests in UI."""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_with_valid_name(self):
        """Create new login message using different values types as name

                :id: a65a6920-69db-4902-81e9-55dc9970270f

                :steps:

                1. Navigate to Administer -> settings
                2. Click on general tab
                3. Give valid login page footer message


                :CaseAutomation: notautomated

                :expectedresults: Message should be displayed on login page.

                :CaseImportance: Critical
                """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new login message using invalid values

                :id: 0615e866-4f84-4ca0-a7ad-bf42151afa41

                :steps:

                1. Navigate to Administer -> settings
                2. Click on general tab
                3. Give invalid login page footer message


                :CaseAutomation: notautomated

                :expectedresults: Message should not be displayed on
                                  login page.

                :CaseImportance: Critical
                """
