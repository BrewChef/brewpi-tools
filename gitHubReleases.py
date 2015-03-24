import urllib2
import simplejson as json
import os


class gitHubReleases:
    def __init__(self, url):
        self.url = url
        self.releases = []
        self.update()

    def download(self, url, path):
        # Open the url
        try:
            f = urllib2.urlopen(url)
            print "downloading " + url

            # Open our local file for writing
            fileName = os.path.join(path, os.path.basename(url))
            with open(fileName, "wb") as localFile:
                localFile.write(f.read())
            return os.path.abspath(fileName)

        #handle errors
        except urllib2.HTTPError, e:
            print "HTTP Error:", e.code, url
        except urllib2.URLError, e:
            print "URL Error:", e.reason, url
        return None

    def update(self):
        self.releases = json.load(urllib2.urlopen(self.url + "/releases"))

    # writes .bin in release tagged with tag to directory
    # defaults to ./downloads/tag_name/ as download location
    def getBin(self, tag, path = None):
        try:
            match = (release for release in self.releases if release["tag_name"] == tag).next()
            downloadUrl = (asset["browser_download_url"] for asset in match["assets"] if ".bin" in asset["name"]).next()
        except StopIteration:
            print "tag '{0}' not found".format(tag)
            return None

        if path == None:
            path = os.path.join(os.path.dirname(__file__), "downloads")
            
        downloadDir = os.path.join(os.path.abspath(path), tag)
        print downloadDir
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir)

        fileName = self.download(downloadUrl, downloadDir)
        return fileName

    def getLatestTag(self):
        return self.releases[0]["tag_name"]

    def getTags(self):
        return self.releases[0]["tag_name"]


if __name__ == "__main__":
    # test code
    releases = gitHubReleases("https://api.github.com/repos/BrewPi/firmware")

    latest = releases.getLatestTag()
    print "Latest tag: " + latest
    print "Downloading binary for latest tag"
    localFileName = releases.getBin(latest)
    print "Latest binary downloaded to " + localFileName



# print json.load(urllib2.urlopen(firmwareUrl + "/releases/latest"))


