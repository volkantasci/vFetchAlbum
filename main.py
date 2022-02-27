import os
import subprocess
import multiprocessing
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from sys import argv
from webdriver_manager.firefox import GeckoDriverManager
from shutil import which


class Cloner:
    def __init__(self, music_folder_path: str, url_list: list, driver: webdriver.Firefox, temp_folder: str):
        self.driver = driver
        self.url_list = url_list
        self.music_folder_path = music_folder_path
        self.current_album = ""
        self.current_artist = ""
        self.current_url = ""
        self.temp_folder = temp_folder

    def get_parser_from_url(self, url):
        self.driver.get(url)
        soup = BeautifulSoup(self.driver.page_source.encode('utf-8'), features="html.parser")
        self.current_album = soup.find('yt-formatted-string', class_='title').text
        all_a_tags = soup.find_all('a')
        for a in all_a_tags:
            try:
                if 'channel' in a['href']:
                    self.current_artist = a.text
            except KeyError:
                pass

        return soup

    def create_folders(self):
        if os.path.isdir(self.music_folder_path):
            structure = os.sep.join([self.music_folder_path, self.current_artist, self.current_album])
            os.makedirs(structure, exist_ok=True)
            os.makedirs(self.temp_folder, exist_ok=True)
            os.system(f'rm -rf "{self.temp_folder}/*"')

            return 0, "Successfully created"
        else:
            return 1, "Music folder is not valid"

    def fetch_all_songs(self):
        os.chdir(self.temp_folder)
        os.system("rm -rf *")
        print("Parçalar bu adresten alınıyor, lütfen bekleyiniz...")
        print(f"Adres: {self.current_url}")
        subprocess.run(['yt-dlp', '-x', self.current_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Parçalar çekildi!")

    def fetch_cover(self):
        os.chdir(self.temp_folder)
        soup = BeautifulSoup(self.driver.page_source.encode('utf-8'))
        img = soup.find('img', id='img')
        command = f'wget {img["src"]} -O cover.jpg'
        os.system(command)

    def add_covers(self):
        os.chdir(self.temp_folder)
        os.makedirs('covering')
        os.system('rm -rf covering/*')
        music_file_extensions = ['.opus', '.oog,']
        music_files = [i for i in os.listdir('.') if '.' in i]

        def cover_file(file):
            dot_index = file.rindex('.')
            extension = file[dot_index:]
            title = file

            if '[' in file:
                bracket_index = file.index('[')
                title = file[:bracket_index]

            if extension in music_file_extensions:
                print("Process started for:", title)
                merged_name = os.sep.join([self.music_folder_path, self.current_artist, self.current_album, file])
                add_art_command = f'opusdec --force-wav "{file}" - | opusenc --artist "{self.current_artist}" --album "{self.current_album}" --title "{title}" --picture cover.jpg - "{merged_name}"'
                subprocess.run([add_art_command, ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
                print("Process finished for: ", title)
            else:
                print("Dosya uygun formatta değil: " + title)

        processes = []
        for f in music_files:
            p = multiprocessing.Process(target=cover_file, args=(f,))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

    def run_url_list(self):
        for url in self.url_list:
            if not url:
                continue
            self.current_url = url
            self.get_parser_from_url(self.current_url)
            self.create_folders()
            self.fetch_all_songs()
            self.fetch_cover()
            self.add_covers()

        self.driver.close()


def valid_args():
    return [line if '\n' not in line else line[:-1] for line in open(argv[1]).readlines()] if len(argv) == 2 else print(
        "Missing URL File") or exit(1)


def check_requirements():
    return True not in [which(i) is None for i in ['yt-dlp', 'opusenc', 'opusdec']]


def main():
    if not check_requirements():
        print("Install all requirements programs in Readme.md file!")
        return 9  # Error Code

    options = Options()
    options.headless = True
    service = Service(GeckoDriverManager(log_level=0).install())
    driver = webdriver.Firefox(service=service, options=options)

    path = "/home/navidrome/music/volkantasci"  # IMPORTANT Change this PATH!
    temp = "/home/navidrome/temp"  # IMPORTANT Change this PATH!
    my_list = valid_args()

    cloner = Cloner(path, my_list, driver, temp)
    cloner.run_url_list()


if __name__ == "__main__":
    main()
