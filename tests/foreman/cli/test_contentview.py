"""Test class for Content Views

:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

from fauxfactory import gen_alphanumeric, gen_string
from robottelo import manifests, ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    make_content_view,
    make_content_view_filter,
    make_content_view_filter_rule,
    make_filter,
    make_fake_host,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
    make_role,
    make_user,
)
from robottelo.cli.filter import Filter
from robottelo.cli.host import Host
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.role import Role
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.constants import (
    CUSTOM_PUPPET_REPO,
    DEFAULT_CV,
    DEFAULT_ROLE,
    DISTRO_RHEL7,
    DOCKER_REGISTRY_HUB,
    DOCKER_UPSTREAM_NAME,
    ENVIRONMENT,
    FAKE_0_PUPPET_REPO,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_1_YUM_REPO,
    FEDORA23_OSTREE_REPO,
    PERMISSIONS,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.decorators.host import skip_if_os
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


class ContentViewTestCase(CLITestCase):
    """Content View CLI tests"""

    org = None
    product = None
    env1 = None
    env2 = None
    rhel_content_org = None
    rhel_repo_name = None
    rhel_repo = None

    def create_rhel_content(self):
        """Enable/Synchronize rhel content"""
        if ContentViewTestCase.rhel_content_org is not None:
            return

        try:
            ContentViewTestCase.rhel_content_org = make_org()
            with manifests.clone() as manifest:
                upload_file(manifest.content, manifest.filename)
            Subscription.upload({
                'file': manifest.filename,
                'organization-id': ContentViewTestCase.rhel_content_org['id'],
            })

            RepositorySet.enable({
                'name': REPOSET['rhva6'],
                'organization-id': ContentViewTestCase.rhel_content_org['id'],
                'product': PRDS['rhel'],
                'releasever': '6Server',
                'basearch': 'x86_64',
            })
            ContentViewTestCase.rhel_repo_name = REPOS['rhva6']['name']

            ContentViewTestCase.rhel_repo = Repository.info({
                u'name': ContentViewTestCase.rhel_repo_name,
                u'organization-id': self.rhel_content_org['id'],
                u'product': PRDS['rhel'],
            })

            Repository.synchronize({
                'name': ContentViewTestCase.rhel_repo_name,
                'organization-id': ContentViewTestCase.rhel_content_org['id'],
                'product': PRDS['rhel'],
            })
        except CLIReturnCodeError:
            # Make sure to reset rhel_content_org and let the exception
            # propagate.
            ContentViewTestCase.rhel_content_org = None
            raise

    @staticmethod
    def _get_content_view_version_lce_names_set(content_view_id, version_id):
        """returns a set of content view version lifecycle environment names

        :rtype: set
        """
        lifecycle_environments = ContentView.version_info({
            'content-view-id': content_view_id,
            'id': version_id
        })['lifecycle-environments']
        return {lce['name'] for lce in lifecycle_environments}

    # pylint: disable=unexpected-keyword-arg
    def setUp(self):
        """Tests for content-view via Hammer CLI"""

        super(ContentViewTestCase, self).setUp()

        if ContentViewTestCase.org is None:
            ContentViewTestCase.org = make_org(cached=True)
        if ContentViewTestCase.env1 is None:
            ContentViewTestCase.env1 = make_lifecycle_environment(
                {u'organization-id': ContentViewTestCase.org['id']})
        if ContentViewTestCase.env2 is None:
            ContentViewTestCase.env2 = make_lifecycle_environment(
                {u'organization-id': ContentViewTestCase.org['id'],
                 u'prior': ContentViewTestCase.env1['label']})
        if ContentViewTestCase.product is None:
            ContentViewTestCase.product = make_product(
                {u'organization-id': ContentViewTestCase.org['id']},
                cached=True)

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """create content views with different names

        :id: a154308c-3982-4cf1-a236-3051e740970e

        :expectedresults: content views are created


        :CaseImportance: Critical
        """
        for name in generate_strings_list(exclude_types=['cjk']):
            with self.subTest(name):
                content_view = make_content_view({
                    'name': name,
                    'organization-id': make_org(cached=True)['id'],
                })
                self.assertEqual(content_view['name'], name)

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    def test_negative_create_with_invalid_name(self):
        """create content views with invalid names

        :id: 83046271-76f9-4cda-b579-a2fe63493295

        :expectedresults: content views are not created; proper error thrown
            and system handles it gracefully


        :CaseImportance: Critical
        """
        org_id = make_org(cached=True)['id']
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_content_view({
                        'name': name,
                        'organization-id': org_id,
                    })

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_org_name(self):
        # Use an invalid org name
        """Create content view with invalid org name

        :id: f8b76e98-ccc8-41ac-af04-541650e8f5ba

        :expectedresults: content views are not created; proper error thrown
            and system handles it gracefully


        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.create({'organization-id': gen_string('alpha')})

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_repo_id(self):
        """Create content view providing repository id

        :id: bb91affe-f8d4-4724-8b61-41f3cb898fd3

        :expectedresults: Content view is created and repository is associated
            with CV

        :BZ: 1213097
        """
        repo = make_repository({'product-id': self.product['id']})
        cv = make_content_view({
            'organization-id': self.org['id'],
            'repository-ids': [repo['id']],
        })
        self.assertEqual(cv['yum-repositories'][0]['id'], repo['id'])

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_repo_name(self):
        """Create content view providing repository name

        :id: 80992a94-4c8e-4dbe-bc62-25af0bd2301d

        :expectedresults: Content view is created and repository is associated
            with CV

        :BZ: 1213097
        """
        repo = make_repository({'product-id': self.product['id']})
        cv = make_content_view({
            'organization-id': self.org['id'],
            'product': self.product['name'],
            'repositories': [repo['name']],
        })
        self.assertEqual(cv['yum-repositories'][0]['name'], repo['name'])

    @tier1
    def test_positive_create_empty_and_verify_files(self):
        """Create an empty content view and make sure no files are created at
        /var/lib/pulp/published.

        :id: 0e31573d-bf02-44ae-b3f4-d8aae450ba5e

        :expectedresults: Content view is published and no file is present at
            /var/lib/pulp/published.

        :CaseImportance: Critical
        """
        content_view = make_content_view({'organization-id': self.org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        # Check content view files presence before deletion
        result = ssh.command(
            'find /var/lib/pulp/published -name "*{0}*"'
            .format(content_view['name'])
        )
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout), 0)
        self.assertEqual(len(content_view['versions']), 1)

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_update_name(self):
        """Update content view name

        :id: 35fccf2c-abc4-4ca8-a565-a7a6adaaf429

        :expectedresults: Content view is updated with new name

        :BZ: 1359665

        :CaseImportance: Critical
        """
        con_view = make_content_view({
            'name': gen_string('utf8'),
            'organization-id': make_org(cached=True)['id'],
        })
        new_name = gen_string('utf8')
        ContentView.update({
            'id': con_view['id'],
            'name': new_name,
        })
        con_view = ContentView.info({'id': con_view['id']})
        self.assertEqual(con_view['name'], new_name)

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_update_filter(self):
        # Variations might be:
        # * A filter on errata date (only content that matches date
        # in filter)
        # * A filter on severity (only content of specific errata
        # severity.
        """Edit content views for a rh content

        :id: 4beab1e4-fc58-460e-af24-cdd2c3d283e6

        :expectedresults: Edited content view save is successful and info is
            updated

        :CaseLevel: Integration
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            'organization-id': self.rhel_content_org['id']
        })
        # Associate repo to CV
        ContentView.add_repository({
            'id': new_cv['id'],
            'organization-id': ContentViewTestCase.rhel_content_org['id'],
            'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        new_cv = ContentView.info({'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            ContentViewTestCase.rhel_repo_name,
        )
        cvf = make_content_view_filter({
            'content-view-id': new_cv['id'],
            'inclusion': 'true',
            'type': 'erratum',
        })
        cvf_rule = make_content_view_filter_rule({
            'content-view-filter-id': cvf['filter-id'],
            'types': ['bugfix', 'enhancement'],
        })
        cvf = ContentView.filter.info({'id': cvf['filter-id']})
        self.assertNotIn('security', cvf['rules'][0]['types'])
        ContentView.filter.rule.update({
            'id': cvf_rule['rule-id'],
            'types': 'security',
            'content-view-filter-id': cvf['filter-id'],
        })
        cvf = ContentView.filter.info({'id': cvf['filter-id']})
        self.assertEqual('security', cvf['rules'][0]['types'])

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_id(self):
        """delete content views

        :id: e96d6d47-8be4-4705-979f-e5c320eca293

        :expectedresults: content view can be deleted


        :CaseImportance: Critical
        """
        con_view = make_content_view({
            'organization-id': make_org(cached=True)['id'],
        })
        ContentView.delete({'id': con_view['id']})
        with self.assertRaises(CLIReturnCodeError):
            ContentView.info({'id': con_view['id']})

    @tier1
    @skip_if_bug_open('bugzilla', 1317057)
    def test_positive_delete_with_custom_repo_by_name_and_verify_files(self):
        """Delete content view containing custom repo and verify it was
        actually deleted from hard drive.

        :id: 9f381f77-ce43-4b68-8d00-459f40c9efb6

        :expectedresults: Content view was deleted and pulp folder doesn't
            contain content view files anymore

        :BZ: 1317057, 1265703

        :CaseImportance: Critical
        """
        # Create and sync a repository
        new_product = make_product({u'organization-id': self.org['id']})
        new_repo = make_repository({u'product-id': new_product['id']})
        Repository.synchronize({'id': new_repo['id']})
        # Create a content view, add the repo and publish the content view
        content_view = make_content_view({'organization-id': self.org['id']})
        ContentView.add_repository({
            u'id': content_view['id'],
            u'organization-id': self.org['id'],
            u'repository-id': new_repo['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        # Check content view files presence before deletion
        result = ssh.command(
            'find /var/lib/pulp -name "*{0}*"'.format(content_view['name']))
        self.assertEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stdout), 0)
        self.assertEqual(len(content_view['versions']), 1)
        # Completely delete the content view
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'lifecycle-environment-id':
                content_view['lifecycle-environments'][0]['id'],
        })
        ContentView.version_delete({
            'content-view': content_view['name'],
            'organization': self.org['name'],
            'version': content_view['versions'][0]['version'],
        })
        ContentView.delete({'id': content_view['id']})
        # Check content view files presence after deletion
        result = ssh.command(
            'find /var/lib/pulp -name "*{0}*"'.format(content_view['name']))
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_delete_version_by_name(self):
        """Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'remove-from-environment' command and delete content view version from
        that content view. Use content view version name as a parameter.

        :id: 6e903131-1aeb-478c-ad92-5dedcc22c3f9

        :expectedresults: Content view version deleted successfully


        :CaseLevel: Integration
        """
        content_view = make_content_view({u'organization-id': self.org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 1)
        cvv = content_view['versions'][0]
        env_id = content_view['lifecycle-environments'][0]['id']
        ContentView.remove_from_environment({
            u'id': content_view['id'],
            u'lifecycle-environment-id': env_id,
        })
        ContentView.version_delete({
            u'content-view': content_view['name'],
            u'organization': self.org['name'],
            u'version': cvv['version'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 0)

    @tier1
    @run_only_on('sat')
    def test_positive_delete_version_by_id(self):
        """Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'remove-from-environment' command and delete content view version from
        that content view. Use content view version id as a parameter. Also,
        add repository to initial content view for better coverage.

        :id: 09457d48-2a92-401d-8dd0-45679a547e70

        :expectedresults: Content view version deleted successfully


        :CaseImportance: Critical
        """
        # Create new organization, product and repository
        new_org = make_org({u'name': gen_alphanumeric()})
        new_product = make_product({u'organization-id': new_org['id']})
        new_repo = make_repository({u'product-id': new_product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create new content-view and add repository to view
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': new_org['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a version1 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Get the CV info
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['versions']), 1)
        # Store the associated environment_id
        env_id = new_cv['lifecycle-environments'][0]['id']
        # Store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Remove the CV from selected environment
        ContentView.remove_from_environment({
            u'id': new_cv['id'],
            u'lifecycle-environment-id': env_id,
        })
        # Delete the version
        ContentView.version_delete({u'id': version1_id})
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['versions']), 0)

    @tier2
    @run_only_on('sat')
    def test_negative_delete_version_by_id(self):
        """Create content view and publish it. Try to delete content
        view version while content view is still associated with lifecycle
        environment

        :id: 7334118b-e6c5-4db3-9167-3f006c43f863

        :expectedresults: Content view version is not deleted


        :CaseLevel: Integration
        """
        content_view = make_content_view({u'organization-id': self.org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 1)
        cvv = content_view['versions'][0]
        # Try to delete content view version while it is in environment Library
        with self.assertRaises(CLIReturnCodeError):
            ContentView.version_delete({u'id': cvv['id']})
        # Check that version was not actually removed from the cv
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 1)

    @tier1
    @run_only_on('sat')
    def test_positive_remove_lce_by_id(self):
        """Remove content view from lifecycle environment

        :id: 1bf8a647-d82e-4145-b13b-f92bf6642532

        :expectedresults: Content view removed from environment successfully


        :CaseImportance: Critical
        """
        new_org = make_org({u'name': gen_alphanumeric()})
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        env = new_cv['lifecycle-environments'][0]
        ContentView.remove({
            u'id': new_cv['id'],
            u'environment-ids': env['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['lifecycle-environments']), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_remove_lce_by_id_and_reassign_ak(self):
        """Remove content view environment and re-assign activation key to
        another environment and content view

        :id: 3e3ac439-fa85-42ce-8277-2258bc0c7cb4

        :expectedresults: Activation key re-assigned successfully


        :CaseLevel: Integration
        """
        new_org = make_org({u'name': gen_alphanumeric()})
        env = [
            make_lifecycle_environment({u'organization-id': new_org['id']})
            for _ in range(2)
        ]

        source_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': source_cv['id']})
        source_cv = ContentView.info({u'id': source_cv['id']})
        cvv = source_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[0]['id'],
        })

        destination_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': destination_cv['id']})
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        cvv = destination_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[1]['id'],
        })

        ac_key = make_activation_key({
            u'content-view-id': source_cv['id'],
            u'lifecycle-environment-id': env[0]['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(source_cv['activation-keys'][0], ac_key['name'])
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(len(destination_cv['activation-keys']), 0)

        ContentView.remove({
            u'id': source_cv['id'],
            u'environment-ids': env[0]['id'],
            u'key-content-view-id': destination_cv['id'],
            u'key-environment-id': env[1]['id'],
        })
        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(len(source_cv['activation-keys']), 0)
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(destination_cv['activation-keys'][0], ac_key['name'])

    @tier2
    @run_only_on('sat')
    def test_positive_remove_lce_by_id_and_reassign_chost(self):
        """Remove content view environment and re-assign content host to
        another environment and content view

        :id: 40900199-dcfc-4906-bf54-16c13882c05b

        :expectedresults: Content host re-assigned successfully


        :CaseLevel: Integration
        """
        new_org = make_org({u'name': gen_alphanumeric()})
        env = [
            make_lifecycle_environment({u'organization-id': new_org['id']})
            for _ in range(2)
        ]

        source_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': source_cv['id']})
        source_cv = ContentView.info({u'id': source_cv['id']})
        cvv = source_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[0]['id'],
        })

        destination_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': destination_cv['id']})
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        cvv = destination_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[1]['id'],
        })

        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(source_cv['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': source_cv['id'],
            u'lifecycle-environment-id': env[0]['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })

        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(source_cv['content-host-count'], '1')
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(destination_cv['content-host-count'], '0')

        ContentView.remove({
            u'environment-ids': env[0]['id'],
            u'id': source_cv['id'],
            u'system-content-view-id': destination_cv['id'],
            u'system-environment-id': env[1]['id'],
        })
        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(source_cv['content-host-count'], '0')
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(destination_cv['content-host-count'], '1')

    @tier1
    @run_only_on('sat')
    def test_positive_remove_version_by_id(self):
        """Delete content view version using 'remove' command

        :id: e8664353-6601-4566-8478-440be20a089d

        :expectedresults: Content view version deleted successfully


        :CaseImportance: Critical
        """
        new_org = make_org({u'name': gen_alphanumeric()})
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        env = new_cv['lifecycle-environments'][0]
        cvv = new_cv['versions'][0]
        ContentView.remove_from_environment({
            u'id': new_cv['id'],
            u'lifecycle-environment-id': env['id'],
        })

        ContentView.remove({
            u'content-view-version-ids': cvv['id'],
            u'id': new_cv['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['versions']), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_create_composite(self):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case
        # (test_negative_add_puppet_repo). Individual modules from a puppet
        # repo, however, are a valid variation.
        """create a composite content view

        :id: bded6acd-8da3-45ea-9e39-19bdc6c06341

        :setup: sync multiple content source/types (RH, custom, etc.)

        :expectedresults: Composite content views are created


        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Create CV
        con_view = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
        })
        # Associate version to composite CV
        ContentView.add_version({
            u'content-view-version-id': version1_id,
            u'id': con_view['id'],
        })
        # Assert whether version was associated to composite CV
        con_view = ContentView.info({u'id': con_view['id']})
        self.assertEqual(
            con_view['components'][0]['id'],
            version1_id,
            'version was not associated to composite CV',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_remove_version_by_id_from_composite(self):
        """Create a composite content view and remove its content version by id

        :id: 0ff675d0-45d6-4f15-9e84-3b5ce98ce7de

        :expectedresults: Composite content view info output does not contain
            any values

        :CaseLevel: Integration
        """
        # Create new repository
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create new content-view and add repository to view
        new_cv = make_content_view({u'organization-id': self.org['id']})
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': self.org['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        # Get the CV info
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Create a composite CV
        comp_cv = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
            'component-ids': new_cv['versions'][0]['id']
        })
        ContentView.publish({u'id': comp_cv['id']})
        new_cv = ContentView.info({u'id': comp_cv['id']})
        env = new_cv['lifecycle-environments'][0]
        cvv = new_cv['versions'][0]
        ContentView.remove_from_environment({
            u'id': new_cv['id'],
            u'lifecycle-environment-id': env['id'],
        })
        ContentView.remove({
            u'content-view-version-ids': cvv['id'],
            u'id': new_cv['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['versions']), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_create_composite_with_component_ids(self):
        """create a composite content view with a component_ids option

        :id: 6d4b94da-258d-4690-a5b6-bacaf6b1671a

        :expectedresults: Composite content view component ids are similar to
            the nested content view versions ids

        :CaseLevel: Integration
        """
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Publish a new version of CV twice
        for _ in range(2):
            ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version ids
        component_ids = [version['id'] for version in new_cv['versions']]
        # Create CV
        comp_cv = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
            'component-ids': component_ids
        })
        # Assert whether the composite content view components IDs are equal
        # to the component_ids input values
        comp_cv = ContentView.info({u'id': comp_cv['id']})
        self.assertEqual(
            {comp['id'] for comp in comp_cv['components']},
            set(component_ids),
            'IDs of the composite content view components differ from '
            'the input values',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_update_composite_with_component_ids(self):
        """Update a composite content view with a component_ids option

        :id: e6106ff6-c526-40f2-bdc0-ae291f7b267e

        :expectedresults: Composite content view component ids are similar to
            the nested content view versions ids

        :CaseLevel: Integration
        """
        # Create a CV to add to the composite one
        cv = make_content_view({u'organization-id': self.org['id']})
        # Publish a new version of the CV
        ContentView.publish({u'id': cv['id']})
        new_cv = ContentView.info({u'id': cv['id']})
        # Let us now store the version ids
        component_ids = new_cv['versions'][0]['id']
        # Create a composite CV
        comp_cv = make_content_view({
            'composite': True,
            'organization-id': self.org['id']
        })
        # Update a composite content view with a component id version
        ContentView.update({
            'id': comp_cv['id'],
            'component-ids': component_ids,
        })
        # Assert whether the composite content view components IDs are equal
        # to the component_ids input values
        comp_cv = ContentView.info({u'id': comp_cv['id']})
        self.assertEqual(
            comp_cv['components'][0]['id'],
            component_ids,
            'IDs of the composite content view components differ from '
            'the input values',
        )

    # Content Views: Adding products/repos

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_add_rh_repo_by_id(self):
        """Associate Red Hat content to a content view

        :id: b31a85c3-aa56-461b-9e3a-f7754c742573

        :setup: Sync RH content

        :expectedresults: RH Content can be seen in the content view


        :CaseLevel: Integration
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            u'organization-id': self.rhel_content_org['id']
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            self.rhel_repo_name,
            'Repo was not associated to CV',
        )

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    @tier2
    def test_positive_add_rh_repo_by_id_and_create_filter(self):
        """Associate Red Hat content to a content view and create filter

        :id: 7723247a-9367-4367-b251-bd079b79b8a2

        :setup: Sync RH content

        :steps: Assure filter(s) applied to associated content

        :expectedresults: Filtered RH content only is available/can be seen in
            a view


        :CaseLevel: Integration

        :BZ: 1359665
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            u'organization-id': self.rhel_content_org['id']
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            ContentViewTestCase.rhel_repo_name,
            'Repo was not associated to CV',
        )
        name = gen_string('alphanumeric')
        ContentView.filter.create({
            'content-view-id': new_cv['id'],
            'inclusion': 'true',
            'name': name,
            'type': 'rpm',
        })
        ContentView.filter.rule.create({
            'content-view-filter': name,
            'content-view-id': new_cv['id'],
            'name': 'walgrind',
        })

    @tier2
    @run_only_on('sat')
    def test_positive_add_custom_repo_by_id(self):
        """Associate custom content to a Content view

        :id: b813b222-b984-47e0-8d9b-2daa43f9a221

        :setup: Sync custom content

        :expectedresults: Custom content can be seen in a view


        :CaseLevel: Integration
        """
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV',
        )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1343006)
    @tier1
    def test_positive_add_custom_repo_by_name(self):
        """Associate custom content to a content view with name

        :id: 62431e11-bec6-4444-abb0-e3758ba25fd8

        :expectedresults: whether repos are added to cv.


        :CaseImportance: Critical
        """
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': new_cv['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
            u'repository': new_repo['name'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_add_puppet_module(self):
        """Add puppet module to Content View by name

        :id: 81d3305e-c0c2-487b-9fd8-828b3250fe6e

        :expectedresults: Module was added and has latest version.

        :CaseLevel: Integration
        """
        module = {'name': 'versioned', 'version': '3.3.3'}
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': CUSTOM_PUPPET_REPO,
        })
        puppet_module = PuppetModule.list({
            'search': 'name={name} and version={version}'.format(**module)})[0]
        Repository.synchronize({'id': puppet_repository['id']})
        content_view = make_content_view({u'organization-id': self.org['id']})
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'name': puppet_module['name'],
            u'author': puppet_module['author'],
        })
        # Check output of `content-view info` subcommand
        content_view = ContentView.info({'id': content_view['id']})
        self.assertGreater(content_view['puppet-modules'], 0)
        self.assertEqual(
            puppet_module['name'], content_view['puppet-modules'][0]['name'])
        # Check output of `content-view puppet module list` subcommand
        cv_module = ContentView.puppet_module_list(
            {'content-view-id': content_view['id']})
        self.assertGreater(len(cv_module), 0)
        self.assertIn(puppet_module['version'], cv_module[0]['version'])
        self.assertIn('Latest', cv_module[0]['version'])

    @tier2
    @run_only_on('sat')
    def test_positive_add_puppet_module_older_version(self):
        """Add older version of puppet module to Content View by id/uuid

        :id: 39654b3e-963f-4859-81f2-9992b60433c2

        :Steps:

            1. Upload/sync puppet repo with several versions of the same module
            2. Add older version by id/uuid to CV

        :expectedresults: Exact version (and not latest) was added.

        :CaseLevel: Integration

        :BZ: 1240491
        """
        module = {'name': 'versioned', 'version': '2.2.2'}
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': CUSTOM_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_module = PuppetModule.list({
            'search': 'name={name} and version={version}'.format(**module)})[0]
        for identifier_type in ('uuid', 'id'):
            with self.subTest(add_by=identifier_type):
                content_view = make_content_view(
                    {u'organization-id': self.org['id']})
                ContentView.puppet_module_add({
                    u'content-view-id': content_view['id'],
                    identifier_type: puppet_module[identifier_type],
                })
                # Check output of `content-view info` subcommand
                content_view = ContentView.info({'id': content_view['id']})
                self.assertGreater(len(content_view['puppet-modules']), 0)
                self.assertEqual(
                    puppet_module['name'],
                    content_view['puppet-modules'][0]['name']
                )
                # Check output of `content-view puppet module list` subcommand
                cv_module = ContentView.puppet_module_list(
                    {'content-view-id': content_view['id']})
                self.assertGreater(len(cv_module), 0)
                self.assertEqual(cv_module[0]['version'], module['version'])

    @tier2
    @run_only_on('sat')
    def test_positive_remove_puppet_module_by_name(self):
        """Remove puppet module from Content View by name

        :id: b9d161de-d2a1-46e1-922d-5e22826a41e4

        :expectedresults: Module successfully removed and no modules are listed

        :CaseLevel: Integration
        """
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': CUSTOM_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list(
            {u'repository-id': puppet_repository['id']})
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': self.org['id']})
        # Add puppet module
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'name': puppet_module['name'],
            u'author': puppet_module['author'],
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertGreater(len(content_view['puppet-modules']), 0)
        # Remove puppet module
        ContentView.puppet_module_remove({
            u'content-view-id': content_view['id'],
            u'name': puppet_module['name'],
            u'author': puppet_module['author'],
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(len(content_view['puppet-modules']), 0)

    @tier2
    @skip_if_bug_open('bugzilla', 1427260)
    @run_only_on('sat')
    def test_positive_remove_puppet_module_by_id(self):
        """Remove puppet module from Content View by id

        :id: 972a484c-6f38-4015-b20b-6a83d15b6c97

        :expectedresults: Module successfully removed and no modules are listed

        :CaseLevel: Integration

        :BZ: 1427260
        """
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': CUSTOM_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list(
            {u'repository-id': puppet_repository['id']})
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': self.org['id']})
        # Add puppet module
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'id': puppet_module['id']
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertGreater(len(content_view['puppet-modules']), 0)
        # Remove puppet module
        ContentView.puppet_module_remove({
            'content-view-id': content_view['id'],
            'id': content_view['puppet-modules'][0]['id']
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(len(content_view['puppet-modules']), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_remove_puppet_module_by_uuid(self):
        """Remove puppet module from Content View by uuid

        :id: c63339aa-3d74-4a37-aaef-6777e0f6cb35

        :expectedresults: Module successfully removed and no modules are listed

        :CaseLevel: Integration
        """
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': CUSTOM_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list(
            {u'repository-id': puppet_repository['id']})
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': self.org['id']})
        # Add puppet module
        ContentView.puppet_module_add({
            'content-view-id': content_view['id'],
            'uuid': puppet_module['uuid'],
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertGreater(len(content_view['puppet-modules']), 0)
        # Remove puppet module
        ContentView.puppet_module_remove({
            'content-view-id': content_view['id'],
            'uuid': puppet_module['uuid'],
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(len(content_view['puppet-modules']), 0)

    @tier2
    @run_only_on('sat')
    def test_negative_add_puppet_repo(self):
        # Again, individual modules should be ok.
        """attempt to associate puppet repos within a custom content
        view

        :id: 7625c07b-edeb-48ef-85a2-4d1c09874a4b

        :expectedresults: User cannot create a content view that contains
            direct puppet repos.

        :CaseLevel: Integration
        """
        new_repo = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate puppet repo to CV
        with self.assertRaises(CLIReturnCodeError):
            ContentView.add_repository({
                u'id': new_cv['id'],
                u'repository-id': new_repo['id'],
            })

    @tier2
    @run_only_on('sat')
    def test_negative_add_component_in_non_composite_cv(self):
        """attempt to associate components in a non-composite content
        view

        :id: 2a6f150d-e012-47c1-9423-d73f5d620dc9

        :expectedresults: User cannot add components to the view


        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create component CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        # Fetch version id
        cv_version = ContentView.version_list({
            u'content-view-id': new_cv['id']
        })
        # Create non-composite CV
        with self.assertRaises(CLIFactoryError):
            make_content_view({
                u'component-ids': cv_version[0]['id'],
                u'organization-id': self.org['id'],
            })

    @tier2
    @run_only_on('sat')
    def test_negative_add_same_yum_repo_twice(self):
        """attempt to associate the same repo multiple times within a
        content view

        :id: 5fb09b30-5f5b-4473-a62b-8f41045ac2b6

        :expectedresults: User cannot add repos multiple times to the view


        :CaseLevel: Integration
        """
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV',
        )
        repos_length = len(new_cv['yum-repositories'])
        # Re-associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            len(new_cv['yum-repositories']),
            repos_length,
            'No new entry of same repo is expected',
        )

    @tier2
    @run_only_on('sat')
    def test_negative_add_same_puppet_repo_twice(self):
        """attempt to associate duplicate puppet module(s) within a
        content view

        :id: 674cbae2-8493-466d-a2e4-dc11fb5c6b6f

        :expectedresults: User cannot add puppet modules multiple times to the
            content view

        :CaseLevel: Integration
        """
        # see BZ #1222118
        repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        # Sync REPO
        Repository.synchronize({'id': repository['id']})
        repository = Repository.info({'id': repository['id']})
        puppet_modules = int(repository['content-counts']['puppet-modules'])
        # Create CV
        content_view = make_content_view({
            u'organization-id': self.org['id'],
        })
        # Fetch puppet module
        puppet_result = PuppetModule.list({
            u'repository-id': repository['id'],
            u'per-page': False,
        })
        self.assertEqual(len(puppet_result), puppet_modules)
        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add({
                u'author': puppet_module['author'],
                u'content-view-id': content_view['id'],
                u'name': puppet_module['name'],
            })
            # Re-associate same puppet module to CV
            with self.assertRaises(CLIReturnCodeError):
                ContentView.puppet_module_add({
                    u'author': puppet_module['author'],
                    u'content-view-id': content_view['id'],
                    u'name': puppet_module['name'],
                })

    @tier2
    @run_only_on('sat')
    def test_negative_add_unpublished_cv_to_composite(self):
        """Attempt to associate unpublished non-composite content view with
        composite content view.

        :id: acee782f-2792-4c4e-b0c9-87d6b89992ef

        :steps:

            1. Create an empty non-composite content view. Do not publish it.
            2. Create a new composite content view

        :expectedresults: Non-composite content view cannot be added to
            composite content view.

        :CaseLevel: Integration

        :BZ: 1367123
        """
        # Create component CV
        content_view = make_content_view({'organization-id': self.org['id']})
        # Create composite CV
        composite_cv = make_content_view({
            'organization-id': self.org['id'],
            'composite': True,
        })
        # Add unpublished component CV
        with self.assertRaises(CLIReturnCodeError) as context:
            ContentView.add_version({
                'id': composite_cv['id'],
                'content-view-id': content_view['id'],
            })
        self.assertIn(
            'Error: content_view_version not found',
            context.exception.message
        )

    @tier2
    @run_only_on('sat')
    def test_negative_add_non_composite_cv_to_composite(self):
        """Attempt to associate both published and unpublished
        non-composite content views with composite content view.

        :id: 4f6d3308-8083-4fc3-bb4f-5d5e1b886a96

        :steps:

            1. Create an empty non-composite content view. Do not publish it
            2. Create a second non-composite content view. Publish it.
            3. Create a new composite content view.
            4. Add the published non-composite content view to the composite
               content view.

        :expectedresults:

            1. Unpublished non-composite content view cannot be added to
               composite content view
            2. Published non-composite content view is successfully added to
               composite content view.

        :CaseLevel: Integration

        :BZ: 1367123
        """
        # Create published component CV
        published_cv = make_content_view({'organization-id': self.org['id']})
        ContentView.publish({'id': published_cv['id']})
        # Create unpublished component CV
        unpublished_cv = make_content_view({'organization-id': self.org['id']})
        # Create composite CV
        composite_cv = make_content_view({
            'organization-id': self.org['id'],
            'composite': True,
        })
        # Add published CV
        ContentView.add_version({
            'id': composite_cv['id'],
            'content-view-id': published_cv['id']
        })
        published_cv = ContentView.info({'id': published_cv['id']})
        composite_cv = ContentView.info({'id': composite_cv['id']})
        self.assertEqual(
            composite_cv['components'][0]['id'],
            published_cv['versions'][0]['id']
        )
        # Add unpublished CV
        with self.assertRaises(CLIReturnCodeError) as context:
            ContentView.add_version({
                'id': composite_cv['id'],
                'content-view-id': unpublished_cv['id'],
            })
        self.assertIn(
            'Error: content_view_version not found',
            context.exception.message
        )

    # Content View: promotions
    # katello content view promote --label=MyView --env=Dev --org=ACME
    # katello content view promote --view=MyView --env=Staging --org=ACME

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_promote_rh_content(self):
        """attempt to promote a content view containing RH content

        :id: 53b3661b-b40f-466e-a742-bc4b8c1f6cd8

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be promoted


        :CaseLevel: Integration
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': self.rhel_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        env1 = make_lifecycle_environment({
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': new_cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': env1['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        environment = {
            'id': env1['id'],
            'name': env1['name'],
        }
        self.assertIn(environment, new_cv['lifecycle-environments'])

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_promote_rh_and_custom_content(self):
        """attempt to promote a content view containing RH content and
        custom content using filters

        :id: f96e97ef-f73c-4506-855c-2392e06f3a6a

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be promoted

        :CaseLevel: Integration
        """
        # Enable RH repo
        self.create_rhel_content()
        # Create custom repo
        new_repo = make_repository({
            'product-id': make_product({
                'organization-id': self.rhel_content_org['id']})['id']
        })
        # Sync custom repo
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({
            'organization-id': self.rhel_content_org['id'],
        })
        # Associate repos with CV
        ContentView.add_repository({
            'id': new_cv['id'],
            'repository-id': self.rhel_repo['id'],
        })
        ContentView.add_repository({
            'id': new_cv['id'],
            'repository-id': new_repo['id'],
        })
        cvf = make_content_view_filter({
            'content-view-id': new_cv['id'],
            'inclusion': 'false',
            'type': 'rpm',
        })
        make_content_view_filter_rule({
            'content-view-filter-id': cvf['filter-id'],
            'min-version': 5,
            'name': FAKE_1_CUSTOM_PACKAGE_NAME,
        })
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        env1 = make_lifecycle_environment({
            'organization-id': ContentViewTestCase.rhel_content_org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            'id': new_cv['versions'][0]['id'],
            'to-lifecycle-environment-id': env1['id'],
        })
        new_cv = ContentView.info({'id': new_cv['id']})
        environment = {
            'id': env1['id'],
            'name': env1['name'],
        }
        self.assertIn(environment, new_cv['lifecycle-environments'])

    @tier2
    @run_only_on('sat')
    def test_positive_promote_custom_content(self):
        """attempt to promote a content view containing custom content

        :id: 64c2f1c2-7443-4836-a108-060b913ad2b1

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Content view can be promoted


        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': new_cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertIn(
            {u'id': self.env1['id'], u'name': self.env1['name']},
            new_cv['lifecycle-environments'],
        )

    @tier2
    @run_only_on('sat')
    def test_positive_promote_ccv(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to promote a content view containing custom content

        :id: 9d31113d-39ec-4524-854c-7f03b0f028fe

        :setup: Multiple environments for an org; custom content synced

        :steps: create a composite view containing multiple content types

        :expectedresults: Content view can be promoted


        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Create CV
        con_view = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
        })
        # Associate version to composite CV
        ContentView.add_version({
            u'content-view-version-id': version1_id,
            u'id': con_view['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': con_view['id']})
        # As version info is populated after publishing only
        con_view = ContentView.info({u'id': con_view['id']})
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': con_view['versions'][0]['id'],
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        con_view = ContentView.info({u'id': con_view['id']})
        self.assertIn(
            {u'id': self.env1['id'], u'name': self.env1['name']},
            con_view['lifecycle-environments'],
        )

    @tier2
    @run_only_on('sat')
    def test_negative_promote_default_cv(self):
        """attempt to promote a default content view

        :id: ef25a4d9-8852-4d2c-8355-e9b07eb0560b

        :expectedresults: Default content views cannot be promoted


        :CaseLevel: Integration
        """
        result = ContentView.list(
            {u'organization-id': self.org['id']},
            per_page=False,
        )
        content_view = random.choice([
            cv for cv in result
            if cv['name'] == DEFAULT_CV
        ])
        cvv = ContentView.version_list({
            'content-view-id': content_view['content-view-id']})[0]
        # Promote the Default CV to the next env
        with self.assertRaises(CLIReturnCodeError):
            ContentView.version_promote({
                u'id': cvv['id'],
                u'to-lifecycle-environment-id': self.env1['id'],
            })

    @tier2
    @run_only_on('sat')
    def test_negative_promote_with_invalid_lce(self):
        """attempt to promote a content view using an invalid
        environment

        :id: b143552e-610e-4188-b754-e7462ced8cf3

        :expectedresults: Content views cannot be promoted; handled gracefully


        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Promote the Published version of CV,
        # to the previous env which is Library
        with self.assertRaises(CLIReturnCodeError):
            ContentView.version_promote({
                u'id': new_cv['versions'][0]['id'],
                u'to-lifecycle-environment-id': new_cv[
                    'lifecycle-environments'][0]['id'],
            })

    # Content Views: publish
    # katello content definition publish --label=MyView

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_publish_rh_content(self):
        """attempt to publish a content view containing RH content

        :id: d4323759-d869-4d62-ab2e-f1ea3dbb38ba

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be published


        :CaseLevel: Integration
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            self.rhel_repo['name'],
            'Repo was not associated to CV',
        )
        self.assertEqual(
            new_cv['versions'][0]['version'], u'1.0',
            'Publishing new version of CV was not successful'
        )

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_publish_rh_and_custom_content(self):
        """attempt to publish  a content view containing a RH and custom
        repos and has filters

        :id: 0b116172-06a3-4327-81a8-17a098a1a564

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be published

        :CaseLevel: Integration
        """
        # Enable RH repo
        self.create_rhel_content()
        # Create custom repo
        new_repo = make_repository({
            'product-id': make_product({
                'organization-id': self.rhel_content_org['id']})['id']
        })
        # Sync custom repo
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({
            'organization-id': self.rhel_content_org['id'],
        })
        # Associate repos with CV
        ContentView.add_repository({
            'id': new_cv['id'],
            'repository-id': self.rhel_repo['id'],
        })
        ContentView.add_repository({
            'id': new_cv['id'],
            'repository-id': new_repo['id'],
        })
        cvf = make_content_view_filter({
            'content-view-id': new_cv['id'],
            'inclusion': 'false',
            'type': 'rpm',
        })
        make_content_view_filter_rule({
            'content-view-filter-id': cvf['filter-id'],
            'min-version': 5,
            'name': FAKE_1_CUSTOM_PACKAGE_NAME,
        })
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        self.assertTrue(
            {self.rhel_repo['name'], new_repo['name']}.issubset(
                {repo['name'] for repo in new_cv['yum-repositories']})
        )
        self.assertEqual(new_cv['versions'][0]['version'], '1.0')

    @tier2
    @run_only_on('sat')
    def test_positive_publish_custom_content(self):
        """attempt to publish a content view containing custom content

        :id: 84158023-3980-45c6-87d8-faacea3c942f

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Content view can be published


        :CaseLevel: Integration
        """
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV',
        )
        self.assertEqual(
            new_cv['versions'][0]['version'],
            u'1.0',
            'Publishing new version of CV was not successful',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_publish_ccv(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to publish a composite content view containing custom
        content

        :id: fde99446-241f-422d-987b-fa1987b654ee

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Content view can be published


        :CaseLevel: Integration
        """
        repository = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': repository['id']})
        # Create CV
        content_view = make_content_view({
            u'organization-id': self.org['id'],
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': content_view['id'],
            u'repository-id': repository['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        # Let us now store the version1 id
        version1_id = content_view['versions'][0]['id']
        # Create composite CV
        composite_cv = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
        })
        # Associate version to composite CV
        ContentView.add_version({
            u'content-view-version-id': version1_id,
            u'id': composite_cv['id'],
        })
        # Assert whether version was associated to composite CV
        composite_cv = ContentView.info({u'id': composite_cv['id']})
        self.assertEqual(
            composite_cv['components'][0]['id'],
            version1_id,
            'version was not associated to composite CV',
        )
        # Publish a new version of CV
        ContentView.publish({u'id': composite_cv['id']})
        # Assert whether Version1 was created and exists in Library Env.
        composite_cv = ContentView.info({u'id': composite_cv['id']})
        self.assertEqual(
            composite_cv['lifecycle-environments'][0]['name'],
            ENVIRONMENT,
            'version1 does not exist in Library',
        )
        self.assertEqual(
            composite_cv['versions'][0]['version'],
            u'1.0',
            'Publishing new version of CV was not successful'
        )

    @tier2
    @run_only_on('sat')
    def test_positive_update_version_once(self):
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)
        """when publishing new version to environment, version
        gets updated

        :id: cef62d34-c006-4bd0-950e-29e732388c00

        :setup: Multiple environments for an org; multiple versions of a
            content view created/published

        :steps:
            1. publish a view to an environment noting the CV version
            2. edit and republish a new version of a CV

        :expectedresults: Content view version is updated in target
            environment.


        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a version1 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Only after we publish version1 the info is populated.
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Actual assert for this test happens HERE
        # Test whether the version1 now belongs to Library
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertIn(
            ENVIRONMENT,
            [env['label'] for env in version1['lifecycle-environments']],
            'Version 1 is not in Library',
        )
        # Promotion of version1 to Dev env
        ContentView.version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        # The only way to validate whether env has the version is to
        # validate that version has the env.
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertIn(
            self.env1['id'],
            [env['id'] for env in version1['lifecycle-environments']],
            'Promotion of version1 not successful to the env',
        )
        # Now Publish version2 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Only after we publish version2 the info is populated.
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version2 id
        version2_id = new_cv['versions'][1]['id']
        # Test whether the version2 now belongs to Library
        version2 = ContentView.version_info({u'id': version2_id})
        self.assertIn(
            ENVIRONMENT,
            [env['label'] for env in version2['lifecycle-environments']],
            'Version 2 not in Library'
        )
        # Promotion of version2 to Dev env
        ContentView.version_promote({
            u'id': version2_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        # Actual assert for this test happens here.
        # Test whether the version2 now belongs to next env
        version2 = ContentView.version_info({u'id': version2_id})
        self.assertIn(
            self.env1['id'],
            [env['id'] for env in version2['lifecycle-environments']],
            'Promotion of version2 not successful to the env',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_update_version_multiple(self):
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)
        """when publishing new version to environment, version
        gets updated

        :id: e5704b86-9919-471b-8362-1831d1983e70

        :setup: Multiple environments for an org; multiple versions of a
            content view created/published

        :steps:
            1. publish a view to an environment
            2. edit and republish a new version of a CV

        :expectedresults: Content view version is updated in source
            environment.


        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a version1 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Only after we publish version1 the info is populated.
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Test whether the version1 now belongs to Library
        version = ContentView.version_info({u'id': version1_id})
        self.assertIn(
            ENVIRONMENT,
            [env['label'] for env in version['lifecycle-environments']],
            'Version 1 is not in Library',
        )
        # Promotion of version1 to Dev env
        ContentView.version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        # The only way to validate whether env has the version is to
        # validate that version has the env.
        # Test whether the version1 now belongs to next env
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertIn(
            self.env1['id'],
            [env['id'] for env in version1['lifecycle-environments']],
            'Promotion of version1 not successful to the env',
        )
        # Now Publish version2 of CV
        ContentView.publish({u'id': new_cv['id']})
        # As per Dev Notes:
        # Similarly when I publish version y, version x goes away from Library.
        # Actual assert for this test happens here.
        # Test that version1 does not exist in Library after publishing v2
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            len(version1['lifecycle-environments']),
            1,
            'Version1 may still exist in Library',
        )
        self.assertNotIn(
            ENVIRONMENT,
            [env['label'] for env in version1['lifecycle-environments']],
            'Version1 still exists in Library',
        )
        # Only after we publish version2 the info is populated.
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version2 id
        version2_id = new_cv['versions'][1]['id']
        # Promotion of version2 to next env
        ContentView.version_promote({
            u'id': version2_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        # Actual assert for this test happens here.
        # Test that version1 does not exist in any/next env after,
        # promoting version2 to next env
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            len(version1['lifecycle-environments']),
            0,
            'version1 still exists in the next env',
        )

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_chost_by_id(self):
        """Attempt to subscribe content host to content view

        :id: db0bfd9d-3150-427e-9683-a68af33813e7

        :expectedresults: Content host can be subscribed to content view


        :CaseLevel: System
        """
        new_org = make_org()
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        content_view = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')
        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @run_in_one_thread
    @run_only_on('sat')
    @tier3
    def test_positive_subscribe_chost_by_id_using_rh_content(self):
        """Attempt to subscribe content host to content view that has
        Red Hat repository assigned to it

        :id: aeaaa363-5146-45ee-8c81-e54c7876fb81

        :expectedresults: Content Host can be subscribed to content view with
            Red Hat repository

        :CaseLevel: System
        """
        self.create_rhel_content()
        env = make_lifecycle_environment({
            u'organization-id': self.rhel_content_org['id'],
        })
        content_view = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        ContentView.add_repository({
            u'id': content_view['id'],
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(
            content_view['yum-repositories'][0]['name'],
            self.rhel_repo_name,
        )
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')
        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': self.rhel_content_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    @tier3
    def test_positive_subscribe_chost_by_id_using_rh_content_and_filters(self):
        """Attempt to subscribe content host to filtered content view
        that has Red Hat repository assigned to it

        :id: 8d1e0daf-6130-4b50-827d-061e6c32749d

        :expectedresults: Content Host can be subscribed to filtered content
            view with Red Hat repository

        :CaseLevel: System

        :BZ: 1359665
        """
        self.create_rhel_content()
        env = make_lifecycle_environment({
            u'organization-id': self.rhel_content_org['id'],
        })
        content_view = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        ContentView.add_repository({
            u'id': content_view['id'],
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(
            content_view['yum-repositories'][0]['name'],
            self.rhel_repo_name,
        )

        name = gen_string('utf8')
        ContentView.filter.create({
            'content-view-id': content_view['id'],
            'inclusion': 'true',
            'name': name,
            'type': 'rpm',
        })

        make_content_view_filter_rule({
            'content-view-filter': name,
            'content-view-id': content_view['id'],
            'name': gen_string('utf8'),
        })

        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })

        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': self.rhel_content_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_chost_by_id_using_custom_content(self):
        """Attempt to subscribe content host to content view that has
        custom repository assigned to it

        :id: 9758756a-2536-4777-a6a9-ed618453ebe7

        :expectedresults: Content Host can be subscribed to content view with
            custom repository

        :CaseLevel: System
        """
        new_org = make_org()
        new_product = make_product({u'organization-id': new_org['id']})
        new_repo = make_repository({u'product-id': new_product['id']})
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        Repository.synchronize({'id': new_repo['id']})
        content_view = make_content_view({u'organization-id': new_org['id']})
        ContentView.add_repository({
            u'id': content_view['id'],
            u'organization-id': new_org['id'],
            u'repository-id': new_repo['id'],
        })

        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })

        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_chost_by_id_using_ccv(self):
        """Attempt to subscribe content host to composite content view

        :id: 4be340c0-9e58-4b96-ab37-d7e3b12c724f

        :expectedresults: Content host can be subscribed to composite content
            view


        :CaseLevel: System
        """
        new_org = make_org()
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        content_view = make_content_view({
            'composite': True,
            'organization-id': new_org['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })

        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_chost_by_id_using_puppet_content(self):
        """Attempt to subscribe content host to content view that has
        puppet module assigned to it

        :id: 7f45a162-e944-4e2c-a892-b26d1d21c844

        :expectedresults: Content Host can be subscribed to content view with
            puppet module

        :CaseLevel: System
        """
        # see BZ #1222118
        new_org = make_org()
        new_product = make_product({u'organization-id': new_org['id']})

        repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': new_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': repository['id']})

        content_view = make_content_view({u'organization-id': new_org['id']})

        puppet_result = PuppetModule.list({
            u'repository-id': repository['id'],
            u'per-page': False,
        })

        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add({
                u'content-view-id': content_view['id'],
                u'uuid': puppet_module['uuid'],
            })

        env = make_lifecycle_environment({u'organization-id': new_org['id']})

        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })

        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_host_with_restricted_user_permissions(self):
        """Attempt to subscribe a host with restricted user permissions.

        :id: 7b5ec90b-3942-48a9-9cc1-a361e698d16d

        :BZ: 1379856

        :steps:

            1. Create organization, content view with custom yum repository.
            2. Publish the content view
            3. Create a user within the created organization with the following
               permissions::

                - (Miscellaneous) [my_organizations]
                - Environment [view_environments]
                - Organization [view_organizations,
                    view_subscriptions,
                    attach_subscriptions,
                    unattach_subscriptions,
                    import_manifest,
                    delete_manifest]
                - Katello::ContentView [view_content_views]
                - ConfigGroup [view_config_groups]
                - Hostgroup view_hostgroups
                - Host [view_hosts, create_hosts, edit_hosts]
                - Location [view_locations]
                - Katello::KTEnvironment [view_lifecycle_environments]
                - SmartProxy [view_smart_proxies, view_capsule_content]
                - Architecture [view_architectures]

        :expectedresults: host subscribed to content view with user that has
            restricted permissions.

        :CaseLevel: System
        """
        # prepare the user and the required permissions data
        user_name = gen_alphanumeric()
        user_password = gen_alphanumeric()
        required_rc_permissions = {
            '(Miscellaneous)': ['my_organizations'],
            'Environment': ['view_environments'],
            'Organization': [
                'view_organizations',
                'view_subscriptions',
                'attach_subscriptions',
                'unattach_subscriptions',
                'import_manifest',
                'delete_manifest'
            ],
            'Katello::ContentView': ['view_content_views'],
            'ConfigGroup': ['view_config_groups'],
            'Hostgroup': ['view_hostgroups'],
            'Host': ['view_hosts', 'create_hosts', 'edit_hosts'],
            'Location': ['view_locations'],
            'Katello::KTEnvironment': ['view_lifecycle_environments'],
            'SmartProxy': ['view_smart_proxies', 'view_capsule_content'],
            'Architecture': ['view_architectures'],
        }
        # Create an organization
        org = make_org()
        # Create a non admin user, for the moment without any permissions
        user = make_user({
            'admin': False,
            'default-organization-id': org['id'],
            'organization-ids': [org['id']],
            'login': user_name,
            'password': user_password,
        })
        # Create a new role
        role = make_role()
        # Get the available permissions
        available_permissions = Filter.available_permissions()
        # group the available permissions by resource type
        available_rc_permissions = {}
        for permission in available_permissions:
            permission_resource = permission['resource']
            if permission_resource not in available_rc_permissions:
                available_rc_permissions[permission_resource] = []
            available_rc_permissions[permission_resource].append(
                permission)
        # create only the required role permissions per resource type
        for resource_type, permission_names in required_rc_permissions.items():
            # assert that the required resource type is available
            self.assertIn(resource_type, available_rc_permissions)
            available_permission_names = [
                permission['name']
                for permission in available_rc_permissions[resource_type]
                if permission['name'] in permission_names
            ]
            # assert that all the required permissions are available
            self.assertEqual(set(permission_names),
                             set(available_permission_names))
            # Create the current resource type role permissions
            make_filter({
                'role-id': role['id'],
                'permissions': permission_names,
            })
        # Add the created and initiated role with permissions to user
        User.add_role({'id': user['id'], 'role-id': role['id']})
        # assert that the user is not an admin one and cannot read the current
        # role info (note: view_roles is not in the required permissions)
        with self.assertRaises(CLIReturnCodeError) as context:
            Role.with_user(user_name, user_password).info(
                {'id': role['id']})
        self.assertIn(
            'Forbidden - server refused to process the request',
            context.exception.stderr
        )
        # Create a lifecycle environment
        env = make_lifecycle_environment({'organization-id': org['id']})
        # Create a product
        product = make_product({'organization-id': org['id']})
        # Create a yum repository and synchronize
        repo = make_repository({
            'product-id': product['id'],
            'url': FAKE_1_YUM_REPO
        })
        Repository.synchronize({'id': repo['id']})
        # Create a content view, add the yum repository and publish
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        # assert that the content view has been published and has versions
        self.assertGreater(len(content_view['versions']), 0)
        content_view_version = content_view['versions'][0]
        # Promote the content view version to the created environment
        ContentView.version_promote({
            'id': content_view_version['id'],
            'to-lifecycle-environment-id': env['id'],
        })
        # assert that the user can read the content view info as per required
        # permissions
        user_content_view = ContentView.with_user(
            user_name, user_password).info({'id': content_view['id']})
        # assert that this is the same content view
        self.assertEqual(content_view['name'], user_content_view['name'])
        # create a client host and register it with the created user
        with VirtualMachine(distro=DISTRO_RHEL7) as host_client:
            host_client.install_katello_ca()
            host_client.register_contenthost(
                org['name'],
                lce=u'{0}/{1}'.format(env['name'], content_view['name']),
                username=user_name,
                password=user_password
            )
            self.assertTrue(host_client.subscribed)
            # check that the client host exist in the system
            org_hosts = Host.list({'organization-id': org['id']})
            self.assertEqual(len(org_hosts), 1)
            self.assertEqual(org_hosts[0]['name'], host_client.hostname)

    @tier2
    @run_only_on('sat')
    def test_positive_clone_within_same_env(self):
        """Attempt to create, publish and promote new content view based on
        existing view within the same environment as the original content view

        :id: 4d7fa623-3516-4abe-a98c-98acbfb7e9c9

        :expectedresults: Cloned content view can be published and promoted to
            the same environment as the original content view

        :CaseLevel: Integration
        """
        org = make_org()
        cloned_cv_name = gen_string('alpha')
        lc_env = make_lifecycle_environment({u'organization-id': org['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        new_cv = ContentView.copy({
            u'id': content_view['id'],
            u'new-name': cloned_cv_name,
        })[0]
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        cvv = new_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertIn(
            {'id': lc_env['id'], 'name': lc_env['name']},
            new_cv['lifecycle-environments']
        )

    @tier2
    @run_only_on('sat')
    def test_positive_clone_with_diff_env(self):
        """Attempt to create, publish and promote new content view based on
        existing view but promoted to a different environment

        :id: 308ffaa3-cd01-4a16-b84d-c60c32959235

        :expectedresults: Cloned content view can be published and promoted to
            a different environment as the original content view

        :CaseLevel: Integration
        """
        org = make_org()
        cloned_cv_name = gen_string('alpha')
        lc_env = make_lifecycle_environment({u'organization-id': org['id']})
        lc_env_cloned = make_lifecycle_environment({
            u'organization-id': org['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        new_cv = ContentView.copy({
            u'id': content_view['id'],
            u'new-name': cloned_cv_name,
        })[0]
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        cvv = new_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': lc_env_cloned['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertIn(
            {'id': lc_env_cloned['id'], 'name': lc_env_cloned['name']},
            new_cv['lifecycle-environments']
        )

    @run_only_on('sat')
    @stubbed
    def test_positive_restart_dynflow_promote(self):
        """attempt to restart a failed content view promotion

        :id: 2be23f85-3f62-4319-87ea-41f28cf401dc

        :steps:
            1. (Somehow) cause a CV promotion to fail.  Not exactly sure how
               yet.
            2. Via Dynflow, restart promotion

        :expectedresults: Promotion is restarted.

        :caseautomation: notautomated

        """

    @run_only_on('sat')
    @stubbed
    def test_positive_restart_dynflow_publish(self):
        """attempt to restart a failed content view publish

        :id: 24468014-46b2-403e-8ed6-2daeda5a0163

        :steps:
            1. (Somehow) cause a CV publish  to fail.  Not exactly sure how
               yet.
            2. Via Dynflow, restart publish

        :expectedresults: Publish is restarted.

        :caseautomation: notautomated

        """

    @run_only_on('sat')
    @tier2
    def test_positive_remove_renamed_cv_version_from_default_env(self):
        """Remove version of renamed content view from Library environment

        :id: aa9bbfda-72e8-45ec-b26d-fdf2691980cf

        :Steps:

            1. Create a content view
            2. Add a yum repo to the content view
            3. Publish the content view
            4. Rename the content view
            5. remove the published version from Library environment

        :expectedresults: content view version is removed from Library
            environment

        :CaseLevel: Integration
        """
        new_name = gen_string('alpha')
        org = make_org()
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': custom_yum_repo['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        # ensure that the published content version is in Library environment
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        self.assertIn(
            ENVIRONMENT,
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # rename the content view
        ContentView.update({
            'id': content_view['id'],
            'new-name': new_name
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(new_name, content_view['name'])
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': ENVIRONMENT
        })
        # ensure that the published content version is not in Library
        # environment
        self.assertNotIn(
            ENVIRONMENT,
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_promoted_cv_version_from_default_env(self):
        """Remove promoted content view version from Library environment

        :id: 6643837a-560a-47de-aa4d-90778914dcfa

        :Steps:

            1. Create a content view
            2. Add a puppet module(s) to the content view
            3. Publish the content view
            4. Promote the content view version from Library -> DEV
            5. remove the content view version from Library environment

        :expectedresults:

            1. Content view version exist only in DEV and not in Library
            2. The puppet module(s) exists in content view version

        :CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        ContentView.version_promote({
            'id': content_view_version['id'],
            'to-lifecycle-environment-id': lce_dev['id']
        })
        # ensure that the published content version is in Library and DEV
        # environments
        content_view_version_info = ContentView.version_info({
            'organization-id': org['id'],
            'content-view-id': content_view['id'],
            'id': content_view_version['id']
        })
        content_view_version_lce_names = {
            lce['name']
            for lce in content_view_version_info['lifecycle-environments']
        }
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name']},
            content_view_version_lce_names
        )
        initial_puppet_modules_ids = {
            puppet_module['id']
            for puppet_module in content_view_version_info.get(
                'puppet-modules', [])
        }
        self.assertGreater(len(initial_puppet_modules_ids), 0)
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': ENVIRONMENT
        })
        # ensure content view version not in Library and only in DEV
        # environment and that puppet module still exist
        content_view_version_info = ContentView.version_info({
            'organization-id': org['id'],
            'content-view-id': content_view['id'],
            'id': content_view_version['id']
        })
        content_view_version_lce_names = {
            lce['name']
            for lce in content_view_version_info['lifecycle-environments']
        }
        self.assertEqual({lce_dev['name']}, content_view_version_lce_names)
        puppet_modules_ids = {
                puppet_module['id']
                for puppet_module in content_view_version_info.get(
                    'puppet-modules', [])
        }
        self.assertEqual(initial_puppet_modules_ids, puppet_modules_ids)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_qe_promoted_cv_version_from_default_env(self):
        """Remove QE promoted content view version from Library environment

        :id: e286697f-4113-40a3-b8e8-9ca50647e6d5

        :Steps:

            1. Create a content view
            2. Add docker repo(s) to it
            3. Publish content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE
            5. remove the content view version from Library environment

        :expectedresults: Content view version exist only in DEV, QE and not in
            Library

        :CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        docker_product = make_product({u'organization-id': org['id']})
        docker_repository = make_repository({
            'content-type': 'docker',
            'docker-upstream-name': DOCKER_UPSTREAM_NAME,
            'name': gen_string('alpha', 20),
            'product-id': docker_product['id'],
            'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': docker_repository['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': docker_repository['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV and QE
        # environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': ENVIRONMENT
        })
        # ensure content view version is not in Library and only in DEV and QE
        # environments
        self.assertEqual(
            {lce_dev['name'], lce_qe['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_prod_promoted_cv_version_from_default_env(self):
        """Remove PROD promoted content view version from Library environment

        :id: ffe3d64e-c3d2-4889-9454-ccc6b10f4db7

        :Steps:

            1. Create a content view
            2. Add yum repositories, puppet modules, docker repositories to CV
            3. Publish content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE -> PROD
            5. remove the content view version from Library environment

        :expectedresults: Content view version exist only in DEV, QE, PROD and
            not in Library

        :CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        lce_prod = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_qe['name']
        })
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        docker_product = make_product({u'organization-id': org['id']})
        docker_repository = make_repository({
            'content-type': 'docker',
            'docker-upstream-name': DOCKER_UPSTREAM_NAME,
            'name': gen_string('alpha', 20),
            'product-id': docker_product['id'],
            'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': docker_repository['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        for repo in [custom_yum_repo, docker_repository]:
            ContentView.add_repository({
                'id': content_view['id'],
                'organization-id': org['id'],
                'repository-id': repo['id'],
            })
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_prod]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV, QE and
        # PROD environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': ENVIRONMENT
        })
        # ensure content view version is not in Library and only in DEV, QE
        # and PROD environments
        self.assertEqual(
            {lce_dev['name'], lce_qe['name'], lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_cv_version_from_env(self):
        """Remove promoted content view version from environment

        :id: 577757ac-b184-4ece-9310-182dd5ceb718

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE -> STAGE -> PROD
            5. remove the content view version from PROD environment
            6. Assert: content view version exists only in Library, DEV, QE,
               STAGE and not in PROD
            7. Promote again from STAGE -> PROD

        :expectedresults: Content view version exist in Library, DEV, QE,
            STAGE, PROD

        :CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        lce_stage = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_qe['name']
        })
        lce_prod = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_stage['name']
        })
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': custom_yum_repo['id'],
        })
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name'],
             lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # remove content view version from PROD lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': lce_prod['name']
        })
        # ensure content view version is not in PROD and only in Library, DEV,
        # QE and STAGE environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # promote content view version to PROD environment again
        ContentView.version_promote({
            'id': content_view_version['id'],
            'to-lifecycle-environment-id': lce_prod['id']
        })
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name'],
             lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_cv_version_from_multi_env(self):
        """Remove promoted content view version from multiple environment

        :id: 997cfd7d-9029-47e2-a41e-84f4370b5ce5

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE -> STAGE -> PROD
            5. Remove content view version from QE, STAGE and PROD

        :expectedresults: Content view version exists only in Library, DEV

        :CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        lce_stage = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_qe['name']
        })
        lce_prod = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_stage['name']
        })
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': custom_yum_repo['id'],
        })
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name'],
             lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # remove content view version from QE, STAGE, PROD lifecycle
        # environments
        for lce in [lce_qe, lce_stage, lce_prod]:
            ContentView.remove_from_environment({
                'id': content_view['id'],
                'organization-id': org['id'],
                'lifecycle-environment': lce['name']
            })
        # ensure content view version is not in PROD and only in Library, DEV,
        # QE and STAGE environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_delete_cv_promoted_to_multi_env(self):
        """Delete published content view with version promoted to multiple
         environments

        :id: 93dd7518-5901-4a71-a4c3-0f1215238b26

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment Library -> DEV
               -> QE -> STAGE -> PROD
            5. Delete the content view (may delete the published versions
               environments prior this step)

        :expectedresults: The content view doesn't exists

        :CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        lce_stage = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_qe['name']
        })
        lce_prod = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_stage['name']
        })
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': custom_yum_repo['id'],
        })
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        promoted_lce_names_set = self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name'],
             lce_prod['name']},
            promoted_lce_names_set
        )
        # remove from all promoted lifecycle environments
        for lce_name in promoted_lce_names_set:
            ContentView.remove_from_environment({
                'id': content_view['id'],
                'organization-id': org['id'],
                'lifecycle-environment': lce_name
            })
        # ensure content view in content views list
        content_views = ContentView.list({'organization-id': org['id']})
        self.assertIn(
            content_view['name'],
            [cv['name'] for cv in content_views]
        )
        # delete the content view
        ContentView.delete({'id': content_view['id']})
        # ensure the content view is not in content views list
        content_views = ContentView.list({'organization-id': org['id']})
        self.assertNotIn(
            content_view['name'],
            [cv['name'] for cv in content_views]
        )

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_remove_cv_version_from_env_with_host_registered(self):
        """Remove promoted content view version from environment that is used
        in association of an Activation key and content-host registration.

        :id: 001a2b76-a87b-4c11-8837-f5fe3c04a075

        :Steps:

            1. Create a content view cv1
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment Library -> DEV
               -> QE
            5. Create an Activation key with the QE environment
            6. Register a content-host using the Activation key
            7. Remove the content view cv1 version from QE environment.
               Note - prior removing replace the current QE environment of cv1
               by DEV and content view cv1 for Content-host and for Activation
               key.
            8. Refresh content-host subscription

        :expectedresults:

            1. Activation key exists
            2. Content-host exists
            3. QE environment of cv1 was replaced by DEV environment of cv1 in
               activation key
            4. QE environment of cv1 was replaced by DEV environment of cv1 in
               content-host
            5. At content-host some package from cv1 is installable

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_delete_cv_multi_env_promoted_with_host_registered(self):
        """Delete published content view with version promoted to multiple
         environments, with one of the environments used in association of an
         Activation key and content-host registration.

        :id: 82442d23-45b5-4d39-b867-c5d46bbcbbf9

        :Steps:

            1. Create two content view cv1 and cv2
            2. Add a yum repo and a puppet module to both content views
            3. Publish the content views
            4. Promote the content views to multiple environment Library -> DEV
               -> QE
            5. Create an Activation key with the QE environment and cv1
            6. Register a content-host using the Activation key
            7. Delete the content view cv1.
               Note - prior deleting replace the current QE environment of cv1
               by DEV and content view cv2 for Content-host and for Activation
               key.
            8. Refresh content-host subscription

        :expectedresults:

            1. The content view cv1 doesn't exist
            2. Activation key exists
            3. Content-host exists
            4. QE environment of cv1 was replaced by DEV environment of cv2 in
               activation key
            5. QE environment of cv1 was replaced by DEV environment of cv2 in
               content-host
            6. At content-host some package from cv2 is installable

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_remove_cv_version_from_multi_env_capsule_scenario(self):
        """Remove promoted content view version from multiple environment,
        with satellite setup to use capsule

        :id: 3725fef6-73a4-4dcb-a306-70e6ba826a3d

        :Steps:

            1. Create a content view
            2. Setup satellite to use a capsule and to sync all lifecycle
               environments
            3. Add a yum repo, puppet module and a docker repo to the content
               view
            4. Publish the content view
            5. Promote the content view to multiple environment Library -> DEV
               -> QE -> PROD
            6. Make sure the capsule is updated (content synchronization may be
               applied)
            7. Disconnect the capsule
            8. Remove the content view version from Library and DEV
               environments and assert successful completion
            9. Bring the capsule back online and assert that the task is
               completed in capsule
            10. Make sure the capsule is updated (content synchronization may
                be applied)

        :expectedresults: content view version in capsule is removed from
            Library and DEV and exists only in QE and PROD

        :caseautomation: notautomated

        :CaseLevel: System
        """
        # Note: This test case requires complete external capsule
        #  configuration.

    # ROLES TESTING

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    def test_negative_user_with_no_create_view_cv_permissions(self):
        """Unauthorized users are not able to create/view content views

        :id: 17617893-27c2-4cb2-a2ed-47378ef90e7a

        :setup: Create a user without the Content View create/view permissions

        :expectedresults: User with no content view create/view permissions
            cannot create or view the content view

        :CaseImportance: Critical
        """
        password = gen_alphanumeric()
        no_rights_user = make_user({'password': password})
        no_rights_user['password'] = password
        org_id = make_org(cached=True)['id']
        for name in generate_strings_list(exclude_types=['cjk']):
            with self.subTest(name):
                # test that user can't create
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.with_user(
                        no_rights_user['login'],
                        no_rights_user['password'],
                    ).create({
                        'name': name,
                        'organization-id': org_id,
                    })
                # test that user can't read
                con_view = make_content_view({
                    'name': name,
                    'organization-id': org_id,
                })
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.with_user(
                        no_rights_user['login'],
                        no_rights_user['password'],
                    ).info({'id': con_view['id']})

    @run_only_on('sat')
    @tier2
    def test_negative_user_with_read_only_cv_permission(self):
        """Read-only user is able to view content view

        :id: 588f57b5-9855-4c14-80d0-64b617c6b6dc

        :setup: create a user with the Content View read-only role

        :expectedresults: User with read-only role for content view can view
            the content view but not Create / Modify / Promote / Publish

        :CaseLevel: Integration
        """
        cv = make_content_view({'organization-id': self.org['id']})
        password = gen_string('alphanumeric')
        user = make_user({'password': password})
        role = make_role()
        make_filter({
            'organization-ids': self.org['id'],
            'permissions': 'view_content_views',
            'role-id': role['id'],
            'override': 1,
        })
        User.add_role({
            'id': user['id'],
            'role-id': role['id'],
        })
        ContentView.with_user(user['login'], password).info({'id': cv['id']})
        # Verify read-only user can't either edit CV
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).update({
                'id': cv['id'],
                'new-name': gen_string('alphanumeric'),
            })
        # or create a new one
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).create({
                'name': gen_string('alphanumeric'),
                'organization-id': self.org['id'],
            })
        # or publish
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).publish({
                'id': cv['id']})
        ContentView.publish({'id': cv['id']})
        cvv = ContentView.info({'id': cv['id']})['versions'][-1]
        # or promote
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).version_promote({
                'id': cvv['id'],
                'organization-id': self.org['id'],
                'to-lifecycle-environment-id': self.env1['id'],
            })

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1464414)
    @tier2
    def test_positive_user_with_all_cv_permissions(self):
        """A user with all content view permissions is able to create,
        read, modify, promote, publish content views

        :id: ac40e9bb-9f1a-48d1-a0fe-9ac2be0f33f4

        :setup: create a user with all content view permissions

        :expectedresults: User is able to perform create, read, modify,
            promote, publish content view

        :CaseLevel: Integration
        """
        cv = make_content_view({'organization-id': self.org['id']})
        password = gen_string('alphanumeric')
        user = make_user({
            'password': password,
            'organization-ids': self.org['id']
        })
        role = make_role({'organization-ids': self.org['id']})
        # note: the filters inherit role organizations
        make_filter({
            'permissions': PERMISSIONS['Katello::ContentView'],
            'role-id': role['id'],
        })
        make_filter({
            'permissions': PERMISSIONS['Katello::KTEnvironment'],
            'role-id': role['id'],
        })
        User.add_role({
            'id': user['id'],
            'role-id': role['id'],
        })
        # Make sure user is not admin and has only expected roles assigned
        user = User.info({'id': user['id']})
        self.assertEqual(user['admin'], 'no')
        self.assertEqual(set(user['roles']), {DEFAULT_ROLE, role['name']})
        # Verify user can either edit CV
        ContentView.with_user(user['login'], password).info({'id': cv['id']})
        new_name = gen_string('alphanumeric')
        ContentView.with_user(user['login'], password).update({
            'id': cv['id'],
            'new-name': new_name,
        })
        cv = ContentView.info({'id': cv['id']})
        self.assertEqual(cv['name'], new_name)
        # or create a new one
        new_cv_name = gen_string('alphanumeric')
        new_cv = ContentView.with_user(user['login'], password).create({
            'name': new_cv_name,
            'organization-id': self.org['id'],
        })
        self.assertEqual(new_cv['name'], new_cv_name)
        # or publish
        ContentView.with_user(user['login'], password).publish({
            'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        self.assertEqual(len(cv['versions']), 1)
        # or promote
        ContentView.with_user(user['login'], password).version_promote({
            'id': cv['versions'][-1]['id'],
            'organization-id': self.org['id'],
            'to-lifecycle-environment-id': self.env1['id'],
        })
        cv = ContentView.info({'id': cv['id']})
        self.assertIn(
            self.env1['id'],
            [env['id'] for env in cv['lifecycle-environments']],
        )


class OstreeContentViewTestCase(CLITestCase):
    """Tests for custom ostree contents in content views."""

    @classmethod
    @skip_if_os('RHEL6')
    def setUpClass(cls):
        """Create an organization, product, and repo with all content-types."""
        super(OstreeContentViewTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({u'organization-id': cls.org['id']})
        # Create new custom ostree repo
        cls.ostree_repo = make_repository({
            u'product-id': cls.product['id'],
            u'content-type': u'ostree',
            u'publish-via-http': u'false',
            u'url': FEDORA23_OSTREE_REPO,
        })
        Repository.synchronize({'id': cls.ostree_repo['id']})
        # Create new yum repository
        cls.yum_repo = make_repository({
            u'url': FAKE_1_YUM_REPO,
            u'product-id': cls.product['id'],
        })
        Repository.synchronize({'id': cls.yum_repo['id']})
        # Create new Puppet repository
        cls.puppet_repo = make_repository({
            u'url': FAKE_0_PUPPET_REPO,
            u'content-type': 'puppet',
            u'product-id': cls.product['id'],
        })
        Repository.synchronize({'id': cls.puppet_repo['id']})
        # Create new docker repository
        cls.docker_repo = make_repository({
            u'content-type': u'docker',
            u'docker-upstream-name': u'busybox',
            u'product-id': cls.product['id'],
            u'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': cls.docker_repo['id']})

    @tier2
    @run_only_on('sat')
    def test_positive_add_custom_ostree_content(self):
        """Associate custom ostree content in a view

        :id: 6e89094d-ffd3-4dc6-b925-f76531c56c20

        :expectedresults: Custom ostree content assigned and present in content
            view

        :CaseLevel: Integration
        """
        # Create CV
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
            u'repository': self.ostree_repo['name'],
        })
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(
            cv['ostree-repositories'][0]['name'],
            self.ostree_repo['name'],
            'Ostree Repo was not associated to CV',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_publish_custom_ostree(self):
        """Publish a content view with custom ostree contents

        :id: ec66f1d3-9750-4dfc-a189-f3b0fd6af3e8

        :expectedresults: Content-view with Custom ostree published
            successfully

        :CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
            u'repository': self.ostree_repo['name'],
        })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(len(cv['versions']), 1)

    @tier2
    def test_positive_promote_custom_ostree(self):
        """Promote a content view with custom ostree contents

        :id: 5eb7b9e6-8757-4152-9114-42a5eb021bbc

        :expectedresults: Content-view with custom ostree contents promoted
            successfully

        :CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
            u'repository': self.ostree_repo['name'],
        })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        lc_env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        cv = ContentView.info({u'id': cv['id']})
        environment = {'id': lc_env['id'], 'name': lc_env['name']}
        self.assertIn(environment, cv['lifecycle-environments'])

    @tier2
    def test_positive_publish_promote_with_custom_ostree_and_other(self):
        """Publish & Promote a content view with custom ostree and other contents

        :id: 35668fa6-0a24-43ae-b562-26c5ac77e94d

        :expectedresults: Content-view with custom ostree and other contents
            promoted successfully

        :CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        repos = [
            self.ostree_repo,
            self.yum_repo,
            self.docker_repo,
        ]
        for repo in repos:
            ContentView.add_repository({
                u'name': cv['name'],
                u'organization': self.org['name'],
                u'product': self.product['name'],
                u'repository': repo['name'],
            })
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(
            cv['ostree-repositories'][0]['name'],
            self.ostree_repo['name'],
            'Ostree Repo was not associated to CV',
        )
        self.assertEqual(
            cv['yum-repositories'][0]['name'],
            self.yum_repo['name'],
            'Yum Repo was not associated to CV',
        )
        self.assertEqual(
            cv['docker-repositories'][0]['name'],
            self.docker_repo['name'],
            'Docker Repo was not associated to CV',
        )
        # Fetch puppet module
        puppet_result = PuppetModule.list({
            u'repository-id': self.puppet_repo['id'],
            u'per-page': False,
        })
        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add({
                u'content-view-id': cv['id'],
                u'uuid': puppet_module['uuid'],
            })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        lc_env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        cv = ContentView.info({u'id': cv['id']})
        environment = {
            'id': lc_env['id'],
            'name': lc_env['name'],
        }
        self.assertIn(environment, cv['lifecycle-environments'])


@run_in_one_thread
class ContentViewRedHatOstreeContent(CLITestCase):
    """Tests for publishing and promoting cv with RH ostree contents."""

    @classmethod
    @skip_if_os('RHEL6')
    @skip_if_not_set('fake_manifest')
    def setUpClass(cls):
        """Set up organization, product and RH atomic repository for tests."""
        super(ContentViewRedHatOstreeContent, cls).setUpClass()
        cls.org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': cls.org['id'],
        })
        RepositorySet.enable({
            u'basearch': None,
            u'name': REPOSET['rhaht'],
            u'organization-id': cls.org['id'],
            u'product': PRDS['rhah'],
            u'releasever': None,
        })
        cls.repo_name = REPOS['rhaht']['name']
        Repository.synchronize({
            u'name': cls.repo_name,
            u'organization-id': cls.org['id'],
            u'product': PRDS['rhah'],
        })

    @tier2
    def test_positive_add_rh_ostree_content(self):
        """Associate RH atomic ostree content in a view

        :id: 5e9dfb32-9cc7-4257-ab6b-f439fb9db2bd

        :expectedresults: RH atomic ostree content assigned and present in
            content view

        :CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhah'],
            u'repository': self.repo_name,
        })
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(
            cv['ostree-repositories'][0]['name'],
            self.repo_name,
            'Ostree Repo was not associated to CV',
        )

    @tier2
    def test_positive_publish_RH_ostree(self):
        """Publish a content view with RH ostree contents

        :id: 4ac5c7d1-9ab2-4a65-b4b8-1582b001125f

        :expectedresults: Content-view with RH ostree contents published
            successfully

        :CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhah'],
            u'repository': self.repo_name,
        })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(len(cv['versions']), 1)

    @tier2
    def test_positive_promote_RH_ostree(self):
        """Promote a content view with RH ostree contents

        :id: 71986705-fe45-4e0f-af0b-288c9c7ce61b

        :expectedresults: Content-view with RH ostree contents promoted
            successfully

        :CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhah'],
            u'repository': self.repo_name,
        })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        lc_env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        cv = ContentView.info({u'id': cv['id']})
        environment = {'id': lc_env['id'], 'name': lc_env['name']}
        self.assertIn(environment, cv['lifecycle-environments'])

    @tier2
    def test_positive_publish_promote_with_RH_ostree_and_other(self):
        """Publish & Promote a content view with RH ostree and other contents

        :id: 87c8ddb1-da32-4103-810d-8e5e28fa888f

        :expectedresults: Content-view with RH ostree and other contents
            promoted successfully

        :CaseLevel: Integration
        """
        RepositorySet.enable({
            'name': REPOSET['rhst7'],
            'organization-id': self.org['id'],
            'product': PRDS['rhel'],
            'releasever': None,
            'basearch': 'x86_64',
        })
        rpm_repo_name = REPOS['rhst7']['name']
        Repository.synchronize({
            u'name': rpm_repo_name,
            u'organization-id': self.org['id'],
            u'product': PRDS['rhel'],
        })
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhah'],
            u'repository': self.repo_name,
        })
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhel'],
            u'repository': rpm_repo_name,
        })
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(
            cv['ostree-repositories'][0]['name'],
            self.repo_name,
            'RH Ostree Repo was not associated to CV',
        )
        self.assertEqual(
            cv['yum-repositories'][0]['name'],
            rpm_repo_name,
            'RH rpm Repo was not associated to CV',
        )
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        lc_env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        cv = ContentView.info({u'id': cv['id']})
        environment = {
            'id': lc_env['id'],
            'name': lc_env['name'],
        }
        self.assertIn(environment, cv['lifecycle-environments'])
