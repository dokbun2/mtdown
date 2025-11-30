"""YouTube 및 Aikive 다운로드 로직 모듈"""
import re
import os
import sys
import subprocess
from typing import Callable, Optional
import yt_dlp

# certifi는 optional (패키징 앱에서만 필요)
try:
    import certifi
    HAS_CERTIFI = True
except ImportError:
    HAS_CERTIFI = False


def get_ffmpeg_path():
    """번들된 ffmpeg 경로 또는 시스템 ffmpeg 반환 (실행파일 경로)"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우
        base_path = sys._MEIPASS
        if sys.platform == 'darwin':
            ffmpeg = os.path.join(base_path, 'ffmpeg')
        else:
            ffmpeg = os.path.join(base_path, 'ffmpeg.exe')
        if os.path.exists(ffmpeg):
            return ffmpeg
    return 'ffmpeg'  # 시스템 ffmpeg 사용


def get_ffmpeg_location():
    """yt-dlp용 ffmpeg 디렉토리 경로 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우 - 번들 디렉토리 반환
        base_path = sys._MEIPASS
        if sys.platform == 'darwin':
            ffmpeg = os.path.join(base_path, 'ffmpeg')
        else:
            ffmpeg = os.path.join(base_path, 'ffmpeg.exe')
        if os.path.exists(ffmpeg):
            return base_path  # 디렉토리 경로 반환
    return None  # 시스템 ffmpeg 사용 (PATH에서 찾음)


def setup_playwright_path():
    """번들된 Playwright 브라우저 경로 설정"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        playwright_path = os.path.join(base_path, 'ms-playwright')
        if os.path.exists(playwright_path):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = playwright_path
            return True
    return False


class YouTubeDownloader:
    """YouTube/Instagram 영상/음원 다운로드 클래스 (yt-dlp 지원 사이트)"""

    YOUTUBE_REGEX = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=|shorts/)?([^&=%\?]{11})'
    )

    INSTAGRAM_REGEX = re.compile(
        r'(https?://)?(www\.)?instagram\.com/(p|reel|reels|tv)/[\w-]+'
    )

    def __init__(self):
        self.current_process = None

    @staticmethod
    def validate_url(url: str) -> bool:
        """YouTube/Instagram URL 유효성 검사"""
        return bool(YouTubeDownloader.YOUTUBE_REGEX.match(url) or
                    YouTubeDownloader.INSTAGRAM_REGEX.match(url))

    def download_video(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """영상 다운로드 (최고 화질)"""

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    speed = d.get('speed', 0)
                    speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "계산 중..."
                    if progress_callback:
                        progress_callback(percent, f"다운로드 중... {percent:.1f}% ({speed_str})")
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(100, "다운로드 완료! 처리 중...")

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',
            'nocheckcertificate': True,
            'no_check_certificate': True,
        }
        # 번들된 ffmpeg가 있으면 경로 지정
        ffmpeg_loc = get_ffmpeg_location()
        if ffmpeg_loc:
            ydl_opts['ffmpeg_location'] = ffmpeg_loc
        # SSL 인증서 경로 설정 (패키징 앱용)
        if HAS_CERTIFI:
            try:
                os.environ['SSL_CERT_FILE'] = certifi.where()
                os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
            except:
                pass

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.current_process = ydl
                ydl.download([url])
            return True
        except Exception as e:
            print(f"다운로드 실패: {e}")
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            return False
        finally:
            self.current_process = None

    def download_audio(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """음원 추출 (MP3)"""

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    speed = d.get('speed', 0)
                    speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "계산 중..."
                    if progress_callback:
                        progress_callback(percent, f"다운로드 중... {percent:.1f}% ({speed_str})")
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(100, "MP3 변환 중...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'nocheckcertificate': True,
            'no_check_certificate': True,
        }
        # 번들된 ffmpeg가 있으면 경로 지정
        ffmpeg_loc = get_ffmpeg_location()
        if ffmpeg_loc:
            ydl_opts['ffmpeg_location'] = ffmpeg_loc
        # SSL 인증서 경로 설정 (패키징 앱용)
        if HAS_CERTIFI:
            try:
                os.environ['SSL_CERT_FILE'] = certifi.where()
                os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
            except:
                pass

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.current_process = ydl
                ydl.download([url])
            return True
        except Exception as e:
            print(f"다운로드 실패: {e}")
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            return False
        finally:
            self.current_process = None


class AikiveDownloader:
    """Aikive.com 영상 다운로드 클래스"""

    AIKIVE_REGEX = re.compile(r'https?://aikive\.com/list-video/(shorts/)?(\d+)')

    def __init__(self):
        self.current_process = None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Aikive URL 유효성 검사"""
        return bool(AikiveDownloader.AIKIVE_REGEX.match(url))

    def _extract_video_url(self, url: str, progress_callback=None) -> Optional[tuple]:
        """Playwright로 비디오 URL 및 제목 추출"""
        # 번들된 Playwright 브라우저 경로 설정
        setup_playwright_path()

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Playwright가 설치되어 있지 않습니다.")
            return None

        if progress_callback:
            progress_callback(5, "페이지 분석 중...")

        video_urls = []
        title = "aikive_video"

        def handle_response(response):
            url = response.url
            if '.m3u8' in url or 'master.m3u8' in url:
                video_urls.append(url)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.on("response", handle_response)
                page.goto(url, wait_until="networkidle", timeout=30000)

                # 제목 추출
                try:
                    title_el = page.query_selector('h1, .title, [class*="title"]')
                    if title_el:
                        title = title_el.inner_text().strip()
                    else:
                        title = page.title().split(' - ')[0].strip()
                except:
                    pass

                browser.close()

            # m3u8 URL 찾기
            m3u8_url = None
            for vurl in video_urls:
                if 'master.m3u8' in vurl:
                    m3u8_url = vurl
                    break

            if m3u8_url:
                # 파일명에 사용할 수 없는 문자 제거
                title = re.sub(r'[<>:"/\\|?*]', '', title)
                return (m3u8_url, title)
            return None
        except Exception as e:
            print(f"URL 추출 실패: {e}")
            return None

    def download_video(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """영상 다운로드"""
        if progress_callback:
            progress_callback(0, "비디오 URL 추출 중...")

        result = self._extract_video_url(url, progress_callback)
        if not result:
            if progress_callback:
                progress_callback(0, "비디오 URL을 찾을 수 없습니다.")
            return False

        m3u8_url, title = result

        if progress_callback:
            progress_callback(10, f"다운로드 시작: {title}")

        output_file = os.path.join(output_path, f"{title}.mp4")

        # FFmpeg로 m3u8 다운로드
        cmd = [
            get_ffmpeg_path(), '-y',
            '-i', m3u8_url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            output_file
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.current_process = process

            # 진행률 시뮬레이션 (FFmpeg는 정확한 진행률을 주지 않음)
            if progress_callback:
                progress_callback(30, "다운로드 중...")

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                if progress_callback:
                    progress_callback(100, "다운로드 완료!")
                return True
            else:
                print(f"FFmpeg 오류: {stderr}")
                if progress_callback:
                    progress_callback(0, f"다운로드 실패")
                return False
        except Exception as e:
            print(f"다운로드 실패: {e}")
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            return False
        finally:
            self.current_process = None

    def download_audio(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """음원 추출 (MP3)"""
        if progress_callback:
            progress_callback(0, "비디오 URL 추출 중...")

        result = self._extract_video_url(url, progress_callback)
        if not result:
            if progress_callback:
                progress_callback(0, "비디오 URL을 찾을 수 없습니다.")
            return False

        m3u8_url, title = result

        if progress_callback:
            progress_callback(10, f"음원 추출 시작: {title}")

        output_file = os.path.join(output_path, f"{title}.mp3")

        # FFmpeg로 오디오만 추출
        cmd = [
            get_ffmpeg_path(), '-y',
            '-i', m3u8_url,
            '-vn',
            '-acodec', 'libmp3lame',
            '-ab', '320k',
            output_file
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.current_process = process

            if progress_callback:
                progress_callback(30, "음원 추출 중...")

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                if progress_callback:
                    progress_callback(100, "음원 추출 완료!")
                return True
            else:
                print(f"FFmpeg 오류: {stderr}")
                if progress_callback:
                    progress_callback(0, f"추출 실패")
                return False
        except Exception as e:
            print(f"다운로드 실패: {e}")
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            return False
        finally:
            self.current_process = None


class ThreadsDownloader:
    """Threads 영상 다운로드 클래스"""

    THREADS_REGEX = re.compile(r'https?://(www\.)?threads\.net/@[\w.]+/post/[\w]+')

    def __init__(self):
        self.current_process = None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Threads URL 유효성 검사"""
        return bool(ThreadsDownloader.THREADS_REGEX.match(url)) or 'threads.com' in url or 'threads.net' in url

    def _extract_video_url(self, url: str, progress_callback=None) -> Optional[tuple]:
        """Playwright로 비디오 URL 및 제목 추출"""
        # 번들된 Playwright 브라우저 경로 설정
        setup_playwright_path()

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Playwright가 설치되어 있지 않습니다.")
            return None

        if progress_callback:
            progress_callback(5, "페이지 분석 중...")

        video_urls = []
        title = "threads_video"

        def handle_response(response):
            resp_url = response.url
            if any(ext in resp_url for ext in ['.mp4', 'video']):
                if 'cdninstagram' in resp_url or 'fbcdn' in resp_url:
                    video_urls.append(resp_url)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.on("response", handle_response)

                # threads.com을 threads.net으로 변환
                if 'threads.com' in url:
                    url = url.replace('threads.com', 'threads.net')

                # domcontentloaded로 빠르게 로드하고 짧게 대기 (첫 비디오만 캡처)
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)

                # 제목 추출 (post_id 사용)
                try:
                    if '/post/' in url:
                        post_id = url.split('/post/')[1].split('?')[0]
                        title = f"threads_{post_id}"
                except:
                    pass

                browser.close()

            if video_urls:
                # 첫 번째 비디오가 메인 게시물 (추천 영상보다 먼저 로드됨)
                video_url = video_urls[0]
                title = re.sub(r'[<>:"/\\|?*@]', '', title)
                return (video_url, title)
            return None
        except Exception as e:
            print(f"URL 추출 실패: {e}")
            return None

    def download_video(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """영상 다운로드"""
        if progress_callback:
            progress_callback(0, "비디오 URL 추출 중...")

        result = self._extract_video_url(url, progress_callback)
        if not result:
            if progress_callback:
                progress_callback(0, "비디오 URL을 찾을 수 없습니다.")
            return False

        video_url, title = result

        if progress_callback:
            progress_callback(10, f"다운로드 시작: {title}")

        output_file = os.path.join(output_path, f"{title}.mp4")

        # FFmpeg로 다운로드
        cmd = [
            get_ffmpeg_path(), '-y',
            '-i', video_url,
            '-c', 'copy',
            output_file
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.current_process = process

            if progress_callback:
                progress_callback(30, "다운로드 중...")

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                if progress_callback:
                    progress_callback(100, "다운로드 완료!")
                return True
            else:
                print(f"FFmpeg 오류: {stderr}")
                if progress_callback:
                    progress_callback(0, f"다운로드 실패")
                return False
        except Exception as e:
            print(f"다운로드 실패: {e}")
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            return False
        finally:
            self.current_process = None

    def download_audio(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """음원 추출 (MP3)"""
        if progress_callback:
            progress_callback(0, "비디오 URL 추출 중...")

        result = self._extract_video_url(url, progress_callback)
        if not result:
            if progress_callback:
                progress_callback(0, "비디오 URL을 찾을 수 없습니다.")
            return False

        video_url, title = result

        if progress_callback:
            progress_callback(10, f"음원 추출 시작: {title}")

        output_file = os.path.join(output_path, f"{title}.mp3")

        cmd = [
            get_ffmpeg_path(), '-y',
            '-i', video_url,
            '-vn',
            '-acodec', 'libmp3lame',
            '-ab', '320k',
            output_file
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.current_process = process

            if progress_callback:
                progress_callback(30, "음원 추출 중...")

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                if progress_callback:
                    progress_callback(100, "음원 추출 완료!")
                return True
            else:
                print(f"FFmpeg 오류: {stderr}")
                if progress_callback:
                    progress_callback(0, f"추출 실패")
                return False
        except Exception as e:
            print(f"다운로드 실패: {e}")
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            return False
        finally:
            self.current_process = None


class UniversalDownloader:
    """통합 다운로더 - URL에 따라 적절한 다운로더 선택"""

    def __init__(self):
        self.youtube = YouTubeDownloader()
        self.aikive = AikiveDownloader()
        self.threads = ThreadsDownloader()

    def validate_url(self, url: str) -> bool:
        """URL 유효성 검사"""
        return (self.youtube.validate_url(url) or
                self.aikive.validate_url(url) or
                self.threads.validate_url(url))

    def get_downloader(self, url: str):
        """URL에 맞는 다운로더 반환"""
        if self.aikive.validate_url(url):
            return self.aikive
        elif self.threads.validate_url(url):
            return self.threads
        elif self.youtube.validate_url(url):
            return self.youtube
        return None

    def download_video(self, url: str, output_path: str, progress_callback=None) -> bool:
        """영상 다운로드"""
        downloader = self.get_downloader(url)
        if downloader:
            return downloader.download_video(url, output_path, progress_callback)
        return False

    def download_audio(self, url: str, output_path: str, progress_callback=None) -> bool:
        """음원 추출"""
        downloader = self.get_downloader(url)
        if downloader:
            return downloader.download_audio(url, output_path, progress_callback)
        return False
