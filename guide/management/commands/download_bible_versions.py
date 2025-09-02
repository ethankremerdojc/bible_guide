import os
from django.core.management.base import BaseCommand, CommandError
import requests
from bible_guide.settings import VERSIONS_DIR
import io
import zipfile

class Command(BaseCommand):
    help = "Downloads a list of bible versions like esv, niv etc."
    
    def get_web_page_contents(self, url):
        response = requests.get(url)

        print(response)

        if response.status_code == 200:
            html_content = response.text
            return html_content
        else:
            raise Exception(f"Failed to get content for the url: {url}")

    def download_king_james(self):
        # Format: Zip into html
        
        source_url = "https://www.gutenberg.org/cache/epub/10/pg10-h.zip"
        response = requests.get(source_url)
        response.raise_for_status()

        zip_data = zipfile.ZipFile(io.BytesIO(response.content))
        html_files = [f for f in zip_data.namelist() if f.endswith(".html")]

        original_name = html_files[0]
        html_content = zip_data.read(original_name)

        kjv_dest_path = os.path.join(VERSIONS_DIR, "kjv.html") 

        with open(kjv_dest_path, 'wb') as kjvfile:
            kjvfile.write(html_content)

        print("Wrote KJV contents to ", kjv_dest_path)



    def handle(self, *args, **kwargs):

        versions_to_download = [
            "KJV"
        ]
        
        if "KJV" in versions_to_download:
            king_james_version = self.download_king_james()


