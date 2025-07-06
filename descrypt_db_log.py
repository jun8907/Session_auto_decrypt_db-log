import os
import struct
import sqlite3
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from sqlcipher3 import dbapi2 as sqlcipher
from descrypt_key import get_sqlcipher_keys

# 키 가져오기
log_key_hex, db_key_hex = get_sqlcipher_keys()
if log_key_hex is None or db_key_hex is None:
    print("[!] SQLCipher 키 복호화 실패, 종료합니다.")
    exit(1)

log_key = bytes.fromhex(log_key_hex)

# ───────────────────────────────
# 1. 로그 파일 복호화
# ───────────────────────────────
log_dir = "log_files"
output_log_dir = "des_log_files"
os.makedirs(output_log_dir, exist_ok=True)

def decrypt_log_file(filepath, key, output_path):
    with open(filepath, "rb") as f:
        data = f.read()

    with open(output_path, "w", encoding="utf-8") as out_file:
        offset = 0
        block_num = 1
        while offset + 20 <= len(data):
            try:
                iv = data[offset:offset+16]
                length = struct.unpack(">I", data[offset+16:offset+20])[0]
                ciphertext = data[offset+20:offset+20+length]

                if len(ciphertext) < length:
                    break

                cipher = AES.new(key, AES.MODE_CBC, iv)
                plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
                decoded_text = plaintext.decode(errors='replace')

                out_file.write(f"[+] 복호화된 블록 {block_num}:\n{decoded_text}\n\n")

                block_num += 1
                offset += 20 + length
            except Exception as e:
                out_file.write(f"[!] 블록 {block_num} 복호화 중 오류 발생: {e}\n")
                break

log_files = [f for f in os.listdir(log_dir) if f.startswith("log-")]
if not log_files:
    print("[!] log_files 디렉터리에 log- 파일이 없습니다.")
else:
    for log_filename in log_files:
        log_path = os.path.join(log_dir, log_filename)
        output_path = os.path.join(output_log_dir, f"{log_filename}_dec.txt")
        decrypt_log_file(log_path, log_key, output_path)
        print(f"[+] 로그 파일 백업 완료: {output_path}")  # ← 추가된 출력

# ───────────────────────────────
# 2. DB 파일 복호화
# ───────────────────────────────
def decrypt_and_export_db(encrypted_db_path, output_db_path, key_plaintext):
    try:
        conn = sqlcipher.connect(encrypted_db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA key = '{key_plaintext}';")
        cursor.execute("PRAGMA cipher_page_size = 4096;")
        cursor.execute("PRAGMA kdf_iter = 1;")
        cursor.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512;")
        cursor.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;")
        cursor.execute("SELECT count(*) FROM sqlite_master;")  # 복호화 테스트용

        cursor.execute("SELECT count(*) FROM sqlite_master;")
        print("[+] 복호화 성공!")

        print(f"[*] 백업 중 → {output_db_path}")
        with sqlite3.connect(output_db_path) as out_conn:
            out_cursor = out_conn.cursor()

            
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
            table_info = cursor.fetchall()

            for table_name, create_stmt in table_info:
                if table_name == "sqlite_sequence":
                    continue  
                if not create_stmt:
                    continue
                if "fts5" in create_stmt.lower():
                    print(f"[!] FTS5 테이블 제외됨: {table_name}")
                    continue

                
                out_cursor.execute(create_stmt)

                
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                column_names = [col[1] for col in columns_info]

                
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                if not rows:
                    continue

                placeholders = ','.join(['?'] * len(column_names))
                columns_str = ','.join(column_names)

                for row in rows:
                    trimmed_row = row[:len(column_names)]  
                    out_cursor.execute(
                        f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", 
                        trimmed_row
                    )

            out_conn.commit()

        conn.close()
        print(f"[+] DB 파일 백업 완료: {output_db_path}")
        return True

    except Exception as e:
        print(f"[!] 복호화 또는 백업 실패: {e}")
        return False

os.makedirs("des_database_files", exist_ok=True)
db_targets = [
    ("extracted_files/session.db", "des_database_files/des_session.sqlite")
]
for enc_db, out_db in db_targets:
    decrypt_and_export_db(enc_db, out_db, db_key_hex)
