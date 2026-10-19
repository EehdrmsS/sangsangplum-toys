# 상상자두 · 작은 데스크톱 토이

Clap Cat과 우사기 랩의 소스 및 설치 없는 브라우저 체험입니다.

| 프로젝트 | 바로 체험 | 동작 |
| --- | --- | --- |
| Clap Cat | [브라우저에서 만나기](https://sangsangplum.pages.dev/clap-cat/) | 간식 → 박수 → 클릭하면 쉿과 악수 |
| 우사기 랩 | 제공 중단 | 웹 체험·Windows EXE 배포 중단 (2026-10-20) |

**2026-10-20부터 우사기 랩 웹 체험과 Windows EXE 배포를 중단했습니다.** 이 저장소에는 EXE·설치 ZIP·GitHub Releases를 제공하지 않습니다. 기존 소스는 보존하며, 아래 내용은 소스 보관 기록입니다. Clap Cat EXE 다운로드도 제공하지 않습니다.

## 설치 없이 체험

Clap Cat 링크를 열고 소리를 켠 뒤 체험하세요. 웹 고양이는 실제 로컬 `git push`를 감지하지 않습니다. 우사기 랩 웹 체험은 제공을 중단했습니다.

## 소스 내려받기와 실행

```powershell
git clone https://github.com/EehdrmsS/sangsangplum-toys.git
cd sangsangplum-toys
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Windows 10 (1803 이상) / Windows 11, Python 3.11 이상과 Tkinter가 필요합니다. 다른 OS에서 데스크톱 앱은 실행되지 않습니다.

### 우사기 랩

```powershell
.venv\Scripts\python.exe usagi-rap\src\usagi_rap.py
```

문자 키 입력 한 번에 기본 0.3초가 쌓입니다. 세 번 입력하면 0.9초를 재생하고, 분량이 끝나면 멈춘 위치에서 다음 입력을 기다립니다. 우클릭 → 설정에서 입력당 재생 길이를 바꿀 수 있습니다. F8 켜기/끄기, F9 처음부터, 우클릭 → 종료. 입력한 글은 기록하거나 전송하지 않습니다.

### Clap Cat

```powershell
.venv\Scripts\python.exe clap-cat\pushcat.py
```

Git for Windows가 필요합니다. 실행 중 같은 Windows 사용자의 GitHub push 성공을 감지하면 간식과 박수가 이어집니다. 고양이를 클릭하면 쉿과 악수, 드래그하면 이동합니다. 제어 창 X 또는 우클릭 → 종료로 닫으세요.

Git 감지를 위해 전역 Git 설정에 앱 전용 `include.path` 한 항목을 연결합니다. 정상 종료하면 제거합니다. 강제 종료 후에는 같은 폴더에서 다시 실행하고 정상 종료하세요. 앱을 닫아도 연결이 남았다면 `clap-cat/Disconnect-PushCat.ps1`을 확인하세요. Git 인증·remote·hook은 변경하지 않습니다. Trace2 원본 명령줄은 파일이나 서버에 저장하지 않습니다. WSL·다른 PC·GitHub 웹 화면에서 수행한 push는 감지 대상이 아닙니다.

## 웹 소스를 로컬에서 실행

```powershell
python -m http.server 8080 --directory web
```

[http://localhost:8080](http://localhost:8080)을 여세요. 데스크톱 Chrome·Edge에서 지원되는 경우 Clap Cat의 작은 플로팅 창을 사용할 수 있으며, 미지원 환경에서는 페이지 안에서 체험합니다.

## 코드 검증

```powershell
.venv\Scripts\python.exe usagi-rap\tests\test_pcm_credit.py
```

정확한 PCM 연속 재생·재개·음원 끝 순환과 입력당 재생 길이를 검사합니다. 소스에서 EXE를 만드는 배포 작업은 이 저장소에 포함하지 않았습니다.

## 미디어 출처와 이용 범위

[THIRD_PARTY_ASSETS.md](THIRD_PARTY_ASSETS.md)를 확인하세요. 캐릭터·영상·음원·GitHub 표시는 각 권리자에게 귀속되며, 이 저장소 공개가 해당 미디어의 재배포·상업 이용 허락을 의미하지 않습니다. 프로그램 코드에도 별도의 오픈소스 라이선스를 부여하지 않았습니다.

---

Source archive for two small toys by Sangsangplum. The Usagi Rap web demo and Windows executable distribution were discontinued on October 20, 2026. Existing source is preserved; no executables are hosted here. The Clap Cat web demo remains available and does not detect local Git pushes. Media rights remain with their respective owners.

## 체험 페이지 디자인 규칙

[공통 디자인 규칙](docs/SERVICE_PAGE_DESIGN.md)에 따라 같은 템플릿과 CSS로 두 페이지를 만듭니다. 개별 체험 DOM과 문구를 수정한 다음 생성·검증하세요.

```powershell
python scripts/render-toy-pages.py
python scripts/check-toy-pages.py
```

## 우사기 랩 가사 도전

웹 체험은 2026-10-20에 제공을 중단했습니다. 기존 챌린지 소스와 판정 검사는 보관합니다.

판정 검사: `node scripts/test-rap-challenge.mjs`
