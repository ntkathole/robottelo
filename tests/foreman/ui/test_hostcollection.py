# -*- encoding: utf-8 -*-
"""Test class for Host Collection UI

:Requirement: Hostcollection

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.api.utils import promote
from robottelo.cleanup import vm_cleanup
from robottelo.cli.factory import (
    make_fake_host,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.constants import (
    DISTRO_RHEL7,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_GROUP,
    FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.datafactory import (
    invalid_names_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier3,
)
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_host_collection
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine
from time import sleep


class HostCollectionTestCase(UITestCase):
    """Implements Host Collection tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(HostCollectionTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create Host Collection for all name variations

        :id: 267bd784-1ef7-4270-a264-6f8659e239fd

        :expectedresults: Host Collection is created

        :CaseImportance: Critical
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_host_collection(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(self.hostcollection.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Host Collection with valid description

        :id: 830ff39e-0d4c-4368-bc47-12b060a09410

        :expectedresults: Host Collection is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session,
                name=name,
                org=self.organization.name,
                description=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.hostcollection.search(name))

    @tier1
    def test_positive_create_with_limit(self):
        """Create Host Collection with finite content hosts limit

        :id: 9983b61d-f820-4b60-ae5e-a45925f2dcf0

        :expectedresults: Host Collection is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name, limit='10')
            self.assertIsNotNone(self.hostcollection.search(name))

    @tier1
    def test_negative_create_with_name(self):
        """Create Host Collections with invalid name

        :id: 04e36c46-7577-4308-b9bb-4ec74549d9d3

        :expectedresults: Host Collection is not created and appropriate error
            message thrown

        :CaseImportance: Critical
        """
        with Session(self.browser) as session:
            for name in invalid_values_list('ui'):
                with self.subTest(name):
                    make_host_collection(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['common_invalid'])
                    )

    @skip_if_bug_open('bugzilla', 1300350)
    @tier1
    def test_negative_create_with_invalid_limit(self):
        """Create Host Collections with invalid Content Host Limit value. Both
        with too long numbers and using letters.

        :id: c15b3540-809e-4339-ad5f-1ab488244299

        :expectedresults: Host Collection is not created. Appropriate error
            shown.

        :CaseImportance: Critical
        """
        with Session(self.browser) as session:
            for limit in invalid_names_list():
                with self.subTest(limit):
                    make_host_collection(
                        session,
                        name=gen_string('alpha'),
                        org=self.organization.name,
                        limit=limit,
                    )
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['invalid_limit'])
                    )

    @tier1
    def test_positive_update_name(self):
        """Update existing Host Collection name

        :id: 9df33661-7a9c-40d9-8f2c-52e5ed21c156

        :expectedresults: Host Collection is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.hostcollection.update(name, new_name=new_name)
                    self.assertIsNotNone(self.hostcollection.search(new_name))
                    name = new_name

    @tier1
    def test_positive_update_description(self):
        """Update existing Host Collection entity description

        :id: 5ef92657-489f-46a2-9b3a-e40322ca86d8

        :expectedresults: Host Collection is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session,
                name=name,
                org=self.organization.name,
                description=gen_string('alpha'),
            )
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    self.hostcollection.update(name, description=new_desc)
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['alert.success_sub_form'])
                    )
                    self.assertTrue(self.hostcollection.validate_field_value(
                        name, 'description', new_desc))

    @tier1
    def test_positive_update_limit(self):
        """Update Content Host limit from Unlimited to a finite number

        :id: 6f5015c4-06c9-4873-806e-5f9d39c9d8a8

        :expectedresults: Host Collection is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            self.hostcollection.update(name, limit='25')
            self.assertIsNotNone(self.hostcollection.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.assertTrue(self.hostcollection.validate_field_value(
                name, 'limit', '25'))

    @tier1
    def test_positive_update_limit_to_unlimited(self):
        """Update Content Host limit from definite number to Unlimited

        :id: 823acd9e-1259-47b6-8236-7547ef3fff98

        :expectedresults: Host Collection is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name, limit='15')
            self.assertIsNotNone(self.hostcollection.search(name))
            self.hostcollection.update(name, limit='Unlimited')
            self.assertIsNotNone(self.hostcollection.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.assertTrue(self.hostcollection.validate_field_value(
                name, 'limit', 'Unlimited'))

    @tier1
    def test_negative_update_name(self):
        """Update existing Host Collection entity name with invalid value

        :id: 7af999e8-5189-45c0-a92d-8c05b03f556a

        :expectedresults: Host Collection is not updated.  Appropriate error
            shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.hostcollection.update(name, new_name=new_name)
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['alert.error_sub_form'])
                    )

    @tier1
    def test_negative_update_limit(self):
        """Update Host Collection with invalid Content Host Limit

        :id: 3f3749f9-cf52-4897-993f-804def785510

        :expectedresults: Host Collection is not updated.  Appropriate error
            shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for limit in ' ', -1, 'text', '0':
                with self.subTest(limit):
                    with self.assertRaises(ValueError):
                        self.hostcollection.update(name, limit=limit)

    @tier1
    def test_positive_delete(self):
        """Create Host Collection and delete it for all variations of name

        :id: 978a985c-29f4-4b1f-8c68-8cd412af21e6

        :expectedresults: Host Collection is deleted

        :CaseImportance: Critical
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_host_collection(
                        session, name=name, org=self.organization.name)
                    self.assertIsNotNone(self.hostcollection.search(name))
                    self.hostcollection.delete(name)

    @tier1
    def test_positive_copy(self):
        """Create Host Collection and copy it

        :id: af8d968c-8241-40dc-b92c-81965f470191

        :expectedresults: Host Collection copy exists

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.hostcollection.copy(name, new_name)
                    self.assertIsNotNone(
                        self.hostcollection.search(new_name))

    @skip_if_bug_open('bugzilla', 1461016)
    @tier1
    def test_negative_copy(self):
        """Create Host Collection and copy it. Use invalid values for copy name

        :id: 99d47520-c09a-4fbc-8e53-a4e889af0187

        :expectedresults: Host Collection copy does not exist

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.hostcollection.copy(name, new_name)
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['alert.error_sub_form'])
                    )

    @tier3
    def test_positive_add_host(self):
        """Check if host can be added to Host Collection

        :id: 80824c9f-15a1-4f76-b7ac-7d9ca9f6ed9e

        :expectedresults: Host is added to Host Collection successfully

        :CaseLevel: System
        """
        name = gen_string('alpha')
        cv = entities.ContentView(organization=self.organization).create()
        lce = entities.LifecycleEnvironment(
            organization=self.organization).create()
        cv.publish()
        promote(cv.read().version[0], lce.id)
        new_system = make_fake_host({
            u'content-view-id': cv.id,
            u'lifecycle-environment-id': lce.id,
            u'name': gen_string('alpha'),
            u'organization-id': self.organization.id,
        })
        with Session(self.browser) as session:
            make_host_collection(
                session, org=self.organization.name, name=name)
            self.hostcollection.add_host(name, new_system['name'])

    @tier3
    def test_negative_hosts_limit(self):
        """Check that Host limit actually limits usage

        :id: 57b70977-2110-47d9-be3b-461ad15c70c7

        :Steps:
            1. Create Host Collection entity that can contain only one Host
                (using Host Limit field)
            2. Create Host and add it to Host Collection. Check that it was
                added successfully
            3. Create one more Host and try to add it to Host Collection
            4. Check that expected error is shown

        :expectedresults: Second host is not added to Host Collection and
            appropriate error is shown

        :CaseLevel: System
        """
        name = gen_string('alpha')
        org = entities.Organization().create()
        cv = entities.ContentView(organization=org).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        cv.publish()
        promote(cv.read().version[0], lce.id)
        new_systems = [
            make_fake_host({
                u'content-view-id': cv.id,
                u'lifecycle-environment-id': lce.id,
                u'name': gen_string('alpha'),
                u'organization-id': org.id,
            })['name']
            for _ in range(2)
        ]
        with Session(self.browser) as session:
            make_host_collection(
                session, org=org.name, name=name, limit='1')
            self.hostcollection.add_host(name, new_systems[0])
            with self.assertRaises(UIError):
                self.hostcollection.add_host(name, new_systems[1])
            self.assertIsNotNone(self.hostcollection.wait_until_element(
                common_locators['alert.error_sub_form']))


@run_in_one_thread
class HostCollectionPackageManagementTest(UITestCase):
    """Implements Host Collection package management related tests in UI"""

    hosts_number = 2  # number of hosts per host collection

    @classmethod
    def set_session_org(cls):
        """Create an organization for tests, which will be selected
        automatically
        """
        cls.session_org = entities.Organization().create()

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key"""
        super(HostCollectionPackageManagementTest, cls).setUpClass()
        cls.env = entities.LifecycleEnvironment(
            organization=cls.session_org).create()
        cls.content_view = entities.ContentView(
            organization=cls.session_org).create()
        cls.activation_key = entities.ActivationKey(
            environment=cls.env,
            organization=cls.session_org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })
        setup_org_for_a_custom_repo({
            'url': FAKE_6_YUM_REPO,
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })

    def setUp(self):
        """Create VMs, subscribe them to satellite-tools repo, install
        katello-ca and katello-agent packages, then create Host collection,
        associate it with previously created hosts.
        """
        super(HostCollectionPackageManagementTest, self).setUp()
        self.hosts = []
        for _ in range(self.hosts_number):
            client = VirtualMachine(distro=DISTRO_RHEL7)
            self.addCleanup(vm_cleanup, client)
            self.hosts.append(client)
            client.create()
            client.install_katello_ca()
            client.register_contenthost(
                self.session_org.label, self.activation_key.name)
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
        host_ids = [
            entities.Host().search(query={
                'search': 'name={0}'.format(host.hostname)})[0].id
            for host in self.hosts
        ]
        self.host_collection = entities.HostCollection(
            host=host_ids,
            organization=self.session_org,
        ).create()

    def _validate_package_installed(self, hosts, package_name,
                                    expected_installed=True, timeout=120):
        """Check whether package was installed on the list of hosts."""

        for host in hosts:
            for _ in range(timeout / 15):
                result = self.contenthost.package_search(
                    host.hostname, package_name)
                if (result is not None and expected_installed or
                        result is None and not expected_installed):
                    break
                sleep(15)
            else:
                self.fail(
                    u'Package {0} was not {1} host {2}'.format(
                        package_name,
                        'installed on ' if expected_installed else
                        'removed from ',
                        host.hostname,
                    )
                )

    @tier3
    def test_positive_install_package(self):
        """Install a package to hosts inside host collection remotely

        :id: eead8392-0ffc-4062-b045-5d0252670775

        :expectedresults: Package was successfully installed on all the hosts
            in host collection

        :CaseLevel: System
        """
        with Session(self.browser):
            self.hostcollection.execute_bulk_package_action(
                self.host_collection.name,
                'install',
                'package',
                FAKE_0_CUSTOM_PACKAGE_NAME,
            )
            self._validate_package_installed(
                self.hosts, FAKE_0_CUSTOM_PACKAGE_NAME)

    @tier3
    def test_positive_remove_package(self):
        """Remove a package from hosts inside host collection remotely

        :id: 488fa88d-d0ef-4108-a050-96fb621383df

        :expectedresults: Package was successfully removed from all the hosts
            in host collection

        :CaseLevel: System
        """
        for client in self.hosts:
            client.download_install_rpm(
                FAKE_6_YUM_REPO,
                FAKE_0_CUSTOM_PACKAGE
            )
        with Session(self.browser):
            self.hostcollection.execute_bulk_package_action(
                self.host_collection.name,
                'remove',
                'package',
                FAKE_0_CUSTOM_PACKAGE_NAME,
            )
            self._validate_package_installed(
                self.hosts,
                FAKE_0_CUSTOM_PACKAGE_NAME,
                expected_installed=False,
            )

    @tier3
    def test_positive_upgrade_package(self):
        """Upgrade a package on hosts inside host collection remotely

        :id: 5a6fff0a-686f-419b-a773-4d03713e47e9

        :expectedresults: Package was successfully upgraded on all the hosts in
            host collection

        :CaseLevel: System
        """
        for client in self.hosts:
            client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with Session(self.browser):
            self.hostcollection.execute_bulk_package_action(
                self.host_collection.name,
                'update',
                'package',
                FAKE_1_CUSTOM_PACKAGE_NAME,
            )
            self._validate_package_installed(self.hosts, FAKE_2_CUSTOM_PACKAGE)

    @tier3
    def test_positive_install_package_group(self):
        """Install a package group to hosts inside host collection remotely

        :id: 2bf47798-d30d-451a-8de5-bc03bd8b9a48

        :expectedresults: Package group was successfully installed on all the
            hosts in host collection

        :CaseLevel: System
        """
        with Session(self.browser):
            self.hostcollection.execute_bulk_package_action(
                self.host_collection.name,
                'install',
                'package_group',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
                self._validate_package_installed(self.hosts, package)

    @tier3
    def test_positive_remove_package_group(self):
        """Remove a package group from hosts inside host collection remotely

        :id: 458897dc-9836-481a-b777-b147d64836f2

        :expectedresults: Package group was successfully removed  on all the
            hosts in host collection

        :CaseLevel: System
        """
        with Session(self.browser):
            self.hostcollection.execute_bulk_package_action(
                self.host_collection.name,
                'install',
                'package_group',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
                self._validate_package_installed(self.hosts, package)
            self.hostcollection.execute_bulk_package_action(
                self.host_collection.name,
                'remove',
                'package_group',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
                self._validate_package_installed(
                    self.hosts, package, expected_installed=False)

    @tier3
    def test_positive_install_errata(self):
        """Install an errata to the hosts inside host collection remotely

        :id: 69c83000-0b46-4735-8c03-e9e0b48af0fb

        :expectedresults: Errata was successfully installed in all the hosts in
            host collection

        :CaseLevel: System
        """
        for client in self.hosts:
            client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with Session(self.browser):
            result = self.hostcollection.execute_bulk_errata_installation(
                self.host_collection.name,
                FAKE_2_ERRATA_ID,
            )
            self.assertEqual(result, 'success')
            self._validate_package_installed(self.hosts, FAKE_2_CUSTOM_PACKAGE)
