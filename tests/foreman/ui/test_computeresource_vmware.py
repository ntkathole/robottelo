"""Test for compute resource UI

:Requirement: Computeresource

:CaseComponent: UI

:CaseLevel: Acceptance

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_resource
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class VmwareComputeResourceTestCase(UITestCase):
    """Implement vmware compute resource tests in UI"""

    @classmethod
    @skip_if_not_set('vmware')
    def setUpClass(cls):
        super(VmwareComputeResourceTestCase, cls).setUpClass()
        cls.vmware_url = settings.vmware.vcenter
        cls.vmware_password = settings.vmware.password
        cls.vmware_username = settings.vmware.username
        cls.vmware_datacenter = settings.vmware.datacenter
        cls.vmware_img_name = settings.vmware.image_name
        cls.vmware_img_arch = settings.vmware.image_arch
        cls.vmware_img_os = settings.vmware.image_os
        cls.vmware_img_user = settings.vmware.image_username
        cls.vmware_img_pass = settings.vmware.image_password
        cls.vmware_vm_name = settings.vmware.vm_name

    @run_only_on('sat')
    @tier1
    def test_positive_create_vmware_with_name(self):
        """Create a new vmware compute resource using valid name.

        :id: 944ed0da-49d4-4c14-8884-9184d2aef126

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide a valid hostname, username and password.
            3. Provide a valid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.

        :expectedresults: A vmware compute resource is created successfully.

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_vmware_with_description(self):
        """Create vmware compute resource with valid description.

        :id: bdd879be-3467-41ca-9a67-d98f185ba892

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide a valid hostname, username and password.
            3. Provide a valid description to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.

        :expectedresults: A vmware compute resource is created successfully

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            for description in valid_data_list():
                with self.subTest(description):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(self.compute_resource.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_vmware_with_invalid_name(self):
        """Create a new vmware compute resource with invalid names.

        :id: 19c206dc-5efc-4a7d-b04d-2aa04a22448c

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Provide invalid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.

        :expectedresults: A vmware compute resource is not created

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        with Session(self.browser) as session:
            for name in invalid_names_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                    self.assertIsNotNone(
                        self.compute_resource.wait_until_element(
                            common_locators["name_haserror"]
                        )
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_update_vmware_name(self):
        """Update a vmware compute resource name

        :id: e2bf2fcb-4611-445e-bc36-a54b3fd2d559

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Provide valid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.
            5. Update the name of the created CR with valid string.

        :expectedresults: The vmware compute resource is updated

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        newname = gen_string('alpha')
        name = gen_string('alpha')
        with Session(self.browser) as session:
            with self.subTest(newname):
                make_resource(
                    session,
                    name=name,
                    provider_type=FOREMAN_PROVIDERS['vmware'],
                    parameter_list=parameter_list
                )
                self.assertIsNotNone(self.compute_resource.search(name))
                self.compute_resource.update(name=name, newname=newname)
                self.assertIsNotNone(self.compute_resource.search(newname))

    @run_only_on('sat')
    @tier2
    def test_positive_update_vmware_organization(self):
        """Update a vmware compute resource organization

        :id: b7ffc933-9ffb-4bcd-ab23-33fde67f27e4

        :setup: vmware hostname and credentials.

        :steps:
            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Provide valid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.
            5. Create a new organization.
            6. Add the CR to new organization.

        :expectedresults: The vmware compute resource is updated

        :Caseautomation: notautomated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list,
                orgs=[entities.Organization().create().name],
                org_select=True
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            self.compute_resource.update(
                name=name,
                orgs=[entities.Organization().create().name],
                org_select=True
            )

    @run_only_on('sat')
    @tier1
    def test_positive_delete_vmware(self):
        """Delete a vmware compute resource

        :id: b38f2c9b-f4e3-41e3-8ee1-3b342025860c

        :setup: vmware hostname and credentials.

        :steps:
            1. Create compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Provide valid name to vmware compute resource.
            4. Test the connection using Load Datacenters and submit.
            5. Delete the created compute resource.

        :expectedresults: The compute resource is deleted

        :Caseautomation: notautomated

        :CaseImportance: Critical
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            with self.subTest(name):
                make_resource(
                    session,
                    name=name,
                    provider_type=FOREMAN_PROVIDERS['vmware'],
                    parameter_list=parameter_list
                )
                self.assertIsNotNone(self.compute_resource.search(name))
                self.compute_resource.delete(name, dropdown_present=True)

    @run_only_on('sat')
    @tier2
    def test_positive_add_image_vmware_with_name(self):
        """Add images to the vmware compute resource

        :id: 4b749529-b98d-4a3e-a2d1-b9738c96c283

        :setup:
            1. Valid vmware hostname, credentials.
            2. Add images as templates in vmware.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR and click images tab.
            4. Select "New image", provide valid name and information.
            5. Select the desired template to create image and submit.

        :expectedresults: The image is added to the CR successfully

        :Caseautomation: notautomated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            for img_name in valid_data_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                parameter_list_img = [
                    ['Name', img_name],
                    ['Operatingsystem', self.vmware_img_os],
                    ['Architecture', self.vmware_img_arch],
                    ['Username', self.vmware_img_user],
                    ['Password', self.vmware_img_pass],
                    ['uuid', self.vmware_img_name],
                ]
                self.compute_resource.add_image(name, parameter_list_img)
                self.assertIsNotNone(self.compute_resource.search(name))
                imgs = self.compute_resource.list_images(name)
                self.assertIn(img_name, imgs)

    @run_only_on('sat')
    @tier2
    def test_negative_add_image_vmware_with_invalid_name(self):
        """Add images to the vmware compute resource

        :id: 436324bf-7dcf-4197-b1ca-198492bf0356

        :setup:

            1. Valid vmware hostname, credentials.
            2. Add images as templates in vmware.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR and click images tab.
            4. Select "New image" , provide invalid name and valid information.
            5. Select the desired template to create the image from and submit.

        :expectedresults: The image should not be added to the CR

        :Caseautomation: notautomated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            for img_name in invalid_names_list():
                with self.subTest(name):
                    make_resource(
                        session,
                        name=name,
                        provider_type=FOREMAN_PROVIDERS['vmware'],
                        parameter_list=parameter_list
                    )
                parameter_list_img = [
                    ['Name', img_name],
                    ['Operatingsystem', self.vmware_img_os],
                    ['Architecture', self.vmware_img_arch],
                    ['Username', self.vmware_img_user],
                    ['Password', self.vmware_img_pass],
                    ['uuid', self.vmware_img_name],
                ]
                self.compute_resource.add_image(name, parameter_list_img)
                self.assertIsNotNone(
                    self.compute_resource.wait_until_element(
                        common_locators["name_haserror"]
                    ))

    @run_only_on('sat')
    @tier2
    def test_positive_access_vmware_with_default_profile(self):
        """Associate default (3-Large) compute profile

        :id: ceb2ef14-fa96-4951-9198-768ffcc4d01f

        :setup: vmware hostname and credentials.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR.
            4. Click Compute Profile tab.
            5. Select (3-Large) and submit.

        :expectedresults: The Compute Resource created and opened successfully

        :Caseautomation: notautomated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_profile.select_resource(
                '3-Large', name, 'VMware'))

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_access_vmware_with_custom_profile(self):
        """Associate custom default (3-Large) compute profile

        :id: 751ef765-5091-4322-a0d9-0c9c73009cc4

        :setup: vmware hostname and credentials.

        :steps:

            1. Create a compute resource of type vmware.
            2. Provide valid hostname, username and password.
            3. Select the created vmware CR.
            4. Click Compute Profile tab.
            5. Edit (3-Large) with valid configurations and submit.

        :expectedresults: The Compute Resource created and opened successfully

        :Caseautomation: notautomated

        :CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_retrieve_vmware_vm_list(self):
        """List the virtual machine list from vmware compute resource

        :id: 21ade57a-0caa-4144-9c46-c8e22f33414e

        :setup: vmware hostname and credentials.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.

        :expectedresults: The Virtual machines should be displayed

        :Caseautomation: notautomated

        :CaseLevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            self.assertIsNotNone(self.compute_resource.search(name))
            vms = self.compute_resource.list_vms(name)
            self.assertIn(self.vmware_vm_name, vms)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_vmware_with_image(self):
        """ Provision a host on vmware compute resource with image based

        :id: 2cbddac9-c5fa-4f6e-a098-d3e47a3aeb3c

        :setup: vmware hostname and credentials.

            1. Configured subnet for provisioning of the host.
            2. Configured domains for the host.
            3. Population of images into satellite from vmware templates.
            4. Activation key and CV for the host.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill the required details.(eg name,loc, org).
            3. Select vmware compute resource from "Deploy on" drop down.
            4. Associate appropriate feature capsules.
            5. Go to "operating system tab".
            6. Edit Provisioning Method to image based.
            7. Select the appropriate image .
            8. Associate the activation key and submit.

        :expectedresults: The host should be provisioned successfully

        :Caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_vmware_with_compute_profile(self):
        """ Provision a host on vmware compute resource with compute profile
        default (3-Large)

        :id: cfe68708-f062-425e-bed7-a46e04007b11

        :setup:

            1. Vaild vmware hostname ,credentials.
            2. Configure provisioning setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill the required details.(eg name,loc, org).
            3. Select vmware compute resource from "Deploy on" drop down.
            4. Select the "Compute profile" from the drop down.
            5. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned successfully

        :Caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_vmware_with_custom_compute_settings(self):
        """ Provision a host on vmware compute resource with
        custom disk, cpu count and memory

        :id: d82c2b81-3a24-4d6e-82eb-c35709861a44

        :setup:

            1. Vaild vmware hostname ,credentials.
            2. Configure provisioning setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Fill the required details.(eg name,loc, org).
            3. Select vmware custom compute resource from "Deploy on" drop
               down.
            4. Select the custom compute profile" with custom disk size, cpu
               count and memory.
            5. Provision the host using the compute profile.

        :expectedresults: The host should be provisioned with custom settings

        :Caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_vmware_with_host_group(self):
        """ Provision a host on vmware compute resource with
        the help of hostgroup.

        :id: d4e442ad-77f1-4d5e-9d1b-9a60d69b034f

        :setup:

            1. Vaild vmware hostname ,credentials.
            2. Configure provisioning setup.
            3. Configure host group setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Assign the host group to the host.
            3. Select the Deploy on as vmware Compute Resource.
            4. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :Caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier2
    def test_positive_poweroff_vmware_vms(self):
        """Poweroff the vmware virtual machine

        :id: cc5e1957-ebd6-4621-9451-99607da76aeb

        :setup:

            1. Valid vmware hostname, credentials.
            2. Virtual machine in vmware.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.
            3. Click "Poweroff" button associated with the vm.

        :expectedresults: The Virtual machine should be switched off

        :Caseautomation: notautomated

        :Caselevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            self.assertEqual(self.compute_resource.set_power_status(
                name, self.vmware_vm_name, False), u'Off')

    @run_only_on('sat')
    @tier2
    def test_positive_poweron_vmware_vms(self):
        """Power on the vmware virtual machine

        :id: 846318e9-8b95-46ea-b7bc-26689064f80c

        :setup:

            1. Valid vmware hostname, credentials.
            2. Virtual machine in vmware.

        :steps:

            1. Select the created compute resource.
            2. Go to "Virtual Machines" tab.
            3. Click "Power on" button associated with the vm.

        :expectedresults: The Virtual machine should be switched on

        :Caseautomation: notautomated

        :Caselevel: Integration
        """
        parameter_list = [
            ['VCenter/Server', self.vmware_url, 'field'],
            ['Username', self.vmware_username, 'field'],
            ['Password', self.vmware_password, 'field'],
            ['Datacenter', self.vmware_datacenter, 'special select'],
        ]
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=name,
                provider_type=FOREMAN_PROVIDERS['vmware'],
                parameter_list=parameter_list
            )
            self.assertEqual(self.compute_resource.set_power_status(
                name, self.vmware_vm_name, True), u'On')
