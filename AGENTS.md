# 토이 소스 작업 규칙

웹 체험을 수정·추가할 때 docs/SERVICE_PAGE_DESIGN.md를 먼저 읽습니다.
공통 양식은 templates/toys/page.html과 web/assets/toy-page.css에서 관리합니다.
문구는 templates/toys/pages.json, 개별 조작 DOM은 서비스별 experience.html에서 수정합니다.
python scripts/render-toy-pages.py로 생성하고 python scripts/check-toy-pages.py로 확인합니다.
공통 헤더·소개·소스 카드·버튼·푸터 CSS를 개별 페이지에 복제하지 않습니다.
서비스별 조작, 미디어 출처, 직접 다운로드 미제공 상태를 유지합니다.
