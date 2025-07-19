import os
import struct
import sqlite3
import csv
import xml.etree.ElementTree as ET
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from sqlcipher3 import dbapi2 as sqlcipher
from decrypt_key import get_sqlcipher_keys

# ───────────────────────────────
# 0. 키 가져오기
# ───────────────────────────────
log_key_hex, db_key_hex = get_sqlcipher_keys()
if log_key_hex is None or db_key_hex is None:
    print("[!] SQLCipher 키 복호화 실패, 종료합니다.")
    exit(1)

log_key = bytes.fromhex(log_key_hex)

# ───────────────────────────────
# 1. 로그 파일 복호화
# ───────────────────────────────
log_dir = "log_files"
output_log_dir = "dec_log_files"
os.makedirs(output_log_dir, exist_ok=True)

def decrypt_log_file(filepath, key, output_path):
    with open(filepath, "rb") as f:
        data = f.read()

    with open(output_path, "w", encoding="utf-8") as out_file:
        offset = 0
        block_num = 1
        while offset + 20 <= len(data):
            try:
                iv         = data[offset:offset+16]
                length     = struct.unpack(">I", data[offset+16:offset+20])[0]
                ciphertext = data[offset+20:offset+20+length]
                if len(ciphertext) < length:
                    break

                cipher     = AES.new(key, AES.MODE_CBC, iv)
                plaintext  = unpad(cipher.decrypt(ciphertext), AES.block_size)
                decoded    = plaintext.decode(errors='replace')

                out_file.write(f"[+] 블록 {block_num}:\n{decoded}\n\n")
                offset += 20 + length
                block_num += 1
            except Exception as e:
                out_file.write(f"[!] 블록 {block_num} 복호화 오류: {e}\n")
                break

for fn in os.listdir(log_dir):
    if not fn.startswith("log-"):
        continue
    inp  = os.path.join(log_dir, fn)
    outp = os.path.join(output_log_dir, f"{fn}_dec.txt")
    decrypt_log_file(inp, log_key, outp)
    print(f"[+] 로그 복호화 완료: {outp}")

# ───────────────────────────────
# 2. DB 파일 복호화 + CSV/XML 내보내기
# ───────────────────────────────
def decrypt_and_export_db(encrypted_db_path, output_db_path, key_plaintext):
    try:
        # SQLCipher DB 열고 복호화
        conn = sqlcipher.connect(encrypted_db_path)
        cur = conn.cursor()
        cur.execute(f"PRAGMA key = '{key_plaintext}';")
        cur.execute("PRAGMA cipher_page_size = 4096;")
        cur.execute("PRAGMA kdf_iter = 1;")
        cur.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512;")
        cur.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;")
        cur.execute("SELECT count(*) FROM sqlite_master;")
        print(f"[*] 복호화 성공: {encrypted_db_path}")

        # 새 SQLite DB로 백업 
        print(f"[*] 백업 중 → {output_db_path}")
        with sqlite3.connect(output_db_path) as out_conn:
            out_cur = out_conn.cursor()
            cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
            for name, ddl in cur.fetchall():
                if name == "sqlite_sequence":
                    continue
                if not ddl or "fts5" in ddl.lower():
                    continue
                out_cur.execute(ddl)
                
                cur.execute(f"PRAGMA table_info({name})")
                cols = [c[1] for c in cur.fetchall()]
                
                cur.execute(f"SELECT * FROM {name}")
                rows = cur.fetchall()
                if not rows:
                    continue
                ph = ",".join("?" * len(cols))
                cols_str = ",".join(cols)
                for row in rows:
                    out_cur.execute(
                        f"INSERT INTO {name} ({cols_str}) VALUES ({ph})",
                        row[:len(cols)]
                    )
            out_conn.commit()
        conn.close()
        print(f"[+] DB 백업 완료: {output_db_path}")

        # CSV/XML 내보내기
        base    = os.path.splitext(os.path.basename(output_db_path))[0]
        parent  = os.path.dirname(output_db_path)
        csv_dir = os.path.join(parent, f"{base}_csv")
        xml_dir = os.path.join(parent, f"{base}_xml")
        os.makedirs(csv_dir, exist_ok=True)
        os.makedirs(xml_dir, exist_ok=True)

        with sqlite3.connect(output_db_path) as exp_conn:
            exp_cur = exp_conn.cursor()
            exp_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in exp_cur.fetchall()]

            for tbl in tables:
                
                exp_cur.execute(f"PRAGMA table_info({tbl})")
                cols = [c[1] for c in exp_cur.fetchall()]

                
                if tbl == 'sms':
                    for extra in ('is_deleted','is_group_update'):
                        if extra not in cols:
                            cols.append(extra)

                
                exp_cur.execute(f"SELECT * FROM {tbl}")
                rows = exp_cur.fetchall()

                # CSV 저장
                csv_path = os.path.join(csv_dir, f"{tbl}.csv")
                with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(cols)
                    for row in rows:
                        out = []
                        row = list(row)
                        
                        if len(row) < len(cols):
                            row += [''] * (len(cols)-len(row))
                        for col_name, val in zip(cols, row):
                            if isinstance(val, (bytes, bytearray)):
                                h = val.hex()
                                out.append(" ".join(h[i:i+2] for i in range(0, len(h), 2)))
                            else:
                                out.append(val)
                        writer.writerow(out)
                print(f"[+] CSV 저장: {csv_path}")

                # XML 저장
                root = ET.Element(f"{tbl}_rows")
                for row in rows:
                    r = list(row)
                    if tbl == 'sms' and len(r) < len(cols):
                        r += [''] * (len(cols)-len(r))
                    rec = ET.SubElement(root, tbl)
                    for col_name, val in zip(cols, r):
                        cell = ET.SubElement(rec, col_name)
                        if isinstance(val, (bytes, bytearray)):
                            h = val.hex()
                            cell.text = " ".join(h[i:i+2] for i in range(0, len(h), 2))
                        else:
                            cell.text = "" if val is None else str(val)
                xml_path = os.path.join(xml_dir, f"{tbl}.xml")
                ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
                print(f"[+] XML 저장: {xml_path}")

        return True

    except Exception as e:
        print(f"[!] 복호화/백업/내보내기 실패: {e}")
        return False


os.makedirs("dec_database_files", exist_ok=True)
for enc, out in [("extracted_files/session.db", "dec_database_files/dec_session.sqlite")]:
    decrypt_and_export_db(enc, out, db_key_hex)