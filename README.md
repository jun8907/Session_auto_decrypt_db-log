# Session_auto_decrypt_db-log 🔐

복호화되지 않은 Session 메신저의 session.db 파일을 복호화하는 코드입니다.

<br><br>

## 🧪 사용법

```bash
git clone https://github.com/jun8907/Session_auto_decrypt_db-log.git
cd Session_auto_decrypt_db-log
pip install -r requirements.txt
python pull.py
python decrypt_db_log.py
```

<br><br>

## 📖 관련 라이브러리 설치

```bash
pip install pycryptodome
pip install sqlcipher3-wheels
```

<br><br>

## 🔧 코드 설명

- pull.py
- preferences_log.py
- preferences_database.py
- persistent.py
- decrypt_key.py
- decrypt_db_log.py
<br><br>
### pull.py

루팅된 Android 디바이스에서 Session 메신저의 db 파일, log 파일 및 복호화에 필요한 핵심 파일들을 자동으로 추출하는 코드입니다.
db 파일과 복호화에 필요한 파일들은 `extracted_files/` 디렉터리에 저장
log 파일들은 `log_files/` 디렉터리에 저장

```python
[실행 결과]
[*] su 권한으로 /data/data/network.loki.messenger/shared_prefs/network.loki.messenger_preferences.xml → /sdcard/network.loki.messenger_preferences.xml 복사 중...
[*] /sdcard/network.loki.messenger_preferences.xml → extracted_files\network.loki.messenger_preferences.xml 로컬 로 추출 중...
/sdcard/network.loki.messenger_preferences.xml: 1 file pulled, 0 skipped. 0.2 MB/s (2344 bytes in 0.009s)        
[+] 추출 완료: extracted_files\network.loki.messenger_preferences.xml
[*] su 권한으로 /data/misc/keystore/persistent.sqlite → /sdcard/persistent.sqlite 복사 중...
[*] /sdcard/persistent.sqlite → extracted_files\persistent.sqlite 로컬로 추출 중...
/sdcard/persistent.sqlite: 1 file pulled, 0 skipped. 5.9 MB/s (139264 bytes in 0.023s)
[+] 추출 완료: extracted_files\persistent.sqlite
[*] su 권한으로 /data/data/network.loki.messenger/databases/session.db → /sdcard/session.db 복사 중...
[*] /sdcard/session.db → extracted_files\session.db 로컬로 추출 중...
/sdcard/session.db: 1 file pulled, 0 skipped. 23.0 MB/s (1359872 bytes in 0.056s)
[+] 추출 완료: extracted_files\session.db
[*] 로그 파일 목록 가져오는 중...
[*] su 권한으로 /data/data/network.loki.messenger/cache/log/log-1751743631147 → /sdcard/log-1751743631147 복사 중...
[*] /sdcard/log-1751743631147 → log_files\log-1751743631147 로컬로 추출 중...
/sdcard/log-1751743631147: 1 file pulled, 0 skipped. 15.9 MB/s (198744 bytes in 0.012s)
[+] 추출 완료: log_files\log-1751743631147
```
<br><br>
### preferences_log, database.py

Session 메신저의 /share_pref/org.thoughtcrime.securesms_preferences.xml 파일에서 SQLCipher에 사용된 패스프레이즈를 추출
- `data (hex)`
- `input (hex)`
- `GCM Tag (hex)`
- `iv (base64)`

```python
[실행 결과]
[+] data (hex)       : 13cf56a27bacafadfcadd4c285e86a3fd6bccabebb920073c8e9c2087fd1c317703345fd1d6462d6e73e2729362e0574
[+] ciphertext (hex) : 13cf56a27bacafadfcadd4c285e86a3fd6bccabebb920073c8e9c2087fd1c317
[+] GCM tag (hex)    : 703345fd1d6462d6e73e2729362e0574
[+] iv (base64)      : k7d1sTgb/tBty9YC

[+] data (hex)       : 085617703bc8f3aea69c0f1daaefd7d7838f0370ec3cdecf00ac04e44b270e8e3f8d7d566b45d619dddba8c482f7c89f
[+] ciphertext (hex) : 085617703bc8f3aea69c0f1daaefd7d7838f0370ec3cdecf00ac04e44b270e8e
[+] GCM tag (hex)    : 3f8d7d566b45d619dddba8c482f7c89f
[+] iv (base64)      : 1Fv01G4yumoSIscU
```
<br><br>
### persistent.py

Android 기기에서 추출한 Session 메신저의 `persistent.sqlite` 키스토어 DB에서 `SignalSecret` alias에 해당하는 복호화 키(16바이트)를 자동으로 추출하는 코드입니다.

```python
[실행 결과]
[+] SignalSecret #1 id: 7284520658499830241
    → 추출된 복호화 키 (16바이트 hex): d1ccc1ae4d0e3a5ef0b1074794e076b7
[+] SignalSecret #2 id: 6456924783388765775
    → 추출된 복호화 키 (16바이트 hex): d843d662011f92d82c69659c4311904f
```
<br><br>
### decrypt_key.py

Android의 Session 메신저에서 추출한 설정 파일 (`shared_prefs`)과 키 저장소(`persistent.sqlite`)를 이용하여, SQLCipher로 암호화된 Session DB의 복호화 키(SQLCipher Key)를 자동으로 복원해주는 코드 입니다.

```python
[실행 결과]
[*] 로그 DB용 SignalSecret #1 복호화 시도 중...
[+] 로그 DB 복호화 성공! SQLCipher Key (hex): dcdf7bf1c2df04d94d75c4e4445c7f203bbbdd11d117184b242e36d39ea9dfdb   

[*] 메시지 DB용 SignalSecret #1 복호화 시도 중...
[+] 메시지 DB 복호화 성공! SQLCipher Key (hex): e0ec6de02a377c48b179351992ade4982540ba184324e24f9f92b8795f679696
```
<br><br>
### decrypt_db_log.py

암호화된 Session 데이터베이스(`session.db`)와 로그(`log-~`)를 복호화하여 일반 SQLite, 텍스트 형식으로 변환 및 저장해주는 코드 입니다.

```python
[실행 결과]
[+] 로그 파일 백업 완료: dec_log_files\log-1751743631147_dec.txt
[+] 복호화 성공!
[*] 백업 중 → dec_database_files/dec_session.sqlite
[!] FTS5 테이블 제외됨: sms_fts
[!] FTS5 테이블 제외됨: mms_fts
[!] FTS5 테이블 제외됨: emoji_search
[+] DB 파일 백업 완료: dec_database_files/dec_session.sqlite
```
