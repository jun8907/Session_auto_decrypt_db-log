# Session_auto_descrypt_db 🔐

복호화되지 않은 Session 메신저의 session.db 파일을 복호화하는 코드입니다.

<br><br>

## 🧪 사용법

```bash
git clone https://github.com/jun8907/Session_auto_descrypt_db.git
cd Session_auto_descrypt_db
pip install -r requirements.txt
python pull.py
python decrypt_db.py
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
- preferences.py
- persistent.py
- descrypt_key.py
- descrypt_db.py
<br><br>
### pull.py

루팅된 Android 디바이스에서 Session 메신저의 db 파일 및 복호화에 필요한 핵심 파일들을 자동으로 추출하는 코드입니다.
db 파일과 복호화에 필요한 파일들은 `extracted_files/` 디렉터리에 저장

```python
[실행 결과]
[*] su 권한으로 /data/data/network.loki.messenger/shared_prefs/network.loki.messenger_preferences.xml → /sdcard/network.loki.messenger_preferences.xml  복사 중...
[*] /sdcard/network.loki.messenger_preferences.xml → extracted_files\network.loki.messenger_preferences.xml 로컬로 추출 중...
/sdcard/network.loki.messenger_preferences.xml: 1 file pulled, 0 skipped. 0.5 MB/s (2344 bytes in 0.004s)
[+] 추출 완료: extracted_files\network.loki.messenger_preferences.xml
[*] su 권한으로 /data/data/network.loki.messenger/databases/session.db → /sdcard/session.db 복사 중...
[*] /sdcard/session.db → extracted_files\session.db 로컬로 추출 중...
/sdcard/session.db: 1 file pulled, 0 skipped. 36.5 MB/s (1081344 bytes in 0.028s)
[+] 추출 완료: extracted_files\session.db
[*] su 권한으로 /data/misc/keystore/persistent.sqlite → /sdcard/persistent.sqlite 복사 중...
[*] /sdcard/persistent.sqlite → extracted_files\persistent.sqlite 로컬로 추출 중...
/sdcard/persistent.sqlite: 1 file pulled, 0 skipped. 16.1 MB/s (139264 bytes in 0.008s)
[+] 추출 완료: extracted_files\persistent.sqlite
```
<br><br>
### preferences_attachment, database.py

Session 메신저의 /share_pref/org.thoughtcrime.securesms_preferences.xml 파일에서 SQLCipher에 사용된 패스프레이즈를 추출
- `data (hex)`
- `input (hex)`
- `GCM Tag (hex)`
- `iv (base64)`

```python
[실행 결과]
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
### descrypt_key.py

Android의 Signal 메신저에서 추출한 설정 파일 (`shared_prefs`)과 키 저장소(`persistent.sqlite`)를 이용하여, SQLCipher로 암호화된 Signal DB의 복호화 키(SQLCipher Key)를 자동으로 복원해주는 코드 입니다.

```python
[실행 결과]
[+] 복호화 성공! SQLCipher Key (hex): 9a177c5296dedc24cf72cd563c39d3234e616f4ab2c596696ed27411d65fde94
```
<br><br>
### descrypt_db.py

암호화된 Session 데이터베이스(`session.db`)를 복호화하여 일반 SQLite 형식으로 변환 및 저장해주는 코드 입니다.

```python
[실행 결과]
[*] 복호화 시도: extracted_files/session.db
[+] 복호화 성공!
[*] 백업 중 → decrypted_files/des_session.sqlite
[!] FTS5 테이블 제외됨: sms_fts
[!] FTS5 테이블 제외됨: mms_fts
[!] FTS5 테이블 제외됨: emoji_search
[+] 백업 완료: decrypted_files/des_session.sqlite
```
