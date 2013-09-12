import slumber
import os
import subprocess

from django.conf import settings


class PopitTestCaseMixin(object):
    project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '../..'))
    test_relative_fixtures_path = 'popit/tests/fixtures/%s.js'

    def get_api_url(self):
        return settings.TEST_POPIT_API_URL
        
    def get_api_client(self):
        return slumber.API(self.get_api_url())

    def get_api_database_name(self):
        api = self.get_api_client()
        # https://github.com/dstufft/slumber/issues/28
        return api.__getattr__('').get()['info']['databaseName']

    def delete_api_database(self):
        name = self.get_api_database_name()
        dev_null = open(os.devnull, 'w')
        subprocess.call(["mongo", name, '--eval', 'db.dropDatabase()'], stdout=dev_null)
        
    def load_test_data(self, fixture_name='default'):
        """
        Use the mongofixtures CLI tool provided by the pow-mongodb-fixtures package
        used by popit-api to load some test data into db. Don't use the test fixture
        from popit-api though as we don't want changes to that to break our test
        suite.

            https://github.com/powmedia/pow-mongodb-fixtures#cli-usage

        """
        
        project_root = self.project_root
        
        # gather the args for the call
        mongofixtures_path = os.path.join( project_root, 'popit-api-for-testing/node_modules/.bin/mongofixtures' )
        database_name      = self.get_api_database_name()
        test_fixtures_path = os.path.join( project_root, self.test_relative_fixtures_path%fixture_name )

        # Check that the fixture exists
        if not os.path.exists(test_fixtures_path):
            raise Exception("Could not find fixture for %s at %s" % (fixture_name, test_fixtures_path))

        # Hack to deal with bad handling of absolute paths in mongofixtures.
        # Fix: https://github.com/powmedia/pow-mongodb-fixtures/pull/14
        test_fixtures_path = os.path.relpath( test_fixtures_path )

        # Usage: mongofixtures db_name path/to/fixtures.js
        dev_null = open(os.devnull, 'w')
        exit_code = subprocess.call([mongofixtures_path, database_name, test_fixtures_path], stdout=dev_null)
        if exit_code:
            raise Exception("Error loading fixtures for '%s'" % fixture_name)
