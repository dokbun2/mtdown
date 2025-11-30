"""YouTube Downloader - 메인 애플리케이션"""
import os
import sys
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from downloader import UniversalDownloader


class YouTubeDownloaderApp(ctk.CTk):
    """YouTube 다운로더 GUI 애플리케이션"""

    def __init__(self):
        super().__init__()

        # 앱 설정
        self.title("YouTube Downloader")
        self.geometry("600x580")
        self.minsize(550, 550)

        # 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 다운로더 인스턴스
        self.downloader = UniversalDownloader()
        self.is_downloading = False

        # 기본 저장 경로
        self.save_path = os.path.expanduser("~/Downloads")

        # UI 구성
        self._create_widgets()

        # macOS 복사/붙여넣기 단축키 바인딩
        self._setup_clipboard_bindings()

    def _create_widgets(self):
        """UI 위젯 생성"""
        # 메인 프레임
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 타이틀
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="YouTube Downloader",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(0, 20))

        # URL 입력 섹션
        self.url_frame = ctk.CTkFrame(self.main_frame)
        self.url_frame.pack(fill="x", pady=10)

        self.url_label = ctk.CTkLabel(
            self.url_frame,
            text="YouTube URL:",
            font=ctk.CTkFont(size=14)
        )
        self.url_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.url_inner_frame = ctk.CTkFrame(self.url_frame, fg_color="transparent")
        self.url_inner_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.url_entry = ctk.CTkEntry(
            self.url_inner_frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.paste_btn = ctk.CTkButton(
            self.url_inner_frame,
            text="붙여넣기",
            width=80,
            height=40,
            command=self._paste_url
        )
        self.paste_btn.pack(side="right")

        # 저장 경로 섹션
        self.path_frame = ctk.CTkFrame(self.main_frame)
        self.path_frame.pack(fill="x", pady=10)

        self.path_label = ctk.CTkLabel(
            self.path_frame,
            text="저장 위치:",
            font=ctk.CTkFont(size=14)
        )
        self.path_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.path_inner_frame = ctk.CTkFrame(self.path_frame, fg_color="transparent")
        self.path_inner_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.path_entry = ctk.CTkEntry(
            self.path_inner_frame,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.path_entry.insert(0, self.save_path)

        self.browse_btn = ctk.CTkButton(
            self.path_inner_frame,
            text="찾아보기",
            width=100,
            height=40,
            command=self._browse_folder
        )
        self.browse_btn.pack(side="right")

        # 다운로드 타입 선택
        self.type_frame = ctk.CTkFrame(self.main_frame)
        self.type_frame.pack(fill="x", pady=10)

        self.type_label = ctk.CTkLabel(
            self.type_frame,
            text="다운로드 형식:",
            font=ctk.CTkFont(size=14)
        )
        self.type_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.type_var = ctk.StringVar(value="video")

        self.radio_frame = ctk.CTkFrame(self.type_frame, fg_color="transparent")
        self.radio_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.video_radio = ctk.CTkRadioButton(
            self.radio_frame,
            text="영상 (MP4)",
            variable=self.type_var,
            value="video",
            font=ctk.CTkFont(size=13)
        )
        self.video_radio.pack(side="left", padx=(0, 30))

        self.audio_radio = ctk.CTkRadioButton(
            self.radio_frame,
            text="음원 (MP3)",
            variable=self.type_var,
            value="audio",
            font=ctk.CTkFont(size=13)
        )
        self.audio_radio.pack(side="left")

        # 진행률 바
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", pady=10)

        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="대기 중...",
            font=ctk.CTkFont(size=13)
        )
        self.status_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)

        # 다운로드 버튼
        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="다운로드 시작",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start_download
        )
        self.download_btn.pack(fill="x", pady=20)

    def _paste_url(self):
        """URL 입력창에 클립보드 내용 붙여넣기"""
        try:
            text = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
        except:
            pass

    def _setup_clipboard_bindings(self):
        """macOS Cmd+C/V/X/A 단축키 설정"""
        # CTkEntry 내부의 실제 Entry 위젯에 바인딩
        for ctk_entry in [self.url_entry, self.path_entry]:
            # CTkEntry 내부 위젯 접근
            inner_entry = ctk_entry._entry
            inner_entry.bind("<Command-v>", lambda e, w=ctk_entry: self._paste(w))
            inner_entry.bind("<Command-c>", lambda e, w=ctk_entry: self._copy(w))
            inner_entry.bind("<Command-x>", lambda e, w=ctk_entry: self._cut(w))
            inner_entry.bind("<Command-a>", lambda e, w=ctk_entry: self._select_all(w))

    def _paste(self, widget):
        """붙여넣기"""
        try:
            text = self.clipboard_get()
            # 현재 선택 영역 삭제 후 붙여넣기
            current = widget.get()
            widget.delete(0, "end")
            widget.insert(0, text)
        except:
            pass
        return "break"

    def _copy(self, widget):
        """복사"""
        try:
            text = widget.get()
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
        except:
            pass
        return "break"

    def _cut(self, widget):
        """잘라내기"""
        try:
            text = widget.get()
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
                widget.delete(0, "end")
        except:
            pass
        return "break"

    def _select_all(self, widget):
        """전체 선택"""
        widget.select_range(0, "end")
        widget.icursor("end")
        return "break"

    def _browse_folder(self):
        """폴더 선택 다이얼로그"""
        folder = filedialog.askdirectory(initialdir=self.save_path)
        if folder:
            self.save_path = folder
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def _update_progress(self, percent: float, status: str):
        """진행률 업데이트 (메인 스레드에서 실행)"""
        self.progress_bar.set(percent / 100)
        self.status_label.configure(text=status)

    def _start_download(self):
        """다운로드 시작"""
        if self.is_downloading:
            messagebox.showwarning("경고", "다운로드가 이미 진행 중입니다.")
            return

        url = self.url_entry.get().strip()
        save_path = self.path_entry.get().strip()

        # URL 검증
        if not url:
            messagebox.showerror("오류", "URL을 입력해주세요.")
            return

        if not self.downloader.validate_url(url):
            messagebox.showerror("오류", "지원하지 않는 URL입니다.\n(YouTube, Instagram, Threads, Aikive 지원)")
            return

        # 저장 경로 검증
        if not os.path.isdir(save_path):
            messagebox.showerror("오류", "유효한 저장 경로를 선택해주세요.")
            return

        # 다운로드 시작
        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="다운로드 중...")

        download_type = self.type_var.get()
        thread = threading.Thread(
            target=self._download_thread,
            args=(url, save_path, download_type),
            daemon=True
        )
        thread.start()

    def _download_thread(self, url: str, save_path: str, download_type: str):
        """다운로드 스레드"""
        def progress_callback(percent, status):
            self.after(0, lambda: self._update_progress(percent, status))

        try:
            if download_type == "video":
                success = self.downloader.download_video(url, save_path, progress_callback)
            else:
                success = self.downloader.download_audio(url, save_path, progress_callback)

            if success:
                self.after(0, lambda: self._download_complete())
            else:
                self.after(0, lambda: self._download_failed())
        except Exception as e:
            self.after(0, lambda: self._download_failed(str(e)))

    def _download_complete(self):
        """다운로드 완료 처리"""
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="다운로드 시작")
        self.status_label.configure(text="다운로드 완료!")
        self.progress_bar.set(1)
        messagebox.showinfo("완료", "다운로드가 완료되었습니다!")

        # 다운로드 폴더 열기
        self._open_folder(self.path_entry.get().strip())

    def _open_folder(self, path: str):
        """폴더 열기 (OS별 처리)"""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", path])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["explorer", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            print(f"폴더 열기 실패: {e}")

    def _download_failed(self, error_msg: str = ""):
        """다운로드 실패 처리"""
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="다운로드 시작")
        self.progress_bar.set(0)
        self.status_label.configure(text="다운로드 실패")
        messagebox.showerror("오류", f"다운로드 실패: {error_msg}" if error_msg else "다운로드에 실패했습니다.")


def main():
    app = YouTubeDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
