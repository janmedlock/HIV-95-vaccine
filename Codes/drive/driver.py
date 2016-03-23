import mimetypes
import os.path

import httplib2
import apiclient.discovery
import apiclient.http
import oauth2client.client


class Driver:
    client_secrets = 'client_secret.json'
    credentials_file = 'credentials.json'
    oauth2_scope = 'https://www.googleapis.com/auth/drive'

    def __init__(self, parent = None):
        self.parent = parent

        flow = oauth2client.client.flow_from_clientsecrets(self.client_secrets,
                                                           self.oauth2_scope)
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'r') as fd:
                json = fd.read()
            credentials = oauth2client.client.Credentials.new_from_json(json)
        else:
            flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
            authorize_url = flow.step1_get_authorize_url()
            print('Go to the following link in your browser: ' + authorize_url)
            code = input('Enter verification code: ').strip()
            credentials = flow.step2_exchange(code)
            with open(self.credentials_file, 'w') as fd:
                fd.write(credentials.to_json())

        http = httplib2.Http()
        credentials.authorize(http)
        self.drive_service = apiclient.discovery.build('drive', 'v3',
                                                       http = http)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def find_fileId(self, filename):
        q = "name = '{}' and trashed = false".format(filename)
        if self.parent is not None:
            q += " and '{}' in parents".format(self.parent)

        response = self.drive_service.files().list(
            q = q,
            fields = 'files(id)').execute()

        ids = [f['id'] for f in response['files']]
        if len(ids) == 0:
            return None
        elif len(ids) == 1:
            return ids[0]
        else:
            raise ValueError(
                "Multiple files in directory with name = '{}'!  {}".format(
                    filename, ids))

    def upload(self, filename):
        media_body = apiclient.http.MediaFileUpload(
            filename,
            resumable = True)

        fileId = self.find_fileId(filename)

        if fileId is None:
            print('Creating {}'.format(filename))
        
            job = self.drive_service.files().create(
                body = dict(title = filename,
                            parents = [self.parent]),
                media_body = media_body)
        else:
            print('Updating {}'.format(filename))

            job = self.drive_service.files().update(
                fileId = fileId,
                body = dict(title = filename),
                media_body = media_body)

        return job.execute()

    def download(self, filename):
        fileId = self.find_fileId(filename)

        if fileId is None:
            raise ValueError("No file '{}' in directory!".format(filename))

        print('Downloading {}'.format(filename))

        job = self.drive_service.files().get_media(fileId = fileId)

        response = job.execute()

        with open(filename, 'wb') as fd:
            fd.write(response)

    def export(self, filename, mimeType):
        fileId = self.find_fileId(filename)

        if fileId is None:
            raise ValueError("No file '{}' in directory!".format(filename))

        print('Exporting {}'.format(filename))

        job = self.drive_service.files().export(
            fileId = fileId,
            mimeType = mimeType)

        response = job.execute()

        exportname = filename + mimetypes.guess_extension(mimeType)
        with open(exportname, 'wb') as fd:
            fd.write(response)
